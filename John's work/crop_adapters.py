# AgroSmart Model 2 — Crop Daily Adapters

from .epidemiological_core import evaluate_epidemiological_risk

def evaluate_grape_day(
    class_name,
    weather_day,
    current_case=False
):

    temp_mean = weather_day[
        "temperature"
    ]["mean_c"]

    humidity = weather_day[
        "relative_humidity_percent"
    ]

    rainfall = weather_day[
        "rainfall_mm"
    ]

    leaf_wetness = weather_day[
        "leaf_wetness_hours"
    ]


    # --------------------------------------------------------
    # GRAPE BACTERIAL LEAF SPOT
    # --------------------------------------------------------

    if class_name == "grape__bacterial_leaf_spot":

        return evaluate_epidemiological_risk(

            class_name,

            temperature_c=temp_mean,

            humidity_percent=humidity,

            rainfall_mm=rainfall,

            current_case=current_case
        )


    # --------------------------------------------------------
    # GRAPE DOWNY MILDEW
    # --------------------------------------------------------

    elif class_name == "grape__downy_mildew":

        return evaluate_epidemiological_risk(

            class_name,

            temperature_c=temp_mean,

            humidity_percent=humidity,

            rainfall_mm=rainfall,

            leaf_wetness_hours=leaf_wetness,

            current_case=current_case
        )


    # --------------------------------------------------------
    # GRAPE POWDERY MILDEW
    # --------------------------------------------------------

    elif class_name == "grape__powdery_mildew":

        return evaluate_epidemiological_risk(

            class_name,

            temperature_c=temp_mean,

            humidity_percent=humidity,

            rainfall_mm=rainfall,

            current_case=current_case
        )


    else:

        raise ValueError(
            f"R11A supports grape disease classes only. "
            f"Received: {class_name}"
        )


def evaluate_onion_day(
    class_name,
    weather_day,
    current_case=True
):

    temp_mean = weather_day[
        "temperature"
    ]["mean_c"]

    temp_min = weather_day[
        "temperature"
    ]["min_c"]

    temp_max = weather_day[
        "temperature"
    ]["max_c"]

    rh_mean = weather_day[
        "relative_humidity_percent"
    ]

    rh_min = weather_day[
        "relative_humidity_min_percent"
    ]

    rh_max = weather_day[
        "relative_humidity_max_percent"
    ]

    rainfall = weather_day[
        "rainfall_mm"
    ]


    # --------------------------------------------------------
    # PURPLE BLOTCH
    # --------------------------------------------------------

    if class_name == "onion__purple_blotch":

        return evaluate_epidemiological_risk(

            class_name,

            temperature_c=temp_mean,

            humidity_percent=rh_mean,

            rainfall_mm=rainfall,

            current_case=current_case
        )


    # --------------------------------------------------------
    # STEMPHYLIUM LEAF BLIGHT
    # --------------------------------------------------------

    elif class_name == "onion__stemphylium_leaf_blight":

        result = evaluate_epidemiological_risk(

            class_name,

            max_temp_c=temp_max,

            min_temp_c=temp_min,

            max_rh_percent=rh_max,

            min_rh_percent=rh_min,

            current_case=current_case
        )


        # ----------------------------------------------------
        # Forecast-layer metadata normalization
        # ----------------------------------------------------

        result["evidence_mode"] = (
            "PUBLISHED_MODEL_PLUS_RULES"
        )

        result["evidence_strength"] = (
            "VERY_STRONG_NASHIK_FIELD_EVIDENCE"
        )


        # Preserve a standardized alias for technical displays.
        # Do NOT interpret this as probability.
        if (
            "published_regression_output_raw"
            in result
        ):

            result["raw_disease_pressure"] = (
                result[
                    "published_regression_output_raw"
                ]
            )


        result["regression_interpretation"] = (
            "RAW_PUBLISHED_DISEASE_PRESSURE_CONTEXT_ONLY"
        )

        result["temporal_aggregation_note"] = (
            "The published regression is retained for "
            "scientific traceability. Application to individual "
            "forecast-day extrema is provisional until the "
            "original study's meteorological aggregation period "
            "is verified."
        )

        result["calibrated_probability"] = False

        return result


    else:

        raise ValueError(
            f"Unsupported onion class: {class_name}"
        )


