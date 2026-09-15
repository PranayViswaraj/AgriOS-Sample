# AgroSmart Model 2 — Combined Response Builder

from .impact_engine import evaluate_case_impact, impact_registry

def build_model2_combined_response(
    class_name,
    forecast_records,
    affected_extent=None,
    progression=None,
    crop_stage=None,
    time_untreated_days=None,
    species_confirmed=None,
    confirmed_species=None,
    current_case=True
):

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if class_name not in impact_registry:
        raise ValueError(
            f"Unknown class_name: {class_name}"
        )

    if not isinstance(
        forecast_records,
        list
    ):
        raise ValueError(
            "forecast_records must be a list."
        )

    if len(
        forecast_records
    ) == 0:
        raise ValueError(
            "forecast_records cannot be empty."
        )


    # ========================================================
    # 2. CASE IMPACT
    # ========================================================

    impact_result = evaluate_case_impact(

        class_name=class_name,

        affected_extent=
            affected_extent,

        progression=
            progression,

        crop_stage=
            crop_stage,

        time_untreated_days=
            time_untreated_days,

        species_confirmed=
            species_confirmed,

        confirmed_species=
            confirmed_species
    )


    # ========================================================
    # 3. FORECAST SUMMARY
    # ========================================================

    daily_statuses = []

    attention_levels = []

    for day in forecast_records:

        epi = day[
            "epidemiological_assessment"
        ]

        farmer = day[
            "farmer_interpretation"
        ]

        daily_statuses.append(
            epi.get(
                "environmental_suitability"
            )
        )

        attention_levels.append(
            farmer.get(
                "attention_level"
            )
        )


    # --------------------------------------------------------
    # Forecast attention summary
    # --------------------------------------------------------

    attention_rank = {

        "ROUTINE_MONITORING": 1,
        "MONITOR": 2,
        "INCREASED_ATTENTION": 3,
        "REVIEW_REQUIRED": 4,
        "OFFICER_REVIEW": 5
    }


    highest_attention = None
    highest_rank = -1

    for level in attention_levels:

        rank = attention_rank.get(
            level,
            0
        )

        if rank > highest_rank:

            highest_rank = rank
            highest_attention = level


    # ========================================================
    # 4. TREATMENT HANDOFF
    # ========================================================

    treatment_handoff = {

        "knowledge_base_version":
            "MASTER_TREATMENT_KNOWLEDGE_BASE_V2",

        "class_name":
            class_name,

        "workflow":
            (
                "Detection → Safe immediate actions → "
                "Extension Officer review → Treatment / "
                "Monitoring → Reassessment"
            ),

        "farmer_safe_actions_available":
            True,

        "chemical_recommendations_visible_to_farmer":
            False,

        "chemical_use_requires_extension_officer_approval":
            True,

        "chemical_use_requires_current_indian_regulatory_verification":
            True,

        "farm_visit_supported":
            True,

        "laboratory_referral_supported":
            True
    }


    # ========================================================
    # 5. SCIENTIFIC SAFETY SUMMARY
    # ========================================================

    safety_summary = {

        "forecast_is_calibrated_probability":
            False,

        "impact_is_calibrated_yield_loss_model":
            False,

        "weather_directly_used_for_crop_loss":
            False,

        "quantitative_farmer_loss_enabled":
            False,

        "quantitative_yield_preserved_enabled":
            False,

        "leaf_wetness_directly_measured":
            False,

        "important_note":
            (
                "AgroSmart separates environmental disease "
                "suitability from field-impact assessment. "
                "Weather is used for epidemiological forecasting "
                "but is not converted directly into crop-loss percentage."
            )
    }


    # ========================================================
    # 6. MODEL 2 RESPONSE
    # ========================================================

    response = {

        "response_schema_version":
            "AGROSMART_MODEL2_RESPONSE_V1",

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "class_name":
            class_name,

        "crop":
            class_name.split(
                "__",
                1
            )[0],

        "current_case":
            bool(
                current_case
            ),


        # ----------------------------------------------------
        # Forecast
        # ----------------------------------------------------

        "epidemiological_forecast": {

            "forecast_horizon_days":
                len(
                    forecast_records
                ),

            "highest_attention_level":
                highest_attention,

            "daily_records":
                forecast_records
        },


        # ----------------------------------------------------
        # Impact
        # ----------------------------------------------------

        "field_impact_assessment":
            impact_result,


        # ----------------------------------------------------
        # Treatment KB
        # ----------------------------------------------------

        "treatment_handoff":
            treatment_handoff,


        # ----------------------------------------------------
        # Safety
        # ----------------------------------------------------

        "scientific_safety":
            safety_summary
    }


    return response

