# AgroSmart Model 2 — Open-Meteo Weather Adapter

def build_standard_weather_day(
    date,
    temp_min_c=None,
    temp_max_c=None,
    temp_day_c=None,
    humidity_percent=None,
    rainfall_mm=0.0,
    precipitation_probability=None,
    wind_speed_mps=None,
    clouds_percent=None,
    weather_description=None
):
    """
    Creates the weather structure consumed by Model 2.

    IMPORTANT:
    - rainfall_mm is actual/forecast rainfall amount.
    - precipitation_probability is NOT rainfall amount.
    - leaf wetness is NOT directly available here.
    - sunshine duration is NOT inferred from cloud cover.
    """

    # --------------------------------------------------------
    # Mean temperature
    # --------------------------------------------------------

    if (
        temp_min_c is not None
        and temp_max_c is not None
    ):
        temp_mean_c = round(
            (temp_min_c + temp_max_c) / 2,
            2
        )

    elif temp_day_c is not None:
        temp_mean_c = temp_day_c

    else:
        temp_mean_c = None


    # --------------------------------------------------------
    # Basic moisture proxy
    #
    # This is NOT leaf-wetness duration.
    # It merely tells later evaluators that wet weather
    # evidence exists.
    # --------------------------------------------------------

    moisture_proxy = False
    moisture_reasons = []

    if rainfall_mm is not None and rainfall_mm > 0:
        moisture_proxy = True

        moisture_reasons.append(
            f"Forecast rainfall: {rainfall_mm} mm"
        )

    if (
        humidity_percent is not None
        and humidity_percent >= 90
    ):
        moisture_proxy = True

        moisture_reasons.append(
            f"High relative humidity: {humidity_percent}%"
        )


    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    return {

        "date": str(date),

        "temperature": {
            "min_c": temp_min_c,
            "max_c": temp_max_c,
            "mean_c": temp_mean_c,
            "day_c": temp_day_c
        },

        "relative_humidity_percent":
            humidity_percent,

        "rainfall_mm":
            rainfall_mm,

        "precipitation_probability":
            precipitation_probability,

        "wind_speed_mps":
            wind_speed_mps,

        "clouds_percent":
            clouds_percent,

        "weather_description":
            weather_description,

        # ----------------------------------------------------
        # Variables NOT directly observed
        # ----------------------------------------------------

        "leaf_wetness_hours":
            None,

        "leaf_wetness_source":
            "NOT_DIRECTLY_AVAILABLE",

        "sunshine_hours":
            None,

        "sunshine_source":
            "NOT_DIRECTLY_AVAILABLE",

        # ----------------------------------------------------
        # Supporting proxy only
        # ----------------------------------------------------

        "moisture_proxy": {
            "available":
                moisture_proxy,

            "reasons":
                moisture_reasons,

            "important_note":
                "This proxy must not be treated as measured "
                "leaf-wetness duration."
        },

        # ----------------------------------------------------
        # Data quality
        # ----------------------------------------------------

        "data_quality": {

            "direct_weather_variables": [
                x for x, value in {
                    "temperature":
                        temp_mean_c,

                    "humidity":
                        humidity_percent,

                    "rainfall":
                        rainfall_mm,

                    "precipitation_probability":
                        precipitation_probability,

                    "wind_speed":
                        wind_speed_mps,

                    "cloud_cover":
                        clouds_percent

                }.items()

                if value is not None
            ],

            "estimated_variables": [],

            "missing_epidemiological_variables": [
                "leaf_wetness_hours",
                "sunshine_hours"
            ]
        }
    }


def fetch_open_meteo_forecast(
    latitude,
    longitude,
    forecast_days=7
):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {

        "latitude": latitude,
        "longitude": longitude,

        # Daily variables
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
            "precipitation_probability_max",
            "rain_sum",
            "wind_speed_10m_max",
            "sunshine_duration"
        ]),

        # Hourly RH is requested because daily RH is not
        # directly supplied as a standard daily variable.
        "hourly": ",".join([
            "relative_humidity_2m",
            "temperature_2m",
            "precipitation",
            "rain",
            "dew_point_2m",
            "cloud_cover"
        ]),

        "timezone": "auto",

        "forecast_days": forecast_days
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    if response.status_code != 200:

        print("HTTP status:", response.status_code)

        try:
            print("API response:", response.json())
        except:
            print("API response:", response.text)

        raise RuntimeError(
            "Open-Meteo API request failed."
        )

    return response.json()


