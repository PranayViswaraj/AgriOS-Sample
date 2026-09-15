import io
import json
from pathlib import Path
from datetime import datetime
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

try:
    from john_integration import build_johns_model2_response
except Exception:  # pragma: no cover - optional integration layer
    build_johns_model2_response = None

DATABASE_URL = "postgresql+psycopg2://agrios:agrios@localhost:5432/agrios"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

VALID_TRAP_TYPES = {"Sticky Trap", "Light Trap", "Manual Count"}

try:
    import torch
    import torchvision.transforms as T
    from torchvision.models import efficientnet_b0
    from torch import nn
    from PIL import Image
except Exception:  # pragma: no cover - optional ML stack
    torch = None
    T = None
    efficientnet_b0 = None
    nn = None
    Image = None

ROOT_DIR = Path(__file__).resolve().parent.parent
JOHNS_WORK_DIR = ROOT_DIR / "John's work"
MODEL_CONFIG_PATH = JOHNS_WORK_DIR / "model_config.json"
MODEL_WEIGHT_PATH = JOHNS_WORK_DIR / "agrosmart_model1_efficientnet_b0.pth"
KNOWLEDGE_BASE_PATH = JOHNS_WORK_DIR / "MASTER_TREATMENT_KNOWLEDGE_BASE_V2.json"


@lru_cache(maxsize=1)
def load_model_config():
    with MODEL_CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_knowledge_base():
    with KNOWLEDGE_BASE_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def get_model_runtime():
    if torch is None or efficientnet_b0 is None or nn is None or Image is None:
        raise RuntimeError("PyTorch / torchvision / PIL are not installed in this environment")
    if not MODEL_CONFIG_PATH.exists() or not MODEL_WEIGHT_PATH.exists():
        raise FileNotFoundError("John's model artifact files are missing")

    config = load_model_config()
    model = efficientnet_b0(weights=None)
    classifier_in = model.classifier[1].in_features
    num_classes = int(config.get("num_classes", 15))
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.2, inplace=True),
        nn.Linear(classifier_in, num_classes),
    )

    checkpoint = torch.load(MODEL_WEIGHT_PATH, map_location="cpu")
    if isinstance(checkpoint, dict):
        if "state_dict" in checkpoint:
            checkpoint = checkpoint["state_dict"]
        elif "model_state_dict" in checkpoint:
            checkpoint = checkpoint["model_state_dict"]
        elif "model" in checkpoint and isinstance(checkpoint["model"], dict):
            checkpoint = checkpoint["model"]
    if isinstance(checkpoint, dict):
        clean_state = {}
        for key, value in checkpoint.items():
            normalized = key.replace("module.", "")
            clean_state[normalized] = value
        checkpoint = clean_state
    model.load_state_dict(checkpoint, strict=False)
    model.eval()
    return model, config


def normalize_prediction_label(value: str) -> str:
    if value is None:
        return ""
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def predict_uploaded_image(image_bytes: bytes, top_k: int = 3):
    model, config = get_model_runtime()
    transform = T.Compose([
        T.Resize((int(config["img_size"]), int(config["img_size"]))),
        T.ToTensor(),
        T.Normalize(mean=config["normalization"]["mean"], std=config["normalization"]["std"]),
    ])
    with Image.open(io.BytesIO(image_bytes)).convert("RGB") as image:
        tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0]
        sorted_idx = torch.argsort(probs, descending=True)

    idx_to_class = {int(k): v for k, v in config["idx_to_class"].items()}
    ranked = []
    for idx in sorted_idx[:top_k].tolist():
        prob = float(probs[int(idx)].item())
        label = idx_to_class.get(int(idx), str(int(idx)))
        ranked.append({"label": label, "confidence": round(prob, 4)})

    best_label = ranked[0]["label"] if ranked else "unknown"
    best_confidence = ranked[0]["confidence"] if ranked else 0.0
    return {"best_label": best_label, "confidence": best_confidence, "top_predictions": ranked}


