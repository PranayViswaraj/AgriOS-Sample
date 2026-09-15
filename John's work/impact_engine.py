# AgroSmart Model 2 — Case Impact Engine

import json
from pathlib import Path

_CONFIG = Path(__file__).resolve().parent.parent / "impact_rules"

with open(_CONFIG / "MODEL2_IMPACT_EVIDENCE_REGISTRY_V1.json", encoding="utf-8") as f:
    impact_registry = json.load(f)

VALID_AFFECTED_EXTENT = {"LOCALIZED", "MODERATE", "EXTENSIVE"}
VALID_PROGRESSION = {"IMPROVING", "STABLE", "SPREADING", "RAPIDLY_SPREADING"}

def evaluate_case_impact(
    class_name,
    affected_extent=None,
    progression=None,
    crop_stage=None,
    time_untreated_days=None,
    species_confirmed=None,
    confirmed_species=None
):

    if class_name not in impact_registry:

        raise ValueError(
            f"Unknown class_name: {class_name}"
        )


    entry = impact_registry[
        class_name
    ]


    # --------------------------------------------------------
    # Normalize case inputs
    # --------------------------------------------------------

    affected_extent = normalize_token(
        affected_extent
    )

    progression = normalize_token(
        progression
    )

    crop_stage = normalize_token(
        crop_stage
    )


    # --------------------------------------------------------
    # Validate supplied categorical inputs
    # --------------------------------------------------------

    if (
        affected_extent is not None
        and
        affected_extent not in VALID_AFFECTED_EXTENT
    ):

        raise ValueError(
            "affected_extent must be one of: "
            + ", ".join(
                sorted(
                    VALID_AFFECTED_EXTENT
                )
            )
        )


    if (
        progression is not None
        and
        progression not in VALID_PROGRESSION
    ):

        raise ValueError(
            "progression must be one of: "
            + ", ".join(
                sorted(
                    VALID_PROGRESSION
                )
            )
        )


    if (
        time_untreated_days is not None
        and
        (
            not isinstance(
                time_untreated_days,
                (int, float)
            )
            or
            time_untreated_days < 0
        )
    ):

        raise ValueError(
            "time_untreated_days must be a "
            "non-negative number or None."
        )


    # ========================================================
    # 4. MISSING INPUT AUDIT
    # ========================================================

    missing_inputs = []

    if affected_extent is None:
        missing_inputs.append(
            "affected_extent"
        )

    if progression is None:
        missing_inputs.append(
            "progression"
        )

    if crop_stage is None:
        missing_inputs.append(
            "crop_stage"
        )

    if time_untreated_days is None:
        missing_inputs.append(
            "time_untreated_days"
        )


    # ========================================================
    # 5. CROP-STAGE MATCHING
    # ========================================================

    high_consequence_stages = {

        normalize_token(stage)

        for stage in entry[
            "crop_stage_context"
        ].get(
            "high_consequence_stages",
            []
        )
    }


    stage_sensitive = entry[
        "crop_stage_context"
    ].get(
        "stage_sensitive",
        False
    )


    high_consequence_stage = (
        crop_stage in high_consequence_stages
        if crop_stage is not None
        else False
    )


    # ========================================================
    # 6. CASE IMPACT PRIORITY
    #
    # IMPORTANT:
    # This is operational triage.
    # It is NOT calibrated crop-loss probability
    # and NOT a yield-loss percentage.
    # ========================================================

    reasons = []


    if missing_inputs:

        impact_priority = (
            "LIMITED_ASSESSMENT"
        )

        impact_label = (
            "More field information required"
        )

        reasons.append(
            "Required case information is incomplete."
        )


    else:

        # ----------------------------------------------------
        # Highest concern:
        # extensive field involvement or rapidly spreading case
        # ----------------------------------------------------

        if (
            affected_extent == "EXTENSIVE"
            or
            progression == "RAPIDLY_SPREADING"
        ):

            impact_priority = (
                "HIGH_CASE_IMPACT_PRIORITY"
            )

            impact_label = (
                "High field-impact concern"
            )

            if affected_extent == "EXTENSIVE":

                reasons.append(
                    "A large portion of the observed crop "
                    "is reported as affected."
                )

            if progression == "RAPIDLY_SPREADING":

                reasons.append(
                    "The condition is reported as rapidly spreading."
                )


        # ----------------------------------------------------
        # Elevated concern
        # ----------------------------------------------------

        elif (
            affected_extent == "MODERATE"
            or
            progression == "SPREADING"
            or
            high_consequence_stage
        ):

            impact_priority = (
                "ELEVATED_CASE_IMPACT_PRIORITY"
            )

            impact_label = (
                "Elevated field-impact concern"
            )

            if affected_extent == "MODERATE":

                reasons.append(
                    "A moderate portion of the observed crop "
                    "is reported as affected."
                )

            if progression == "SPREADING":

                reasons.append(
                    "The condition is reported as continuing to spread."
                )

            if high_consequence_stage:

                reasons.append(
                    "The crop is currently in a stage identified "
                    "as potentially higher consequence for this condition."
                )


        # ----------------------------------------------------
        # Lower operational concern
        # ----------------------------------------------------

        else:

            impact_priority = (
                "MONITOR_CASE_IMPACT"
            )

            impact_label = (
                "Monitor current field impact"
            )

            reasons.append(
                "Current field extent and progression do not "
                "indicate the highest operational impact category."
            )


    # ========================================================
    # 7. UNTREATED DURATION
    #
    # Duration is recorded as context ONLY.
    # No universal arbitrary day threshold is used.
    # ========================================================

    untreated_context = {

        "days":
            time_untreated_days,

        "interpretation":
            (
                "Untreated duration is retained as case context. "
                "AgroSmart does not convert untreated days directly "
                "into a yield-loss percentage."
            )
    }


    # ========================================================
    # 8. BOLLWORM SPECIES GATE
    # ========================================================

    species_gate_result = None

    if class_name == "cotton__bollworm":

        species_gate_result = {

            "species_confirmation_required":
                True,

            "species_confirmed":
                bool(
                    species_confirmed
                ),

            "confirmed_species":
                confirmed_species,

            "species_specific_quantification_allowed":
                False,

            "note":
                (
                    "Model 1 detects generic bollworm. "
                    "Species-specific impact evidence cannot be "
                    "used unless an agricultural expert independently "
                    "confirms the species."
                )
        }


    # ========================================================
    # 9. QUANTITATIVE CLAIM CONTROL
    # ========================================================

    quantitative_allowed = entry[
        "claim_control"
    ][
        "allow_quantitative_loss"
    ]

    yield_preserved_allowed = entry[
        "claim_control"
    ][
        "allow_quantitative_yield_preserved"
    ]


    # These MUST currently remain False.
    estimated_yield_loss_percent = None
    estimated_yield_preserved_percent = None


    # ========================================================
    # 10. FARMER-FACING INTERPRETATION
    # ========================================================

    farmer_message_map = {

        "LIMITED_ASSESSMENT":
            (
                "More field information is needed before the "
                "likely crop impact can be assessed."
            ),

        "HIGH_CASE_IMPACT_PRIORITY":
            (
                "The reported field condition suggests a higher "
                "potential for crop impact. Extension Officer review "
                "is recommended promptly."
            ),

        "ELEVATED_CASE_IMPACT_PRIORITY":
            (
                "The reported field condition may have meaningful "
                "crop impact. Continue monitoring and follow the "
                "Extension Officer's management guidance."
            ),

        "MONITOR_CASE_IMPACT":
            (
                "Current field observations suggest continued "
                "monitoring is appropriate. Report any increase "
                "in affected area or disease/pest spread."
            )
    }


    # ========================================================
    # 11. OUTPUT
    # ========================================================

    output = {

        "impact_schema_version":
            "MODEL2_CASE_IMPACT_V1",

        "crop":
            entry["crop"],

        "class_name":
            class_name,

        "condition_name":
            entry["condition_name"],


        # ----------------------------------------------------
        # Case inputs
        # ----------------------------------------------------

        "case_inputs": {

            "affected_extent":
                affected_extent,

            "progression":
                progression,

            "crop_stage":
                crop_stage,

            "time_untreated_days":
                time_untreated_days
        },


        # ----------------------------------------------------
        # Case assessment
        # ----------------------------------------------------

        "impact_assessment": {

            "impact_priority":
                impact_priority,

            "impact_label":
                impact_label,

            "reasons":
                reasons,

            "high_consequence_stage":
                high_consequence_stage,

            "stage_sensitive_condition":
                stage_sensitive,

            "assessment_type":
                "QUALITATIVE_FIELD_IMPACT_TRIAGE",

            "calibrated_yield_loss_model":
                False
        },


        # ----------------------------------------------------
        # Untreated duration
        # ----------------------------------------------------

        "untreated_duration_context":
            untreated_context,


        # ----------------------------------------------------
        # Disease evidence
        # ----------------------------------------------------

        "known_impact": {

            "affected_plant_parts":
                entry[
                    "qualitative_impact"
                ][
                    "affected_plant_parts"
                ],

            "possible_consequences":
                entry[
                    "qualitative_impact"
                ][
                    "possible_consequences"
                ],

            "yield_impact_supported":
                entry[
                    "qualitative_impact"
                ][
                    "yield_impact_supported"
                ],

            "quality_impact_supported":
                entry[
                    "qualitative_impact"
                ][
                    "quality_impact_supported"
                ]
        },


        # ----------------------------------------------------
        # Quantitative output
        # ----------------------------------------------------

        "quantitative_impact": {

            "estimated_yield_loss_percent":
                estimated_yield_loss_percent,

            "estimated_yield_preserved_percent":
                estimated_yield_preserved_percent,

            "quantitative_loss_allowed":
                quantitative_allowed,

            "quantitative_yield_preserved_allowed":
                yield_preserved_allowed,

            "message":
                entry[
                    "claim_control"
                ][
                    "default_user_message"
                ]
        },


        # ----------------------------------------------------
        # Management interpretation
        # ----------------------------------------------------

        "management_interpretation": {

            "message":
                entry[
                    "management_effect"
                ][
                    "interpretation"
                ],

            "claim":
                (
                    "Management is intended to reduce further "
                    "disease/pest progression and preserve remaining "
                    "yield potential; it is not represented as "
                    "creating additional crop yield."
                )
        },


        # ----------------------------------------------------
        # Farmer output
        # ----------------------------------------------------

        "farmer_interpretation": {

            "headline":
                farmer_message_map[
                    impact_priority
                ],

            "quantitative_loss_message":
                entry[
                    "claim_control"
                ][
                    "default_user_message"
                ]
        },


        # ----------------------------------------------------
        # Evidence
        # ----------------------------------------------------

        "scientific_traceability": {

            "impact_evidence_classification":
                entry.get(
                    "impact_evidence_classification"
                ),

            "evidence_level":
                entry[
                    "evidence"
                ][
                    "evidence_level"
                ],

            "source_ids":
                entry[
                    "evidence"
                ][
                    "source_ids"
                ],

            "limitations":
                entry[
                    "evidence"
                ][
                    "limitations"
                ]
        },


        # ----------------------------------------------------
        # Species gate
        # ----------------------------------------------------

        "species_gate":
            species_gate_result
    }


    return output

