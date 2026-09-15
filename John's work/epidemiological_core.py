# AgroSmart Model 2 — Epidemiological Core
# Recovered from validated live runtime.

def at_least(value, threshold):
    if value is None:
        return None
    return value >= threshold


def case_flag(current_case):
    return (
        "ACTIVE_CONFIRMED_CASE"
        if current_case
        else "NO_ACTIVE_CASE_FLAG"
    )


def in_range(value, low, high):
    if value is None:
        return None
    return low <= value <= high


def evaluate_grape_bacterial_leaf_spot(
    temperature_c,
    humidity_percent,
    rainfall_mm=None,
    current_case=False
):

    temp_match = (
        25 <= temperature_c <= 30
    )

    humidity_match = (
        80 <= humidity_percent <= 90
    )

    if temp_match and humidity_match:
        suitability = "FAVORABLE"

    elif temp_match or humidity_match:
        suitability = "PARTIALLY_FAVORABLE"

    else:
        suitability = "NOT_FAVORABLE_BY_QUANTIFIED_RULES"


    drivers = []

    if temp_match:
        drivers.append(
            "Temperature is within the reported favorable "
            "range of 25–30°C."
        )

    if humidity_match:
        drivers.append(
            "Relative humidity is within the reported "
            "favorable range of 80–90%."
        )

    if rainfall_mm is not None and rainfall_mm > 0:
        drivers.append(
            "Rainfall/wet conditions may provide additional "
            "moisture support; no fixed rainfall threshold "
            "is currently used."
        )


    return {

        "class_name":
            "grape__bacterial_leaf_spot",

        "evidence_mode":
            "QUANTITATIVE_RULE",

        "epidemiological_method":
            "DISEASE_SPECIFIC_ENVIRONMENTAL_RULES",

        "environmental_suitability":
            suitability,

        "quantified_conditions": {
            "temperature_match":
                temp_match,

            "humidity_match":
                humidity_match
        },

        "supporting_conditions": {
            "rainfall_mm":
                rainfall_mm
        },

        "drivers":
            drivers,

        "case_priority":
            (
                "ACTIVE_CONFIRMED_CASE"
                if current_case
                else
                "NO_ACTIVE_CASE_FLAG"
            ),

        "calibrated_probability":
            False,

        "note":
            "Output represents environmental suitability, "
            "not probability of infection."
    }


def evaluate_grape_downy_mildew(
    temperature_c=None,
    humidity_percent=None,
    rainfall_mm=None,
    leaf_wetness_hours=None,
    current_case=False
):

    drivers = []
    missing = []

    # Published model fundamentally depends on
    # temperature DURING leaf wetness + wetness duration.
    #
    # We currently do NOT freeze a fabricated universal
    # temperature/wetness cutoff.

    if leaf_wetness_hours is not None:
        drivers.append(
            f"Observed/estimated leaf wetness duration: "
            f"{leaf_wetness_hours} h."
        )
    else:
        missing.append(
            "Direct leaf-wetness duration is unavailable."
        )

    if temperature_c is not None:
        drivers.append(
            f"Temperature during the assessment period: "
            f"{temperature_c}°C."
        )

    if rainfall_mm is not None and rainfall_mm > 0:
        drivers.append(
            "Rainfall indicates wet conditions that may support "
            "downy-mildew infection."
        )

    if humidity_percent is not None:
        drivers.append(
            f"Relative humidity observed: {humidity_percent}%."
        )

    # --------------------------------------------------------
    # Interpretation
    # --------------------------------------------------------

    if (
        leaf_wetness_hours is not None
        and temperature_c is not None
    ):
        suitability = (
            "PUBLISHED_MODEL_INPUTS_AVAILABLE_"
            "TABLE_OR_CALIBRATION_REQUIRED"
        )

        evidence_mode = "QUANTITATIVE_RULE"

    elif (
        rainfall_mm is not None
        or humidity_percent is not None
    ):
        suitability = (
            "WETNESS_PROXY_AVAILABLE_"
            "DIRECT_MODEL_NOT_EXECUTED"
        )

        evidence_mode = "PARTIAL_RULE_WITH_PROXY"

    else:
        suitability = "INSUFFICIENT_ENVIRONMENTAL_DATA"
        evidence_mode = "INSUFFICIENT_FOR_NUMERIC_MODEL"

    return {
        "class_name": "grape__downy_mildew",

        "evidence_mode": evidence_mode,

        "epidemiological_method":
            "LEAF_WETNESS_TEMPERATURE_MODEL_WITH_PROXY_SUPPORT",

        "environmental_suitability":
            suitability,

        "inputs": {
            "temperature_c": temperature_c,
            "humidity_percent": humidity_percent,
            "rainfall_mm": rainfall_mm,
            "leaf_wetness_hours": leaf_wetness_hours
        },

        "case_priority": case_flag(current_case),

        "drivers": drivers,

        "missing_or_uncertain": missing,

        "calibrated_probability": False,

        "important_note":
            "Published grape downy-mildew models depend strongly on "
            "leaf-wetness duration and temperature during the wet period. "
            "Rainfall/RH may be used only as proxies when measured "
            "leaf wetness is unavailable."
    }


