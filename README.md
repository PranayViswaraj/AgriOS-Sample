# AgriOS — Pranay GIS + Field/Pest Inputs

## Your exact responsibility

Build and deliver:
1. Farm registration with crop + taluk/district + GPS.
2. Field observation input.
3. Leaf/pest image upload metadata (AI result is supplied later by Jothi).
4. Pest-trap/manual pest-count input.
5. GPS-tagged records.
6. GIS map for farms, cases and pest traps.
7. Hotspot API for officer/official dashboards.
8. APIs that John/Jothi/Sanjana/Sanjay/Thanushka can consume.

Do NOT build:
- disease AI model — Jothi
- risk forecasting — Sanjana
- IPDM knowledge/advisory engine — Sanjay
- authentication/3-role authorization — John
- officer dashboard workflow — Thanushka

## 1. Install

Requirements:
- Windows 10/11
- Python 3.11 or 3.12
- Docker Desktop
- VS Code recommended

Start database:

```bash
docker compose up -d
```

Create Python environment:

```bash
cd backend
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Run API:

```bash
uvicorn main:app --reload
```

API:
http://127.0.0.1:8000

Swagger:
http://127.0.0.1:8000/docs

## 2. Run frontend

Open `frontend/index.html` in the browser.

If the browser blocks local file requests, run:

```bash
cd frontend
python -m http.server 5500
```

Then open:
http://127.0.0.1:5500

## 3. First demo

1. Register a farm.
2. Use actual GPS or enter coordinates.
3. Add a field observation.
4. Upload a leaf/pest image.
5. Add pest-trap count/image.
6. Refresh the map.
7. Show the map to the team.
8. Give the API endpoints to John for integration.

## 4. API endpoints

GET /health
GET /farms
POST /farms
GET /field-observations
POST /field-observations
POST /field-observations/with-image
GET /pest-traps
POST /pest-traps
GET /hotspots

## 5. Important integration contract

Jothi's AI output should eventually update the field observation:
- disease_pest
- severity
- confidence (add this column later)
- model_version (add this later)

Sanjana can consume:
- farm location
- crop
- growth stage
- detected disease/pest
- observation timestamp

Thanushka can consume:
- /hotspots
- /field-observations
- /pest-traps

John can put JWT authentication/API gateway around these endpoints.

## 6. Production upgrades after this prototype works

Only after the above is working:
- add JWT/user_id
- add confidence/model_version
- use PostGIS spatial queries for real radius/cluster hotspots
- add pagination
- add image-size/type validation
- connect cloud object storage
- connect official dashboard
