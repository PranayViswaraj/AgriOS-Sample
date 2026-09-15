"""Export the trained EfficientNet checkpoint for browser-local ONNX inference."""

import sys
from pathlib import Path

import torch

from predict_mobile1 import load_checkpoint


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CHECKPOINT = ROOT_DIR / "John's work" / "agrosmart_model1_efficientnet_b0.pth"
DEFAULT_CONFIG = ROOT_DIR / "John's work" / "model_config.json"
DEFAULT_OUTPUT = ROOT_DIR / "frontend" / "models" / "mobile1_efficientnetb0.onnx"


def main():
    checkpoint = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CHECKPOINT
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    model, config = load_checkpoint(checkpoint, DEFAULT_CONFIG)
    output.parent.mkdir(parents=True, exist_ok=True)
    sample = torch.randn(1, 3, int(config["img_size"]), int(config["img_size"]))
    torch.onnx.export(
        model,
        sample,
        output,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
        dynamo=False,
    )
    print(output)


if __name__ == "__main__":
    main()