def evaluate_grape_powdery_mildew(
    temperature_c=None,
    humidity_percent=None,
    rainfall_mm=None,
    current_case=False
):

    drivers = []

    if temperature_c is not None:
        drivers.append(
            f"Temperature observed: {temperature_c}°C."
        )

    if humidity_percent is not None:
        drivers.append(
            f"Relative humidity observed: {humidity_percent}%."
        )

    if rainfall_mm is not None:
        drivers.append(
            f"Rainfall observed: {rainfall_mm} mm. "
            "Rainfall is not interpreted using the same logic "
            "as downy mildew."
        )

    # We deliberately avoid freezing an unsupported universal
    # temperature/RH interval at this stage.

    if temperature_c is not None and humidity_percent is not None:
        suitability = (
            "ENVIRONMENTAL_FACTORS_AVAILABLE_"
            "DISEASE_SPECIFIC_THRESHOLD_NOT_FROZEN"
        )

        evidence_mode = "PARTIAL_RULE_WITH_PROXY"

    else:
        suitability = "INSUFFICIENT_FOR_NUMERIC_CLASSIFICATION"
        evidence_mode = "INSUFFICIENT_FOR_NUMERIC_MODEL"

    return {
        "class_name": "grape__powdery_mildew",

        "evidence_mode": evidence_mode,

        "epidemiological_method":
            "EVIDENCE_SUPPORTED_QUALITATIVE_RULES",

        "environmental_suitability":
            suitability,

        "inputs": {
            "temperature_c": temperature_c,
            "humidity_percent": humidity_percent,
            "rainfall_mm": rainfall_mm
        },

        "case_priority": case_flag(current_case),

        "drivers": drivers,

        "calibrated_probability": False,

        "important_note":
            "The earlier grape ML dataset is not used for deployment "
            "because seasonality dominated the learned predictions. "
            "This evaluator therefore uses epidemiological evidence only."
    }


def evaluate_onion_purple_blotch(
    temperature_c,
    humidity_percent,
    rainfall_mm=None,
    current_case=False
):

    temp_match = in_range(
        temperature_c,
        20,
        25
    )

    rh_match = at_least(
        humidity_percent,
        75
    )

    if temp_match and rh_match:
        suitability = "FAVORABLE"
    elif temp_match or rh_match:
        suitability = "PARTIALLY_FAVORABLE"
    else:
        suitability = "NOT_FAVORABLE_BY_QUANTIFIED_RULES"

    drivers = []

    if temp_match:
        drivers.append(
            "Temperature is within the reported favorable "
            "range of approximately 20–25°C."
        )

    if rh_match:
        drivers.append(
            "Relative humidity is above the reported favorable "
            "level of approximately 75%."
        )

    if rainfall_mm is not None and rainfall_mm > 0:
        drivers.append(
            "Rainfall/wet conditions provide additional moisture support; "
            "no universal rainfall threshold is applied."
        )

    return {
        "class_name": "onion__purple_blotch",

        "evidence_mode": "QUANTITATIVE_RULE",

        "epidemiological_method":
            "INDIAN_FIELD_ENVIRONMENTAL_RULES",

        "environmental_suitability":
            suitability,

        "quantified_conditions": {
            "temperature_c": temperature_c,
            "temperature_range_c": [20, 25],
            "temperature_match": temp_match,

            "humidity_percent": humidity_percent,
            "humidity_threshold_percent": 75,
            "humidity_match": rh_match
        },

        "supporting_conditions": {
            "rainfall_mm": rainfall_mm
        },

        "case_priority": case_flag(current_case),

        "calibrated_probability": False,

        "important_note":
            "Favorable conditions represent environmental suitability, "
            "not probability of disease."
    }


