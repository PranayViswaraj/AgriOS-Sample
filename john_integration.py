import importlib.util
import sys
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
JOHNS_WORK_DIR = ROOT_DIR / "John's work"
CONFIG_DIR = ROOT_DIR / "config"
IMPACT_RULES_DIR = ROOT_DIR / "impact_rules"
PACKAGE_NAME = "johns_model_artifacts"


def ensure_john_artifact_paths():
    if not JOHNS_WORK_DIR.exists():
        raise FileNotFoundError(f"John's work directory not found: {JOHNS_WORK_DIR}")

    CONFIG_DIR.mkdir(exist_ok=True)
    IMPACT_RULES_DIR.mkdir(exist_ok=True)

    for filename in ["farmer_status_map_v1.json", "default_farmer_status_v1.json"]:
        src = JOHNS_WORK_DIR / filename
        dst = CONFIG_DIR / filename
        if src.exists() and not dst.exists():
            dst.write_bytes(src.read_bytes())

    for filename in ["MODEL2_IMPACT_EVIDENCE_REGISTRY_V1.json"]:
        src = JOHNS_WORK_DIR / filename
        dst = IMPACT_RULES_DIR / filename
        if src.exists() and not dst.exists():
            dst.write_bytes(src.read_bytes())


def normalize_token(value):
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip().replace("-", "_").replace(" ", "_")
        return cleaned.upper()
    return str(value).strip().replace("-", "_").replace(" ", "_").upper()


@lru_cache(maxsize=1)
def load_johns_work_modules():
    ensure_john_artifact_paths()

    package = sys.modules.get(PACKAGE_NAME)
    if package is None:
        package = type(sys)(PACKAGE_NAME)
        package.__path__ = [str(JOHNS_WORK_DIR)]
        sys.modules[PACKAGE_NAME] = package

    module_names = [
        "impact_engine",
        "crop_adapters",
        "farmer_interpretation",
        "weather_adapter",
        "forecast_standardizer",
        "epidemiological_core",
        "response_builder",
    ]

    for module_name in module_names:
        full_name = f"{PACKAGE_NAME}.{module_name}"
        if full_name not in sys.modules:
            path = JOHNS_WORK_DIR / f"{module_name}.py"
            if not path.exists():
                continue
            spec = importlib.util.spec_from_file_location(full_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[full_name] = module
            setattr(module, "normalize_token", normalize_token)
            spec.loader.exec_module(module)

    response_builder = sys.modules.get(f"{PACKAGE_NAME}.response_builder")
    response_builder.__dict__.setdefault("normalize_token", normalize_token)
    response_builder.__dict__.setdefault("datetime", datetime)
    response_builder.__dict__.setdefault("timezone", timezone)

    impact_engine = sys.modules.get(f"{PACKAGE_NAME}.impact_engine")
    if impact_engine is not None:
        impact_engine.__dict__.setdefault("normalize_token", normalize_token)

    response_builder = sys.modules.get(f"{PACKAGE_NAME}.response_builder")
    if response_builder is None:
        raise ImportError("John's response builder could not be loaded")

    response_builder.__dict__.setdefault("datetime", datetime)
    response_builder.__dict__.setdefault("timezone", timezone)
    return response_builder


def build_johns_model2_response(class_name, forecast_records, **kwargs):
    builder = load_johns_work_modules()
    return builder.build_model2_combined_response(
        class_name=class_name,
        forecast_records=forecast_records,
        **kwargs,
    )