def build_knowledge_case(predicted_label: str, crop_stage: str = "", symptom: str = ""):
    knowledge = load_knowledge_base()
    entry = knowledge.get("classes", {}).get(predicted_label)
    if entry is None:
        for key, value in knowledge.get("classes", {}).items():
            if predicted_label.endswith(key.split("__")[-1]) or key.endswith(predicted_label):
                entry = value
                break
    if entry is None:
        return {
            "predicted_label": predicted_label,
            "crop": "Unknown",
            "condition": "Unrecognized diagnosis",
            "summary": "The model detected an unrecognized pattern and this should be reviewed by an extension officer.",
            "management": {"immediate_actions": ["Request a second image and field check."]},
            "officer_review_required": True,
            "forecast": {"week_1": "Monitor closely for spread", "month_1": "Escalate if worsening"},
        }

    management = entry.get("management", {})
    monitoring = entry.get("monitoring", [])
    crop = entry.get("crop", "Crop")
    condition = entry.get("condition", "Detected issue")
    immediate = management.get("immediate_actions", [])
    cultural = management.get("cultural", [])
    biological = management.get("biological", [])
    chemical = management.get("chemical", [])
    forecast = {
        "horizon_days": 7,
        "week_1": f"{condition} may intensify over the next 7 days without active mitigation, especially under warm and humid conditions.",
        "month_1": f"If left untreated, the affected area may expand and recovery may take several weeks. Continue monitoring and reassess after 7–10 days.",
        "follow_up_due_in_days": 7,
    }

    return {
        "predicted_label": predicted_label,
        "crop": crop,
        "condition": condition,
        "summary": f"Detected {condition} in {crop}.",
        "symptom_context": symptom or entry.get("symptoms", ["Field symptoms need verification"])[0],
        "crop_stage": crop_stage or "Not specified",
        "management": {
            "immediate_actions": immediate[:4],
            "cultural": cultural[:4],
            "biological": biological[:4],
            "chemical": chemical[:4],
        },
        "monitoring": monitoring[:4],
        "officer_review_required": True,
        "forecast": forecast,
    }


def validate_lat_lon(latitude: float, longitude: float, label: str = "GPS") -> tuple[float, float]:
    if latitude is None or longitude is None:
        raise HTTPException(400, f"{label} coordinates are required")
    latitude = float(latitude)
    longitude = float(longitude)
    if not -90 <= latitude <= 90:
        raise HTTPException(400, "Latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise HTTPException(400, "Longitude must be between -180 and 180")
    return latitude, longitude


def validate_image_upload(file: Optional[UploadFile]) -> None:
    if file is None:
        raise HTTPException(400, "Image file is required")
    if not file.filename:
        raise HTTPException(400, "Image filename is required")
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(400, "Uploaded file must be an image")


class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    farmer_name = Column(String(120), nullable=False)
    taluk = Column(String(120), nullable=False)
    district = Column(String(120), nullable=False)
    crop = Column(String(80), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FieldObservation(Base):
    __tablename__ = "field_observations"
    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, nullable=False)
    crop = Column(String(80), nullable=False)
    growth_stage = Column(String(80), nullable=True)
    symptom = Column(Text, nullable=True)
    disease_pest = Column(String(120), nullable=True)
    severity = Column(String(30), nullable=True)
    source = Column(String(30), nullable=False, default="farmer")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    image_path = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True)
    model_version = Column(String(80), nullable=True)
    observed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class PestTrapObservation(Base):
    __tablename__ = "pest_trap_observations"
    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, nullable=False)
    trap_type = Column(String(80), nullable=False)
    pest_name = Column(String(120), nullable=True)
    count = Column(Integer, nullable=False, default=0)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    image_path = Column(String(255), nullable=True)
    observed_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgriOS GIS & Field Input API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class FarmCreate(BaseModel):
    name: str
    farmer_name: str
    taluk: str
    district: str
    crop: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ObservationCreate(BaseModel):
    farm_id: int
    crop: str
    growth_stage: Optional[str] = None
    symptom: Optional[str] = None
    disease_pest: Optional[str] = None
    severity: Optional[str] = None
    source: str = "farmer"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    confidence: Optional[float] = None
    model_version: Optional[str] = None
    observed_at: Optional[datetime] = None


class JohnModel2PreviewRequest(BaseModel):
    class_name: str
    forecast_records: list[dict]
    affected_extent: Optional[str] = None
    progression: Optional[str] = None
    crop_stage: Optional[str] = None
    time_untreated_days: Optional[float] = None
    species_confirmed: Optional[bool] = None
    confirmed_species: Optional[str] = None
    current_case: bool = True