def evaluate_onion_stemphylium(
    max_temp_c,
    min_temp_c,
    max_rh_percent,
    min_rh_percent,
    current_case=False
):

    # --------------------------------------------------------
    # Published Nashik regression:
    #
    # Y = -103.908
    #     + 0.0953*X1
    #     + 5.085*X2
    #     + 0.902*X3
    #     - 0.971*X4
    #
    # X1 = maximum temperature
    # X2 = minimum temperature
    # X3 = maximum RH
    # X4 = minimum RH
    #
    # IMPORTANT:
    # We retain RAW published-equation output.
    # We do NOT convert it into probability.
    # --------------------------------------------------------

    y_raw = (
        -103.908
        + 0.0953 * max_temp_c
        + 5.085 * min_temp_c
        + 0.902 * max_rh_percent
        - 0.971 * min_rh_percent
    )

    favorable_mean_temp = (
        16.25 <= ((max_temp_c + min_temp_c) / 2) <= 22.5
    )

    favorable_high_rh = (
        85 <= max_rh_percent <= 90
    )

    if favorable_mean_temp and favorable_high_rh:
        suitability = "FAVORABLE"
    elif favorable_mean_temp or favorable_high_rh:
        suitability = "PARTIALLY_FAVORABLE"
    else:
        suitability = "NOT_FAVORABLE_BY_REPORTED_RANGE"

    return {
        "class_name":
            "onion__stemphylium_leaf_blight",

        "epidemiological_method":
            "PUBLISHED_NASHIK_REGRESSION_PLUS_RULES",

        "environmental_suitability":
            suitability,

        "published_regression_output_raw":
            round(y_raw, 4),

        "regression_equation":
            "Y = -103.908 + 0.0953*X1 + 5.085*X2 + "
            "0.902*X3 - 0.971*X4",

        "inputs": {
            "X1_max_temp_c": max_temp_c,
            "X2_min_temp_c": min_temp_c,
            "X3_max_rh_percent": max_rh_percent,
            "X4_min_rh_percent": min_rh_percent
        },

        "reported_environmental_checks": {
            "mean_temperature_c":
                round((max_temp_c + min_temp_c) / 2, 2),

            "reported_favorable_mean_temp":
                favorable_mean_temp,

            "reported_favorable_high_rh":
                favorable_high_rh
        },

        "case_priority":
            "ACTIVE_CONFIRMED_CASE"
            if current_case
            else "NO_ACTIVE_CASE_FLAG",

        "calibrated_probability":
            False,

        "important_note":
            "Regression output is retained in the published study's "
            "disease-pressure/severity context. It is NOT interpreted "
            "as probability and is not clipped into 0–100 risk."
    }


def evaluate_cotton_alternaria(
    temperature_c,
    humidity_percent=None,
    rainfall_mm=None,
    current_case=False
):

    temp_match = in_range(
        temperature_c,
        25,
        28
    )

    qualitative_support = []

    if humidity_percent is not None:
        qualitative_support.append({
            "factor": "relative_humidity",
            "observed": humidity_percent,
            "interpretation":
                "High humidity is reported as favorable, but no defensible "
                "numeric threshold is currently frozen."
        })

    if rainfall_mm is not None:
        qualitative_support.append({
            "factor": "rainfall",
            "observed": rainfall_mm,
            "interpretation":
                "Intermittent rainfall is reported as favorable, but no "
                "universal numeric rainfall threshold is currently frozen."
        })

    if temp_match:
        suitability = "TEMPERATURE_FAVORABLE_QUALITATIVE_SUPPORT_REQUIRED"
    else:
        suitability = "TEMPERATURE_NOT_IN_REPORTED_FAVORABLE_RANGE"

    return {
        "class_name":
            "cotton__alternaria_leaf_spot",

        "epidemiological_method":
            "PARTIALLY_QUANTIFIED_DISEASE_RULES",

        "environmental_suitability":
            suitability,

        "quantified_conditions": {
            "temperature_c": temperature_c,
            "reported_range_c": [25, 28],
            "temperature_match": temp_match
        },

        "qualitative_support":
            qualitative_support,

        "case_priority":
            "ACTIVE_CONFIRMED_CASE"
            if current_case
            else "NO_ACTIVE_CASE_FLAG",

        "calibrated_probability":
            False,

        "important_note":
            "Temperature can be tested quantitatively, but humidity and "
            "rainfall remain qualitative until disease-specific numerical "
            "threshold evidence is established."
    }