def evaluate_cotton_day(
    class_name,
    weather_day,
    current_case=True
):

    temp_mean = (
        weather_day[
            "temperature"
        ]["mean_c"]
    )

    temp_min = (
        weather_day[
            "temperature"
        ]["min_c"]
    )

    temp_max = (
        weather_day[
            "temperature"
        ]["max_c"]
    )

    rh_mean = (
        weather_day[
            "relative_humidity_percent"
        ]
    )

    rainfall = (
        weather_day[
            "rainfall_mm"
        ]
    )


    # --------------------------------------------------------
    # ALTERNARIA LEAF SPOT
    # --------------------------------------------------------

    if class_name == "cotton__alternaria_leaf_spot":

        result = evaluate_epidemiological_risk(

            class_name,

            temperature_c=temp_mean,

            humidity_percent=rh_mean,

            rainfall_mm=rainfall,

            current_case=current_case
        )

        result["evidence_mode"] = (
            "KNOWLEDGE_RULES"
        )

        result["evidence_strength"] = (
            "SUPPORTED_FIELD_AND_EXTENSION_EVIDENCE"
        )

        result["calibrated_probability"] = False

        return result


    # --------------------------------------------------------
    # BACTERIAL BLIGHT
    # --------------------------------------------------------

    elif class_name == "cotton__bacterial_blight":

        return evaluate_epidemiological_risk(

            class_name,

            temperature_c=temp_mean,

            humidity_percent=rh_mean,

            rainfall_mm=rainfall,

            historical_or_recent_incidence=None,

            current_case=current_case
        )


    # --------------------------------------------------------
    # BOLLWORM — SPECIES GATE
    # --------------------------------------------------------

    elif class_name == "cotton__bollworm":

        return evaluate_epidemiological_risk(

            class_name,

            min_temp_c=temp_min,

            max_temp_c=temp_max,

            morning_rh_percent=None,

            sunshine_hours=weather_day.get(
                "sunshine_hours"
            ),

            weekly_rainfall_mm=None,

            species_confirmed=False,

            confirmed_species=None,

            current_case=current_case
        )


    else:

        raise ValueError(
            f"Unsupported cotton class: {class_name}"
        )


def evaluate_tomato_day(
    class_name,
    weather_day,
    current_case=True
):

    temp_mean = (
        weather_day[
            "temperature"
        ]["mean_c"]
    )

    rh_mean = (
        weather_day[
            "relative_humidity_percent"
        ]
    )

    rainfall = (
        weather_day[
            "rainfall_mm"
        ]
    )

    leaf_wetness = (
        weather_day.get(
            "leaf_wetness_hours"
        )
    )


    # --------------------------------------------------------
    # EARLY BLIGHT
    # --------------------------------------------------------

    if class_name == "tomato__early_blight":

        result = evaluate_epidemiological_risk(

            class_name,

            temperature_c=temp_mean,

            humidity_percent=rh_mean,

            rainfall_mm=rainfall,

            leaf_wetness_hours=leaf_wetness,

            current_case=current_case
        )

        result["calibrated_probability"] = False

        return result


    # --------------------------------------------------------
    # LATE BLIGHT
    # --------------------------------------------------------

    elif class_name == "tomato__late_blight":

        result = evaluate_epidemiological_risk(

            class_name,

            temperature_c=temp_mean,

            humidity_percent=rh_mean,

            rainfall_mm=rainfall,

            leaf_wetness_hours=leaf_wetness,

            current_case=current_case
        )

        result["calibrated_probability"] = False

        return result


    # --------------------------------------------------------
    # LEAF MOLD
    # --------------------------------------------------------

    elif class_name == "tomato__leaf_mold":

        result = evaluate_epidemiological_risk(

            class_name,

            temperature_c=temp_mean,

            humidity_percent=rh_mean,

            current_case=current_case,

            protected_cultivation=None
        )

        result["evidence_mode"] = (
            "KNOWLEDGE_RULES"
        )

        result["evidence_strength"] = (
            "SUPPORTED_EXTENSION_AND_UNIVERSITY_EVIDENCE"
        )

        result["protected_cultivation_context"] = (
            "UNKNOWN"
        )

        result["calibrated_probability"] = False

        return result


    else:

        raise ValueError(
            f"Unsupported tomato class: {class_name}"
        )