@app.get("/")
def root():
    return {"message": "AgriOS GIS & Field Input API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/john-model2/preview")
def john_model2_preview(payload: JohnModel2PreviewRequest):
    if build_johns_model2_response is None:
        raise HTTPException(503, "John's model integration is currently unavailable in this build")

    try:
        result = build_johns_model2_response(
            class_name=payload.class_name,
            forecast_records=payload.forecast_records,
            affected_extent=payload.affected_extent,
            progression=payload.progression,
            crop_stage=payload.crop_stage,
            time_untreated_days=payload.time_untreated_days,
            species_confirmed=payload.species_confirmed,
            confirmed_species=payload.confirmed_species,
            current_case=payload.current_case,
        )
        return result
    except Exception as exc:  # pragma: no cover - integration should surface validation cleanly
        raise HTTPException(400, f"John model preview failed: {exc}")


@app.post("/farms")
def create_farm(data: FarmCreate, db: Session = Depends(get_db)):
    farm = Farm(
        name=data.name,
        farmer_name=data.farmer_name,
        taluk=data.taluk,
        district=data.district,
        crop=data.crop,
        latitude=data.latitude,
        longitude=data.longitude,
        location=from_shape(Point(data.longitude, data.latitude), srid=4326),
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return {"id": farm.id, "message": "Farm created"}


@app.get("/farms")
def list_farms(db: Session = Depends(get_db)):
    farms = db.query(Farm).order_by(Farm.id.desc()).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "farmer_name": f.farmer_name,
            "taluk": f.taluk,
            "district": f.district,
            "crop": f.crop,
            "latitude": f.latitude,
            "longitude": f.longitude,
        }
        for f in farms
    ]