def evaluate_cotton_bacterial_blight(
    temperature_c=None,
    humidity_percent=None,
    rainfall_mm=None,
    historical_or_recent_incidence=None,
    current_case=False
):

    drivers = []
    missing = []

    if temperature_c is not None:
        drivers.append(
            f"Temperature observed: {temperature_c}°C."
        )

    if humidity_percent is not None:
        drivers.append(
            f"Relative humidity observed: {humidity_percent}%."
        )

    if rainfall_mm is not None:
        drivers.append(
            f"Rainfall observed: {rainfall_mm} mm."
        )

    if historical_or_recent_incidence is not None:

        drivers.append(
            "Recent/historical bacterial-blight incidence "
            "information is available."
        )

    else:
        missing.append(
            "Historical/recent disease-incidence information is unavailable."
        )

    # Published Indian evidence exists, but raw model coefficients
    # / full deployment equation are not available to us.

    if historical_or_recent_incidence is not None:
        suitability = (
            "PUBLISHED_PREDICTORS_AVAILABLE_"
            "MODEL_NOT_DIRECTLY_REPRODUCIBLE"
        )

        evidence_mode = "PARTIAL_RULE_WITH_PROXY"

    else:
        suitability = (
            "WEATHER_CONTEXT_ONLY_"
            "INCIDENCE_HISTORY_MISSING"
        )

        evidence_mode = "INSUFFICIENT_FOR_NUMERIC_MODEL"

    return {
        "class_name": "cotton__bacterial_blight",

        "evidence_mode": evidence_mode,

        "epidemiological_method":
            "INDIAN_PUBLISHED_MODEL_EVIDENCE_NOT_DIRECTLY_REPRODUCIBLE",

        "environmental_suitability":
            suitability,

        "inputs": {
            "temperature_c": temperature_c,
            "humidity_percent": humidity_percent,
            "rainfall_mm": rainfall_mm,
            "historical_or_recent_incidence":
                historical_or_recent_incidence
        },

        "case_priority": case_flag(current_case),

        "drivers": drivers,

        "missing_or_uncertain": missing,

        "calibrated_probability": False,

        "important_note":
            "The published Indian bacterial-blight study supports "
            "weather-plus-incidence forecasting, but a local calibrated "
            "prediction is not generated without the original fitted model."
    }


