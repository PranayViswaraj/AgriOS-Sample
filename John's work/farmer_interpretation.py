# AgroSmart Model 2 — Farmer Interpretation Layer

import json
from pathlib import Path

_CONFIG = Path(__file__).resolve().parent.parent / "config"

with open(_CONFIG / "farmer_status_map_v1.json", encoding="utf-8") as f:
    FARMER_STATUS_MAP = json.load(f)

with open(_CONFIG / "default_farmer_status_v1.json", encoding="utf-8") as f:
    DEFAULT_FARMER_STATUS = json.load(f)

def build_farmer_interpretation(
    epidemiological_result
):

    technical_status = (
        epidemiological_result.get(
            "environmental_suitability"
        )
    )

    interpretation = FARMER_STATUS_MAP.get(
        technical_status,
        DEFAULT_FARMER_STATUS
    ).copy()


    # Preserve technical traceability
    interpretation[
        "technical_status"
    ] = technical_status


    interpretation[
        "evidence_mode"
    ] = epidemiological_result.get(
        "evidence_mode"
    )


    interpretation[
        "case_priority"
    ] = epidemiological_result.get(
        "case_priority"
    )


    # --------------------------------------------------------
    # Scientific disclaimer
    # --------------------------------------------------------

    interpretation[
        "scientific_note"
    ] = (
        "This is an environmental disease-suitability "
        "assessment, not a calibrated probability of infection."
    )


    # --------------------------------------------------------
    # Treatment separation
    # --------------------------------------------------------

    interpretation[
        "treatment_note"
    ] = (
        "Treatment guidance is handled separately through "
        "the AgroSmart Treatment Knowledge Base and "
        "Extension Officer review workflow."
    )


    return interpretation

