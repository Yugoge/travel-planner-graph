#!/usr/bin/env python3
"""Get weather forecast using Open-Meteo API (free, no API key needed)."""
import sys
import json
import argparse
from datetime import datetime
import openmeteo_requests

def parse_args():
    parser = argparse.ArgumentParser(description="Get weather forecast")
    parser.add_argument("latitude", type=float, help="Latitude")
    parser.add_argument("longitude", type=float, help="Longitude")
    parser.add_argument("--days", type=int, default=7, choices=[1, 3, 7, 14],
                        help="Forecast days (default: 7)")
    parser.add_argument("--location-name", type=str, default="",
                        help="Location name for display")
    return parser.parse_args()

def get_forecast(latitude, longitude, days=7, location_name=""):
    """Get weather forecast from Open-Meteo API."""
    try:
        # Setup the Open-Meteo API client
        om = openmeteo_requests.Client()

        # API parameters
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "weather_code"
            ],
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "wind_speed_10m"
            ],
            "timezone": "auto",
            "forecast_days": days
        }

        responses = om.weather_api(url, params=params)
        response = responses[0]

        # Process current weather
        current = response.Current()
        current_data = {
            "temperature": round(current.Variables(0).Value(), 1),
            "feels_like": round(current.Variables(2).Value(), 1),
            "humidity": round(current.Variables(1).Value(), 0),
            "precipitation": round(current.Variables(3).Value(), 1),
            "weather_code": int(current.Variables(4).Value()),
            "wind_speed": round(current.Variables(5).Value(), 1),
            "time": datetime.fromtimestamp(current.Time()).isoformat()
        }

        # Process daily forecast
        daily = response.Daily()
        daily_data = []

        for i in range(days):
            day_data = {
                "date": datetime.fromtimestamp(daily.Time() + i * 86400).strftime("%Y-%m-%d"),
                "temp_max": float(round(daily.Variables(0).ValuesAsNumpy()[i], 1)),
                "temp_min": float(round(daily.Variables(1).ValuesAsNumpy()[i], 1)),
                "precipitation": float(round(daily.Variables(2).ValuesAsNumpy()[i], 1)),
                "precipitation_probability": float(round(daily.Variables(3).ValuesAsNumpy()[i], 0)),
                "wind_speed_max": float(round(daily.Variables(4).ValuesAsNumpy()[i], 1)),
                "weather_code": int(daily.Variables(5).ValuesAsNumpy()[i])
            }
            daily_data.append(day_data)

        # Weather code to description mapping (WMO codes)
        weather_descriptions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }

        result = {
            "location": {
                "name": location_name if location_name else f"{latitude},{longitude}",
                "latitude": response.Latitude(),
                "longitude": response.Longitude(),
                "elevation": response.Elevation(),
                "timezone": response.Timezone().decode('utf-8')
            },
            "current": {
                **current_data,
                "condition": weather_descriptions.get(current_data["weather_code"], "Unknown")
            },
            "forecast": [
                {
                    **day,
                    "condition": weather_descriptions.get(day["weather_code"], "Unknown")
                }
                for day in daily_data
            ],
            "data_source": "Open-Meteo API",
            "units": {
                "temperature": "°C",
                "precipitation": "mm",
                "wind_speed": "km/h",
                "humidity": "%"
            }
        }

        return result

    except Exception as e:
        return {
            "error": str(e),
            "location": location_name if location_name else f"{latitude},{longitude}"
        }

def main():
    args = parse_args()
    result = get_forecast(args.latitude, args.longitude, args.days, args.location_name)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