def evaluate_cotton_bollworm(
    min_temp_c=None,
    max_temp_c=None,
    morning_rh_percent=None,
    sunshine_hours=None,
    weekly_rainfall_mm=None,
    species_confirmed=None,
    confirmed_species=None,
    current_case=False
):

    drivers = []
    matches = {}

    # ========================================================
    # CRITICAL SPECIES SAFETY GATE
    # ========================================================

    spotted_confirmed = (
        species_confirmed is True
        and confirmed_species is not None
        and (
            "earias" in confirmed_species.lower()
            or "spotted" in confirmed_species.lower()
        )
    )

    if not spotted_confirmed:

        return {
            "class_name": "cotton__bollworm",

            "evidence_mode":
                "INSUFFICIENT_FOR_SPECIES_SPECIFIC_MODEL",

            "epidemiological_method":
                "SPECIES_CONFIRMATION_GATE",

            "environmental_suitability":
                "BOLLWORM_DETECTED_SPECIES_CONFIRMATION_REQUIRED",

            "case_priority": case_flag(current_case),

            "species_confirmed": species_confirmed,
            "confirmed_species": confirmed_species,

            "calibrated_probability": False,

            "important_note":
                "Model 1 detects generic cotton bollworm. The available "
                "meteorological regression concerns spotted bollworm "
                "(Earias spp.). Species-specific forecasting must not be "
                "applied until an Extension Officer/expert confirms species."
        }


    # ========================================================
    # SPOTTED BOLLWORM — SUPPORTING HISTORICAL CONDITIONS
    # ========================================================

    if min_temp_c is not None:
        match = in_range(
            min_temp_c,
            19,
            20
        )

        matches["min_temperature"] = match

        if match:
            drivers.append(
                "Minimum temperature is within the approximately "
                "19–20°C range associated with high infestation "
                "in the historical study."
            )


    if max_temp_c is not None:
        match = in_range(
            max_temp_c,
            30,
            32
        )

        matches["max_temperature"] = match

        if match:
            drivers.append(
                "Maximum temperature is within the approximately "
                "30–32°C range reported during high infestation."
            )


    if morning_rh_percent is not None:
        match = in_range(
            morning_rh_percent,
            95,
            100
        )

        matches["morning_rh"] = match

        if match:
            drivers.append(
                "Morning RH is within the approximately 95–100% "
                "range reported during high infestation."
            )


    if sunshine_hours is not None:
        match = in_range(
            sunshine_hours,
            5,
            7
        )

        matches["sunshine"] = match

        if match:
            drivers.append(
                "Bright sunshine duration is within the approximately "
                "5–7 h range reported during high infestation."
            )


    if weekly_rainfall_mm is not None:
        match = in_range(
            weekly_rainfall_mm,
            170,
            210
        )

        matches["weekly_rainfall"] = match

        if match:
            drivers.append(
                "Weekly rainfall is within the approximately "
                "170–210 mm range reported during high infestation."
            )


    true_count = sum(
        1 for value in matches.values()
        if value is True
    )

    evaluated_count = len(matches)


    if evaluated_count == 0:
        suitability = "INSUFFICIENT_METEOROLOGICAL_DATA"

    elif true_count == evaluated_count:
        suitability = (
            "CONDITIONS_RESEMBLE_REPORTED_HIGH_INFESTATION_PERIOD"
        )

    elif true_count > 0:
        suitability = (
            "SOME_REPORTED_HIGH_INFESTATION_CONDITIONS_MATCHED"
        )

    else:
        suitability = (
            "REPORTED_HIGH_INFESTATION_RANGES_NOT_MATCHED"
        )


    return {
        "class_name": "cotton__bollworm",

        "evidence_mode": "PARTIAL_RULE_WITH_PROXY",

        "epidemiological_method":
            "SPOTTED_BOLLWORM_HISTORICAL_METEOROLOGICAL_RELATIONSHIP",

        "environmental_suitability":
            suitability,

        "species_confirmed": True,

        "confirmed_species":
            confirmed_species,

        "reported_condition_matches":
            matches,

        "drivers":
            drivers,

        "case_priority":
            case_flag(current_case),

        "calibrated_probability":
            False,

        "important_note":
            "These ranges originate from historical spotted-bollworm "
            "observations. The published regression uses variables from "
            "specific standard weeks and must not be executed as a generic "
            "daily regression."
    }


