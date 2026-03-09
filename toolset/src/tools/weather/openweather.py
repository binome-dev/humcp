"""OpenWeatherMap tools for current weather, forecasts, air pollution, and geocoding.

Wraps the OpenWeatherMap API for weather data retrieval, 5-day forecasts,
air quality information, and city-to-coordinate geocoding.

Environment variables:
    OPENWEATHER_API_KEY: API key for OpenWeatherMap (free tier supported).
"""

from __future__ import annotations

import logging
import os

import httpx

from src.humcp.decorator import tool
from src.tools.weather.schemas import (
    AirPollutionComponent,
    AirPollutionData,
    AirPollutionResponse,
    CurrentWeatherData,
    CurrentWeatherResponse,
    ForecastEntry,
    ForecastWeatherData,
    ForecastWeatherResponse,
    GeocodingData,
    GeocodingResponse,
    GeocodingResult,
    WeatherCondition,
)

logger = logging.getLogger("humcp.tools.openweather")

_OWM_BASE = "https://api.openweathermap.org/data/2.5"
_GEO_BASE = "https://api.openweathermap.org/geo/1.0"

_VALID_UNITS = {"metric", "imperial", "standard"}


def _get_api_key() -> str | None:
    """Return the OpenWeatherMap API key from environment."""
    return os.getenv("OPENWEATHER_API_KEY")


def _check_configured() -> str | None:
    """Return an error message if OpenWeatherMap is not configured, else None."""
    if not _get_api_key():
        return "OpenWeatherMap API not configured. Set OPENWEATHER_API_KEY environment variable."
    return None


async def _geocode_city(
    client: httpx.AsyncClient, city: str, api_key: str
) -> dict | None:
    """Geocode a city name to lat/lon using the OpenWeatherMap Geocoding API.

    Returns the first result as a dict with 'lat', 'lon', 'name', 'country',
    or None if nothing was found.
    """
    params = {"q": city, "limit": 1, "appid": api_key}
    response = await client.get(f"{_GEO_BASE}/direct", params=params)
    response.raise_for_status()
    results = response.json()
    if not results:
        return None
    return {
        "lat": results[0]["lat"],
        "lon": results[0]["lon"],
        "name": results[0].get("name", city),
        "country": results[0].get("country", ""),
        "state": results[0].get("state"),
    }


def _parse_conditions(weather_list: list[dict]) -> list[WeatherCondition]:
    """Parse a list of weather condition dicts from the OWM API response."""
    return [
        WeatherCondition(
            main=w.get("main", ""),
            description=w.get("description", ""),
            icon=w.get("icon", ""),
        )
        for w in weather_list
    ]


