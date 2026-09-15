"""Run local EfficientNet-B0 image classification without the AgriOS API."""

import argparse
import json
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms
from torchvision.models import efficientnet_b0
from torch import nn


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CHECKPOINT = ROOT_DIR / "John's work" / "mobile1_efficientnetb0.pth"
DEFAULT_CONFIG = ROOT_DIR / "John's work" / "model_config.json"


def load_config(config_path: Path, checkpoint: dict) -> dict:
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        config = {}
    config.setdefault("num_classes", len(checkpoint.get("class_to_idx", {})) or 15)
    config.setdefault("img_size", checkpoint.get("img_size", 224))
    config.setdefault("normalization", {
        "mean": checkpoint.get("imagenet_mean", [0.485, 0.456, 0.406]),
        "std": checkpoint.get("imagenet_std", [0.229, 0.224, 0.225]),
    })
    if "idx_to_class" not in config:
        class_to_idx = checkpoint.get("class_to_idx", {})
        config["idx_to_class"] = {str(index): label for label, index in class_to_idx.items()}
    return config


def load_checkpoint(checkpoint_path: Path, config_path: Path):
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {checkpoint_path}\n"
            "Place mobile1_efficientnetb0.pth there or pass --checkpoint."
        )

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    if not isinstance(checkpoint, dict):
        raise ValueError("Checkpoint must be a PyTorch state-dict or checkpoint dictionary")

    config = load_config(config_path, checkpoint)
    model = efficientnet_b0(weights=None)
    classifier_in = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.2, inplace=True),
        nn.Linear(classifier_in, int(config["num_classes"])),
    )

    state_dict = checkpoint.get("model_state_dict") or checkpoint.get("state_dict") or checkpoint.get("model")
    if state_dict is None:
        state_dict = checkpoint
    state_dict = {key.replace("module.", ""): value for key, value in state_dict.items()}
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    return model, config


def predict(image_path: Path, checkpoint_path: Path, config_path: Path, top_k: int):
    model, config = load_checkpoint(checkpoint_path, config_path)
    transform = transforms.Compose([
        transforms.Resize((int(config["img_size"]), int(config["img_size"]))),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=config["normalization"]["mean"],
            std=config["normalization"]["std"],
        ),
    ])

    with Image.open(image_path).convert("RGB") as image:
        tensor = transform(image).unsqueeze(0)
    with torch.inference_mode():
        probabilities = torch.softmax(model(tensor), dim=1)[0]
        indices = torch.argsort(probabilities, descending=True)[:top_k]

    idx_to_class = {int(key): value for key, value in config["idx_to_class"].items()}
    predictions = [
        {
            "label": idx_to_class.get(int(index), str(int(index))),
            "confidence": round(float(probabilities[index]), 4),
        }
        for index in indices
    ]
    return {"image": str(image_path), "predictions": predictions}


def main():
    parser = argparse.ArgumentParser(description="Predict a crop disease or pest from one image")
    parser.add_argument("image", type=Path, help="Path to the input image")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(predict(args.image, args.checkpoint, args.config, args.top_k), indent=2))


if __name__ == "__main__":
    main()