def evaluate_tomato_early_blight(
    temperature_c=None,
    humidity_percent=None,
    rainfall_mm=None,
    leaf_wetness_hours=None,
    current_case=False
):

    drivers = []
    matches = {}

    # RH >= 90 is one currently frozen quantitative element.
    if humidity_percent is not None:

        rh_match = at_least(
            humidity_percent,
            90
        )

        matches["high_humidity"] = rh_match

        if rh_match:
            drivers.append(
                "Relative humidity is >=90%, supporting prolonged "
                "moisture conditions used in FAST-style disease models."
            )


    if rainfall_mm is not None and rainfall_mm > 0:
        drivers.append(
            "Rainfall contributes to moisture/wetness conditions."
        )


    if leaf_wetness_hours is not None:
        drivers.append(
            f"Leaf-wetness duration available: "
            f"{leaf_wetness_hours} h."
        )


    if temperature_c is not None:
        drivers.append(
            f"Temperature available for infection-period "
            f"interpretation: {temperature_c}°C."
        )


    # FAST requires a temperature/wetness relationship.
    # We are NOT inventing DSV values here.

    if (
        temperature_c is not None
        and leaf_wetness_hours is not None
    ):

        suitability = (
            "FAST_INPUTS_AVAILABLE_"
            "DSV_TABLE_NOT_YET_EXECUTED"
        )

        evidence_mode = "QUANTITATIVE_RULE"

    elif (
        humidity_percent is not None
        or rainfall_mm is not None
    ):

        suitability = (
            "MOISTURE_PROXY_AVAILABLE_"
            "FULL_FAST_MODEL_NOT_EXECUTED"
        )

        evidence_mode = "PARTIAL_RULE_WITH_PROXY"

    else:

        suitability = "INSUFFICIENT_FOR_NUMERIC_MODEL"

        evidence_mode = "INSUFFICIENT_FOR_NUMERIC_MODEL"


    return {
        "class_name": "tomato__early_blight",

        "evidence_mode": evidence_mode,

        "epidemiological_method":
            "FAST_STYLE_PLUS_INDIAN_WEATHER_MODEL_EVIDENCE",

        "environmental_suitability":
            suitability,

        "inputs": {
            "temperature_c": temperature_c,
            "humidity_percent": humidity_percent,
            "rainfall_mm": rainfall_mm,
            "leaf_wetness_hours": leaf_wetness_hours
        },

        "quantified_conditions":
            matches,

        "drivers":
            drivers,

        "case_priority":
            case_flag(current_case),

        "calibrated_probability":
            False,

        "important_note":
            "The Indian study provides strong weather-based forecasting "
            "evidence, including Maharashtra data, but the original fitted "
            "SVR/MLR model is not directly reproduced. FAST-style DSV "
            "calculation also requires its published temperature-wetness "
            "relationship."
    }


def evaluate_tomato_late_blight(
    temperature_c=None,
    humidity_percent=None,
    rainfall_mm=None,
    leaf_wetness_hours=None,
    current_case=False
):

    drivers = []
    matches = {}

    if humidity_percent is not None:

        rh_match = at_least(
            humidity_percent,
            90
        )

        matches["high_humidity"] = rh_match

        if rh_match:
            drivers.append(
                "Relative humidity >=90% supports prolonged "
                "late-blight infection conditions."
            )


    if rainfall_mm is not None and rainfall_mm > 0:
        drivers.append(
            "Rainfall indicates additional moisture/wetness support."
        )


    if leaf_wetness_hours is not None:
        drivers.append(
            f"Leaf-wetness duration available: "
            f"{leaf_wetness_hours} h."
        )


    if temperature_c is not None:
        drivers.append(
            f"Temperature available: {temperature_c}°C."
        )


    # IPI-style disease-pressure interpretation depends on
    # combinations of temp/moisture/wetness.
    #
    # We currently do NOT invent a local IPI equation.

    if (
        temperature_c is not None
        and humidity_percent is not None
        and leaf_wetness_hours is not None
    ):

        suitability = (
            "INFECTION_PERIOD_INPUTS_AVAILABLE_"
            "LOCAL_CALIBRATION_REQUIRED"
        )

        evidence_mode = "QUANTITATIVE_RULE"

    elif (
        humidity_percent is not None
        or rainfall_mm is not None
    ):

        suitability = (
            "MOISTURE_PRESSURE_INDICATORS_AVAILABLE_"
            "FULL_MODEL_NOT_EXECUTED"
        )

        evidence_mode = "PARTIAL_RULE_WITH_PROXY"

    else:

        suitability = "INSUFFICIENT_FOR_NUMERIC_MODEL"

        evidence_mode = "INSUFFICIENT_FOR_NUMERIC_MODEL"


    return {
        "class_name": "tomato__late_blight",

        "evidence_mode": evidence_mode,

        "epidemiological_method":
            "LATE_BLIGHT_INFECTION_PERIOD_MODEL",

        "environmental_suitability":
            suitability,

        "inputs": {
            "temperature_c": temperature_c,
            "humidity_percent": humidity_percent,
            "rainfall_mm": rainfall_mm,
            "leaf_wetness_hours": leaf_wetness_hours
        },

        "quantified_conditions":
            matches,

        "drivers":
            drivers,

        "case_priority":
            case_flag(current_case),

        "calibrated_probability":
            False,

        "important_note":
            "The result represents disease-pressure evidence. "
            "It is not a calibrated probability and does not execute "
            "an unverified local IPI equation."
    }


