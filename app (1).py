"""
Clinical Records RESTful API
Flask service that stores clinical records in BOTH:
  - SQLite (clinical_data.db)          -> transactional integrity
  - JSON Lines (data/clinical_data.jsonl) -> append-only audit trail

Endpoints:
  POST /clinical/  - validate and add a record (writes to DB + appends a JSON line)
  GET  /clinical/  - list all records from the database

Three columns added to the base walkthrough (model, schema and endpoints):
  blood_pressure  - e.g. "120/80" (systolic/diastolic, mmHg)
  heart_rate      - beats per minute (integer, 20-250)
  allergies       - known allergies (text, defaults to "None")
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from flask import Flask, jsonify, request
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ---------------------------------------------------------------------------
# Storage configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "clinical_data.db")
DATA_DIR = os.path.join(BASE_DIR, "data")
JSONL_PATH = os.path.join(DATA_DIR, "clinical_data.jsonl")

os.makedirs(DATA_DIR, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Database model (SQLAlchemy)
# ---------------------------------------------------------------------------
class ClinicalData(Base):
    __tablename__ = "clinical_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(50), nullable=False)
    patient_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    diagnosis = Column(String(255), nullable=False)

    # --- New columns ---
    blood_pressure = Column(String(20), nullable=False)
    heart_rate = Column(Integer, nullable=False)
    allergies = Column(String(255), nullable=False, default="None")

    created_at = Column(DateTime, nullable=False,
                        default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(engine)


# ---------------------------------------------------------------------------
# Pydantic schemas (validation)
# ---------------------------------------------------------------------------
class ClinicalDataCreate(BaseModel):
    """Schema for incoming POST data."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    patient_id: str = Field(..., min_length=1, max_length=50)
    patient_name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=130)
    diagnosis: str = Field(..., min_length=1, max_length=255)

    # --- New fields ---
    blood_pressure: str = Field(..., pattern=r"^\d{2,3}/\d{2,3}$",
                                description='Systolic/diastolic, e.g. "120/80"')
    heart_rate: int = Field(..., ge=20, le=250, description="Beats per minute")
    allergies: Optional[str] = Field(default="None", max_length=255)


class ClinicalDataRead(ClinicalDataCreate):
    """Schema for records returned by the API."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Flask app and endpoints
# ---------------------------------------------------------------------------
app = Flask(__name__)


@app.route("/clinical/", methods=["POST"], strict_slashes=False)
def add_clinical_record():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    # Semantic layer: validate with Pydantic
    try:
        record_in = ClinicalDataCreate.model_validate(payload)
    except ValidationError as e:
        return jsonify({"error": "Validation failed",
                        "details": json.loads(e.json())}), 422

    session = SessionLocal()
    try:
        # 1) Write to SQLite (flush assigns the id without committing yet)
        record = ClinicalData(**record_in.model_dump())
        if record.allergies is None:
            record.allergies = "None"
        session.add(record)
        session.flush()

        record_out = ClinicalDataRead.model_validate(record)
        record_json = record_out.model_dump(mode="json")

        # 2) Append one JSON line to the audit file
        with open(JSONL_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record_json) + "\n")

        # 3) Commit only after both writes succeed
        session.commit()
        return jsonify(record_json), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Could not save record", "details": str(e)}), 500
    finally:
        session.close()


@app.route("/clinical/", methods=["GET"], strict_slashes=False)
def list_clinical_records():
    session = SessionLocal()
    try:
        records = session.query(ClinicalData).order_by(ClinicalData.id).all()
        return jsonify([
            ClinicalDataRead.model_validate(r).model_dump(mode="json")
            for r in records
        ]), 200
    finally:
        session.close()


if __name__ == "__main__":
    # Port 5001 because macOS AirPlay Receiver often occupies port 5000
    app.run(debug=True, port=5001)
