# AgroSmart Model 2 — Forecast Standardization

def standardize_forecast_day(
    class_name,
    day_record,
    farmer_interpretation=None
):

    crop = get_crop_from_class(class_name)

    metadata = R12_PILOT_METADATA.get(
        crop,
        {}
    )

    result = day_record.get(
        "result",
        {}
    )

    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    temperature_mean = first_available(
        day_record,
        [
            "temperature_mean_c",
            "temp_mean_c"
        ]
    )

    temperature_min = first_available(
        day_record,
        [
            "temperature_min_c",
            "temp_min_c"
        ]
    )

    temperature_max = first_available(
        day_record,
        [
            "temperature_max_c",
            "temp_max_c"
        ]
    )

    humidity_mean = first_available(
        day_record,
        [
            "humidity_mean_percent",
            "relative_humidity_percent",
            "rh_mean_percent"
        ]
    )

    humidity_min = first_available(
        day_record,
        [
            "humidity_min_percent",
            "relative_humidity_min_percent"
        ]
    )

    humidity_max = first_available(
        day_record,
        [
            "humidity_max_percent",
            "relative_humidity_max_percent"
        ]
    )

    rainfall = first_available(
        day_record,
        [
            "rainfall_mm",
            "rain_mm"
        ]
    )

    sunshine = first_available(
        day_record,
        [
            "sunshine_hours"
        ]
    )

    leaf_wetness = first_available(
        day_record,
        [
            "leaf_wetness_hours"
        ]
    )


    # --------------------------------------------------------
    # FARMER INTERPRETATION
    # --------------------------------------------------------

    if farmer_interpretation is None:

        farmer_interpretation = (
            build_farmer_interpretation(
                result
            )
        )


    # --------------------------------------------------------
    # SCIENTIFIC TRACEABILITY
    # --------------------------------------------------------

    source_ids = first_available(
        result,
        [
            "source_ids",
            "sources"
        ],
        []
    )

    if source_ids is None:
        source_ids = []

    if isinstance(source_ids, str):
        source_ids = [source_ids]


    drivers = first_available(
        result,
        [
            "drivers",
            "environmental_drivers",
            "supporting_factors"
        ],
        []
    )

    if drivers is None:
        drivers = []

    if isinstance(drivers, str):
        drivers = [drivers]


    limitations = first_available(
        result,
        [
            "limitations",
            "limitation",
            "important_note",
            "note"
        ],
        []
    )

    if limitations is None:
        limitations = []

    if isinstance(limitations, str):
        limitations = [limitations]


    # --------------------------------------------------------
    # STANDARD OUTPUT
    # --------------------------------------------------------

    standardized = {

        "schema_version":
            "MODEL2_FORECAST_SCHEMA_V1",

        "date":
            day_record.get("date"),

        "crop":
            crop,

        "class_name":
            class_name,

        "location": {

            "location_key":
                metadata.get(
                    "location_key"
                ),

            "name":
                metadata.get(
                    "location_name"
                )
        },

        "weather": {

            "temperature_c": {
                "min": temperature_min,
                "max": temperature_max,
                "mean": temperature_mean
            },

            "relative_humidity_percent": {
                "min": humidity_min,
                "max": humidity_max,
                "mean": humidity_mean
            },

            "rainfall_mm":
                rainfall,

            "sunshine_hours":
                sunshine,

            "leaf_wetness_hours":
                leaf_wetness,

            "leaf_wetness_source":
                (
                    "DIRECT"
                    if leaf_wetness is not None
                    else "NOT_DIRECTLY_AVAILABLE"
                )
        },

        "epidemiological_assessment": {

            "environmental_suitability":
                result.get(
                    "environmental_suitability"
                ),

            "epidemiological_method":
                result.get(
                    "epidemiological_method"
                ),

            "evidence_mode":
                result.get(
                    "evidence_mode"
                ),

            "evidence_strength":
                result.get(
                    "evidence_strength"
                ),

            "case_priority":
                result.get(
                    "case_priority"
                ),

            "drivers":
                drivers,

            "calibrated_probability":
                bool(
                    result.get(
                        "calibrated_probability",
                        False
                    )
                )
        },

        "farmer_interpretation": {

            "ui_label":
                farmer_interpretation.get(
                    "ui_label"
                ),

            "short_label":
                farmer_interpretation.get(
                    "short_label"
                ),

            "headline":
                farmer_interpretation.get(
                    "headline"
                ),

            "attention_level":
                farmer_interpretation.get(
                    "attention_level"
                ),

            "technical_status":
                farmer_interpretation.get(
                    "technical_status"
                )
        },

        "scientific_traceability": {

            "source_ids":
                source_ids,

            "limitations":
                limitations,

            "calibrated_probability":
                False
        }
    }

    return standardized


def standardize_crop_timeline(
    class_name,
    timeline
):

    output = []

    for day in timeline:

        output.append(

            standardize_forecast_day(
                class_name=class_name,
                day_record=day
            )
        )

    return output