def evaluate_tomato_leaf_mold(
    temperature_c,
    humidity_percent,
    current_case=False,
    protected_cultivation=None
):

    temp_favorable = in_range(
        temperature_c,
        20,
        25
    )

    temp_optimal = in_range(
        temperature_c,
        22,
        24
    )

    rh_favorable = at_least(
        humidity_percent,
        85
    )

    if temp_favorable and rh_favorable:
        if temp_optimal:
            suitability = "HIGHLY_FAVORABLE_ENVIRONMENT"
        else:
            suitability = "FAVORABLE_ENVIRONMENT"

    elif temp_favorable or rh_favorable:
        suitability = "PARTIALLY_FAVORABLE"

    else:
        suitability = "NOT_FAVORABLE_BY_QUANTIFIED_RULES"

    drivers = []

    if temp_optimal:
        drivers.append(
            "Temperature is within the reported optimum range of approximately 22–24°C."
        )
    elif temp_favorable:
        drivers.append(
            "Temperature is within the broader favorable range of approximately 20–25°C."
        )

    if rh_favorable:
        drivers.append(
            "Relative humidity is at or above the reported high-risk level of approximately 85%."
        )

    if protected_cultivation is True:
        drivers.append(
            "Protected cultivation / poor ventilation can further support "
            "persistent high-humidity leaf-mold conditions."
        )

    return {
        "class_name":
            "tomato__leaf_mold",

        "epidemiological_method":
            "DISEASE_SPECIFIC_EXTENSION_RULES",

        "environmental_suitability":
            suitability,

        "quantified_conditions": {
            "temperature_favorable": temp_favorable,
            "temperature_optimal": temp_optimal,
            "humidity_favorable": rh_favorable
        },

        "context": {
            "protected_cultivation": protected_cultivation
        },

        "case_priority":
            "ACTIVE_CONFIRMED_CASE"
            if current_case
            else "NO_ACTIVE_CASE_FLAG",

        "drivers":
            drivers,

        "calibrated_probability":
            False,

        "important_note":
            "Output represents evidence-based environmental suitability "
            "rather than calibrated disease probability."
    }


def evaluate_epidemiological_risk(
    class_name,
    **kwargs
):

    evaluators = {

        # GRAPE
        "grape__bacterial_leaf_spot":
            evaluate_grape_bacterial_leaf_spot,

        "grape__downy_mildew":
            evaluate_grape_downy_mildew,

        "grape__powdery_mildew":
            evaluate_grape_powdery_mildew,


        # ONION
        "onion__purple_blotch":
            evaluate_onion_purple_blotch,

        "onion__stemphylium_leaf_blight":
            evaluate_onion_stemphylium,


        # COTTON
        "cotton__alternaria_leaf_spot":
            evaluate_cotton_alternaria,

        "cotton__bacterial_blight":
            evaluate_cotton_bacterial_blight,

        "cotton__bollworm":
            evaluate_cotton_bollworm,


        # TOMATO
        "tomato__early_blight":
            evaluate_tomato_early_blight,

        "tomato__late_blight":
            evaluate_tomato_late_blight,

        "tomato__leaf_mold":
            evaluate_tomato_leaf_mold
    }


    # ========================================================
    # HEALTHY CLASSES
    # ========================================================

    healthy_classes = {
        "grape__healthy",
        "onion__healthy",
        "cotton__healthy",
        "tomato__healthy"
    }

    if class_name in healthy_classes:

        return {
            "class_name": class_name,

            "evidence_mode": "PREVENTION_ONLY",

            "environmental_suitability":
                "HEALTHY_DETECTION_PREVENTION_MONITORING",

            "case_priority":
                "NO_DISEASE_CASE_FROM_CURRENT_IMAGE",

            "calibrated_probability":
                False,

            "important_note":
                "A healthy image does not guarantee the entire field is "
                "disease-free. Disease-specific environmental pressure "
                "can still be monitored separately."
        }


    if class_name not in evaluators:
        raise ValueError(
            f"No epidemiological evaluator found for {class_name}"
        )


    return evaluators[class_name](**kwargs)