@app.post("/ai/classify-image")
async def classify_image(
    farm_id: int = Form(...),
    crop: str = Form(...),
    growth_stage: str = Form(""),
    symptom: str = Form(""),
    source: str = Form("farmer"),
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(404, "Farm not found")

    validate_image_upload(image)
    latitude, longitude = validate_lat_lon(latitude, longitude, "Observation")
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(400, "Uploaded image is empty")

    prediction = predict_uploaded_image(image_bytes)
    best_label = prediction["best_label"]
    knowledge = build_knowledge_case(best_label, crop_stage=growth_stage, symptom=symptom)

    safe_name = Path(image.filename or "image.jpg").name
    filename = f"ai_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{safe_name}"
    destination = UPLOAD_DIR / filename
    destination.write_bytes(image_bytes)

    observation = FieldObservation(
        farm_id=farm_id,
        crop=crop,
        growth_stage=growth_stage,
        symptom=symptom,
        disease_pest=best_label,
        severity="Moderate" if prediction["confidence"] >= 0.6 else "Mild",
        source=source or "farmer",
        latitude=latitude,
        longitude=longitude,
        image_path=f"/uploads/{filename}",
        location=from_shape(Point(longitude, latitude), srid=4326),
        confidence=prediction["confidence"],
        model_version="agrosmart_model1_efficientnet_b0",
        observed_at=datetime.utcnow(),
    )
    db.add(observation)
    db.commit()
    db.refresh(observation)

    return {
        "observation_id": observation.id,
        "prediction": prediction,
        "knowledge": knowledge,
        "image_url": observation.image_path,
        "message": "Disease/pest prediction and treatment guidance generated",
    }


@app.post("/ai/forecast-and-case")
async def forecast_and_case(
    farm_id: int = Form(...),
    crop: str = Form(...),
    growth_stage: str = Form(""),
    symptom: str = Form(""),
    source: str = Form("farmer"),
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    result = await classify_image(
        farm_id=farm_id,
        crop=crop,
        growth_stage=growth_stage,
        symptom=symptom,
        source=source,
        latitude=latitude,
        longitude=longitude,
        image=image,
        db=db,
    )
    prediction = result["prediction"]
    best_label = prediction["best_label"]
    knowledge = result["knowledge"]
    predicted_disease = knowledge.get("condition", best_label)

    return {
        "disease_detected": predicted_disease,
        "predicted_label": best_label,
        "confidence": prediction["confidence"],
        "top_predictions": prediction["top_predictions"],
        "forecast": knowledge.get("forecast", {}),
        "management": knowledge.get("management", {}),
        "monitoring": knowledge.get("monitoring", []),
        "officer_review_required": True,
        "case_status": "awaiting_extension_officer_review",
        "image_url": result["image_url"],
        "message": "AI diagnosis generated and escalated for extension officer review.",
    }


@app.post("/field-observations")
async def create_observation(data: ObservationCreate, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == data.farm_id).first()
    if not farm:
        raise HTTPException(404, "Farm not found")

    if data.confidence is not None and not 0 <= float(data.confidence) <= 1:
        raise HTTPException(400, "Confidence must be between 0 and 1")

    latitude, longitude = validate_lat_lon(data.latitude, data.longitude, "Observation")

    obs = FieldObservation(
        farm_id=data.farm_id,
        crop=data.crop,
        growth_stage=data.growth_stage,
        symptom=data.symptom,
        disease_pest=data.disease_pest,
        severity=data.severity,
        source=data.source or "farmer",
        latitude=latitude,
        longitude=longitude,
        location=from_shape(Point(longitude, latitude), srid=4326),
        confidence=data.confidence,
        model_version=data.model_version,
        observed_at=data.observed_at or datetime.utcnow(),
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return {"id": obs.id, "message": "Field observation recorded"}


@app.post("/field-observations/with-image")
async def create_observation_with_image(
    farm_id: int = Form(...),
    crop: str = Form(...),
    growth_stage: str = Form(""),
    symptom: str = Form(""),
    disease_pest: str = Form(""),
    severity: str = Form(""),
    source: str = Form("farmer"),
    latitude: float = Form(...),
    longitude: float = Form(...),
    confidence: Optional[float] = Form(None),
    model_version: Optional[str] = Form(None),
    observed_at: Optional[datetime] = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(404, "Farm not found")

    validate_image_upload(image)
    if confidence is not None and not 0 <= float(confidence) <= 1:
        raise HTTPException(400, "Confidence must be between 0 and 1")

    latitude, longitude = validate_lat_lon(latitude, longitude, "Observation")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(400, "Uploaded image is empty")

    safe_name = Path(image.filename or "image.jpg").name
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{safe_name}"
    destination = UPLOAD_DIR / filename
    destination.write_bytes(image_bytes)

    obs = FieldObservation(
        farm_id=farm_id,
        crop=crop,
        growth_stage=growth_stage,
        symptom=symptom,
        disease_pest=disease_pest,
        severity=severity,
        source=source or "farmer",
        latitude=latitude,
        longitude=longitude,
        image_path=f"/uploads/{filename}",
        location=from_shape(Point(longitude, latitude), srid=4326),
        confidence=confidence,
        model_version=model_version,
        observed_at=observed_at or datetime.utcnow(),
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return {"id": obs.id, "image_url": obs.image_path, "message": "Observation + image saved"}


@app.get("/field-observations")
def list_observations(db: Session = Depends(get_db)):
    rows = db.query(FieldObservation).order_by(FieldObservation.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "farm_id": r.farm_id,
            "crop": r.crop,
            "growth_stage": r.growth_stage,
            "symptom": r.symptom,
            "disease_pest": r.disease_pest,
            "severity": r.severity,
            "source": r.source,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "image_url": r.image_path,
            "confidence": r.confidence,
            "model_version": r.model_version,
            "observed_at": r.observed_at.isoformat() if r.observed_at else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@app.post("/pest-traps")
async def create_pest_trap(
    farm_id: int = Form(...),
    trap_type: str = Form(...),
    pest_name: str = Form(""),
    count: int = Form(0),
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(404, "Farm not found")

    latitude, longitude = validate_lat_lon(latitude, longitude, "Trap")
    trap_type = (trap_type or "Manual Count").strip()
    if trap_type not in VALID_TRAP_TYPES:
        raise HTTPException(400, f"Trap type must be one of: {', '.join(sorted(VALID_TRAP_TYPES))}")

    image_path = None
    if image:
        validate_image_upload(image)
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(400, "Uploaded image is empty")
        safe_name = Path(image.filename or "trap.jpg").name
        filename = f"trap_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{safe_name}"
        destination = UPLOAD_DIR / filename
        destination.write_bytes(image_bytes)
        image_path = f"/uploads/{filename}"

    row = PestTrapObservation(
        farm_id=farm_id,
        trap_type=trap_type,
        pest_name=pest_name,
        count=count,
        latitude=latitude,
        longitude=longitude,
        image_path=image_path,
        location=from_shape(Point(longitude, latitude), srid=4326),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "image_url": image_path, "message": "Pest-trap input saved"}


@app.get("/pest-traps")
def list_pest_traps(db: Session = Depends(get_db)):
    rows = db.query(PestTrapObservation).order_by(PestTrapObservation.observed_at.desc()).all()
    return [
        {
            "id": r.id,
            "farm_id": r.farm_id,
            "trap_type": r.trap_type,
            "pest_name": r.pest_name,
            "count": r.count,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "image_url": r.image_path,
            "observed_at": r.observed_at.isoformat() if r.observed_at else None,
        }
        for r in rows
    ]


@app.get("/hotspots")
def hotspots(db: Session = Depends(get_db)):
    rows = db.query(FieldObservation).filter(
        FieldObservation.disease_pest.isnot(None),
        FieldObservation.disease_pest != "",
        FieldObservation.latitude.isnot(None),
        FieldObservation.longitude.isnot(None),
    ).all()

    if not rows:
        return []

    def severity_rank(value: Optional[str]) -> int:
        if not value:
            return 0
        value = value.strip().lower()
        if value == "severe":
            return 3
        if value == "moderate":
            return 2
        if value == "mild":
            return 1
        return 0

    disease_groups = {}
    for row in rows:
        disease = (row.disease_pest or "").strip()
        if disease:
            disease_groups.setdefault(disease, []).append(row)

    hotspot_results = []
    for disease, items in disease_groups.items():
        clusters = []
        if items:
            current_cluster = [items[0]]
            for item in items[1:]:
                last_item = current_cluster[-1]
                distance = ((item.latitude - last_item.latitude) ** 2 + (item.longitude - last_item.longitude) ** 2) ** 0.5
                if distance <= 0.25:
                    current_cluster.append(item)
                else:
                    clusters.append(current_cluster)
                    current_cluster = [item]
            clusters.append(current_cluster)

        for cluster in clusters:
            case_count = len(cluster)
            lat = sum(item.latitude for item in cluster) / case_count
            lon = sum(item.longitude for item in cluster) / case_count
            severity_counts = {}
            for item in cluster:
                sev = (item.severity or "Unknown").strip() or "Unknown"
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            severity_summary = max(severity_counts.items(), key=lambda kv: (severity_rank(kv[0]), kv[1]))[0]
            hotspot_results.append(
                {
                    "hotspot_latitude": round(float(lat), 5),
                    "hotspot_longitude": round(float(lon), 5),
                    "disease_pest": disease,
                    "case_count": case_count,
                    "severity_summary": severity_summary,
                    "severity_breakdown": severity_counts,
                }
            )

    hotspot_results.sort(key=lambda item: (-item["case_count"], -item["hotspot_latitude"], -item["hotspot_longitude"]))
    return hotspot_results


@app.get("/statistics")
def statistics(db: Session = Depends(get_db)):
    total_farms = db.query(Farm).count()
    total_field_observations = db.query(FieldObservation).count()
    total_pest_observations = db.query(PestTrapObservation).count()

    disease_counts = [
        {"disease_pest": row[0], "count": row[1]}
        for row in db.query(
            FieldObservation.disease_pest,
            func.count(FieldObservation.id).label("count"),
        ).filter(
            FieldObservation.disease_pest.isnot(None),
            FieldObservation.disease_pest != "",
        ).group_by(FieldObservation.disease_pest).order_by(func.count(FieldObservation.id).desc()).all()
    ]

    severity_counts = [
        {"severity": row[0], "count": row[1]}
        for row in db.query(
            FieldObservation.severity,
            func.count(FieldObservation.id).label("count"),
        ).filter(
            FieldObservation.severity.isnot(None),
            FieldObservation.severity != "",
        ).group_by(FieldObservation.severity).order_by(func.count(FieldObservation.id).desc()).all()
    ]

    return {
        "total_farms": total_farms,
        "total_field_observations": total_field_observations,
        "total_pest_observations": total_pest_observations,
        "disease_pest_counts": disease_counts,
        "severity_counts": severity_counts,
        "hotspot_count": len(hotspots(db)),
    }