def parse_open_meteo_forecast(
    raw_response
):

    daily = raw_response.get(
        "daily",
        {}
    )

    hourly = raw_response.get(
        "hourly",
        {}
    )

    grouped_hourly = group_hourly_by_date(
        hourly
    )

    dates = daily.get(
        "time",
        []
    )

    standardized_days = []


    for i, date in enumerate(dates):

        hourly_day = grouped_hourly.get(
            date,
            {}
        )


        # ----------------------------------------------------
        # DAILY HUMIDITY
        #
        # We derive daily mean RH from the provider's hourly
        # RH forecast.
        # ----------------------------------------------------

        humidity_values = hourly_day.get(
            "humidity",
            []
        )

        humidity_mean = safe_mean(
            humidity_values
        )


        # ----------------------------------------------------
        # DAILY CLOUD COVER
        # ----------------------------------------------------

        cloud_values = hourly_day.get(
            "cloud_cover",
            []
        )

        cloud_mean = safe_mean(
            cloud_values
        )


        # ----------------------------------------------------
        # SAFE DAILY VALUE RETRIEVAL
        # ----------------------------------------------------

        def daily_value(variable, default=None):

            values = daily.get(
                variable,
                []
            )

            if i < len(values):
                return values[i]

            return default


        # Prefer rain_sum for rain specifically.
        rainfall_mm = daily_value(
            "rain_sum",
            0.0
        )

        if rainfall_mm is None:
            rainfall_mm = 0.0


        # ----------------------------------------------------
        # BUILD OUR EXISTING STANDARD WEATHER OBJECT
        # ----------------------------------------------------

        standard_day = build_standard_weather_day(

            date=date,

            temp_min_c=daily_value(
                "temperature_2m_min"
            ),

            temp_max_c=daily_value(
                "temperature_2m_max"
            ),

            temp_day_c=daily_value(
                "temperature_2m_mean"
            ),

            humidity_percent=humidity_mean,

            rainfall_mm=rainfall_mm,

            precipitation_probability=(
                None
                if daily_value(
                    "precipitation_probability_max"
                ) is None
                else
                daily_value(
                    "precipitation_probability_max"
                ) / 100.0
            ),

            wind_speed_mps=(
                None
                if daily_value(
                    "wind_speed_10m_max"
                ) is None
                else
                round(
                    daily_value(
                        "wind_speed_10m_max"
                    ) / 3.6,
                    2
                )
            ),

            clouds_percent=cloud_mean,

            weather_description=None
        )


        # ----------------------------------------------------
        # OPEN-METEO-SPECIFIC ADDITIONAL VARIABLES
        # ----------------------------------------------------

        sunshine_seconds = daily_value(
            "sunshine_duration"
        )

        if sunshine_seconds is not None:

            sunshine_hours = round(
                sunshine_seconds / 3600,
                2
            )

            standard_day[
                "sunshine_hours"
            ] = sunshine_hours

            standard_day[
                "sunshine_source"
            ] = "OPEN_METEO_FORECAST"

            # Remove sunshine from missing list
            missing = standard_day[
                "data_quality"
            ][
                "missing_epidemiological_variables"
            ]

            if "sunshine_hours" in missing:
                missing.remove(
                    "sunshine_hours"
                )

            standard_day[
                "data_quality"
            ][
                "direct_weather_variables"
            ].append(
                "sunshine_hours"
            )


        # ----------------------------------------------------
        # EXTRA CONTEXT
        # ----------------------------------------------------

        standard_day[
            "dew_point_mean_c"
        ] = safe_mean(
            hourly_day.get(
                "dew_point",
                []
            )
        )

        standard_day[
            "humidity_daily_source"
        ] = (
            "MEAN_OF_OPEN_METEO_HOURLY_FORECAST"
        )

        standard_day[
            "cloud_cover_daily_source"
        ] = (
            "MEAN_OF_OPEN_METEO_HOURLY_FORECAST"
        )

        standardized_days.append(
            standard_day
        )


    return {

        "provider":
            "Open-Meteo",

        "location": {

            "latitude":
                raw_response.get("latitude"),

            "longitude":
                raw_response.get("longitude"),

            "timezone":
                raw_response.get("timezone"),

            "elevation_m":
                raw_response.get("elevation")
        },

        "forecast_days_returned":
            len(standardized_days),

        "daily":
            standardized_days,

        "epidemiological_notes": {

            "relative_humidity":
                "Daily RH is calculated as the mean of "
                "hourly Open-Meteo RH forecasts.",

            "leaf_wetness":
                "Leaf wetness is not treated as directly measured.",

            "sunshine":
                "Sunshine duration is obtained from the "
                "forecast provider when available.",

            "probability":
                "Precipitation probability is stored as "
                "0–1 in the AgroSmart standard schema."
        }
    }