@tool()
async def openweather_get_current(
    city: str,
    units: str = "metric",
) -> CurrentWeatherResponse:
    """Get current weather data for a city.

    Returns temperature, humidity, pressure, wind, visibility, cloud cover,
    sunrise/sunset times, and weather conditions.

    Args:
        city: City name, optionally with country code (e.g. "London",
            "New York", "Tokyo", "Paris,FR").
        units: Units of measurement. One of "metric" (Celsius, m/s),
            "imperial" (Fahrenheit, mph), or "standard" (Kelvin, m/s).
            Default is "metric".

    Returns:
        Current weather data including temperature, wind, humidity, and conditions.
    """
    try:
        err = _check_configured()
        if err:
            return CurrentWeatherResponse(success=False, error=err)

        api_key = _get_api_key()

        if units not in _VALID_UNITS:
            return CurrentWeatherResponse(
                success=False,
                error=f"Invalid units '{units}'. Must be one of: {', '.join(sorted(_VALID_UNITS))}",
            )

        logger.info("OpenWeather current city=%r units=%s", city, units)

        async with httpx.AsyncClient(timeout=15) as client:
            geo = await _geocode_city(client, city, api_key)
            if geo is None:
                return CurrentWeatherResponse(
                    success=False,
                    error=f"City '{city}' not found.",
                )

            params = {
                "lat": geo["lat"],
                "lon": geo["lon"],
                "units": units,
                "appid": api_key,
            }
            response = await client.get(f"{_OWM_BASE}/weather", params=params)
            response.raise_for_status()
            data = response.json()

        main = data.get("main", {})
        wind = data.get("wind", {})
        sys_data = data.get("sys", {})

        return CurrentWeatherResponse(
            success=True,
            data=CurrentWeatherData(
                city=geo["name"],
                country=geo["country"],
                temperature=main.get("temp", 0.0),
                feels_like=main.get("feels_like", 0.0),
                temp_min=main.get("temp_min", 0.0),
                temp_max=main.get("temp_max", 0.0),
                humidity=main.get("humidity", 0),
                pressure=main.get("pressure", 0),
                wind_speed=wind.get("speed", 0.0),
                wind_deg=wind.get("deg"),
                wind_gust=wind.get("gust"),
                visibility=data.get("visibility"),
                clouds=data.get("clouds", {}).get("all"),
                conditions=_parse_conditions(data.get("weather", [])),
                units=units,
                sunrise=sys_data.get("sunrise"),
                sunset=sys_data.get("sunset"),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("OpenWeather current HTTP error")
        return CurrentWeatherResponse(
            success=False,
            error=f"OpenWeatherMap API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("OpenWeather current failed")
        return CurrentWeatherResponse(
            success=False, error=f"OpenWeather current weather failed: {e}"
        )


@tool()
async def openweather_get_forecast(
    city: str,
    days: int = 5,
    units: str = "metric",
) -> ForecastWeatherResponse:
    """Get a 5-day weather forecast for a city in 3-hour intervals.

    The OpenWeatherMap free tier provides up to 5 days of forecast data
    with 3-hour granularity (up to 40 data points).

    Args:
        city: City name, optionally with country code (e.g. "London",
            "New York,US", "Tokyo,JP").
        days: Number of forecast days (1-5, default 5). Clamped to valid range.
        units: Units of measurement. One of "metric" (Celsius, m/s),
            "imperial" (Fahrenheit, mph), or "standard" (Kelvin, m/s).
            Default is "metric".

    Returns:
        Forecast entries with temperature, humidity, wind, precipitation
        probability, and conditions.
    """
    try:
        err = _check_configured()
        if err:
            return ForecastWeatherResponse(success=False, error=err)

        api_key = _get_api_key()

        if units not in _VALID_UNITS:
            return ForecastWeatherResponse(
                success=False,
                error=f"Invalid units '{units}'. Must be one of: {', '.join(sorted(_VALID_UNITS))}",
            )

        days = max(1, min(days, 5))
        logger.info("OpenWeather forecast city=%r days=%d units=%s", city, days, units)

        async with httpx.AsyncClient(timeout=15) as client:
            geo = await _geocode_city(client, city, api_key)
            if geo is None:
                return ForecastWeatherResponse(
                    success=False,
                    error=f"City '{city}' not found.",
                )

            params = {
                "lat": geo["lat"],
                "lon": geo["lon"],
                "units": units,
                "cnt": min(days * 8, 40),
                "appid": api_key,
            }
            response = await client.get(f"{_OWM_BASE}/forecast", params=params)
            response.raise_for_status()
            data = response.json()

        forecasts: list[ForecastEntry] = []
        for entry in data.get("list", []):
            entry_main = entry.get("main", {})
            entry_wind = entry.get("wind", {})
            forecasts.append(
                ForecastEntry(
                    dt=entry.get("dt", 0),
                    dt_txt=entry.get("dt_txt", ""),
                    temperature=entry_main.get("temp", 0.0),
                    feels_like=entry_main.get("feels_like", 0.0),
                    temp_min=entry_main.get("temp_min", 0.0),
                    temp_max=entry_main.get("temp_max", 0.0),
                    humidity=entry_main.get("humidity", 0),
                    pressure=entry_main.get("pressure", 0),
                    wind_speed=entry_wind.get("speed", 0.0),
                    wind_deg=entry_wind.get("deg"),
                    pop=entry.get("pop"),
                    conditions=_parse_conditions(entry.get("weather", [])),
                )
            )

        logger.info("OpenWeather forecast complete entries=%d", len(forecasts))
        return ForecastWeatherResponse(
            success=True,
            data=ForecastWeatherData(
                city=geo["name"],
                country=geo["country"],
                days=days,
                units=units,
                forecasts=forecasts,
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("OpenWeather forecast HTTP error")
        return ForecastWeatherResponse(
            success=False,
            error=f"OpenWeatherMap API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("OpenWeather forecast failed")
        return ForecastWeatherResponse(
            success=False, error=f"OpenWeather forecast failed: {e}"
        )


@tool()
async def openweather_get_air_pollution(
    city: str,
) -> AirPollutionResponse:
    """Get current air pollution data for a city.

    Returns the Air Quality Index (AQI) and concentrations of pollutants
    including CO, NO, NO2, O3, SO2, PM2.5, PM10, and NH3.

    The AQI scale: 1 = Good, 2 = Fair, 3 = Moderate, 4 = Poor, 5 = Very Poor.

    Args:
        city: City name (e.g. "London", "Beijing", "Los Angeles").

    Returns:
        Air quality index and pollutant concentrations.
    """
    try:
        err = _check_configured()
        if err:
            return AirPollutionResponse(success=False, error=err)

        api_key = _get_api_key()

        logger.info("OpenWeather air pollution city=%r", city)

        async with httpx.AsyncClient(timeout=15) as client:
            geo = await _geocode_city(client, city, api_key)
            if geo is None:
                return AirPollutionResponse(
                    success=False,
                    error=f"City '{city}' not found.",
                )

            params = {
                "lat": geo["lat"],
                "lon": geo["lon"],
                "appid": api_key,
            }
            response = await client.get(f"{_OWM_BASE}/air_pollution", params=params)
            response.raise_for_status()
            data = response.json()

        pollution_list = data.get("list", [])
        if not pollution_list:
            return AirPollutionResponse(
                success=False,
                error=f"No air pollution data available for '{city}'.",
            )

        entry = pollution_list[0]
        main_data = entry.get("main", {})
        components = entry.get("components", {})

        return AirPollutionResponse(
            success=True,
            data=AirPollutionData(
                city=geo["name"],
                country=geo["country"],
                aqi=main_data.get("aqi", 0),
                components=AirPollutionComponent(
                    co=components.get("co"),
                    no=components.get("no"),
                    no2=components.get("no2"),
                    o3=components.get("o3"),
                    so2=components.get("so2"),
                    pm2_5=components.get("pm2_5"),
                    pm10=components.get("pm10"),
                    nh3=components.get("nh3"),
                ),
                dt=entry.get("dt"),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("OpenWeather air pollution HTTP error")
        return AirPollutionResponse(
            success=False,
            error=f"OpenWeatherMap API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("OpenWeather air pollution failed")
        return AirPollutionResponse(
            success=False, error=f"OpenWeather air pollution failed: {e}"
        )


@tool()
async def openweather_geocode(
    query: str,
    limit: int = 5,
) -> GeocodingResponse:
    """Geocode a location name to latitude/longitude coordinates.

    Uses the OpenWeatherMap Geocoding API to convert city names, zip codes,
    or location strings into geographic coordinates.  Useful for finding
    exact coordinates before using other weather tools.

    Args:
        query: Location to search for (e.g. "London", "New York,US",
            "Tokyo,JP", "10001").
        limit: Maximum number of results to return (1-5, default 5).

    Returns:
        List of matching locations with name, country, state, and coordinates.
    """
    try:
        err = _check_configured()
        if err:
            return GeocodingResponse(success=False, error=err)

        api_key = _get_api_key()
        limit = max(1, min(limit, 5))

        logger.info("OpenWeather geocode query=%r limit=%d", query, limit)

        async with httpx.AsyncClient(timeout=15) as client:
            params = {"q": query, "limit": limit, "appid": api_key}
            response = await client.get(f"{_GEO_BASE}/direct", params=params)
            response.raise_for_status()
            results = response.json()

        locations = [
            GeocodingResult(
                name=r.get("name", ""),
                country=r.get("country", ""),
                state=r.get("state"),
                lat=r["lat"],
                lon=r["lon"],
            )
            for r in results
        ]

        logger.info("OpenWeather geocode complete count=%d", len(locations))

        return GeocodingResponse(
            success=True,
            data=GeocodingData(
                query=query,
                results=locations,
                count=len(locations),
            ),
        )
    except httpx.HTTPStatusError as e:
        logger.exception("OpenWeather geocode HTTP error")
        return GeocodingResponse(
            success=False,
            error=f"OpenWeatherMap API error ({e.response.status_code}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("OpenWeather geocode failed")
        return GeocodingResponse(
            success=False, error=f"OpenWeather geocode failed: {e}"
        )
