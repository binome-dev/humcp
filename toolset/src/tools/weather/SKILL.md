---
name: weather-data
description: Fetches current weather conditions and forecasts using the OpenWeatherMap API. Use when the user asks about weather, temperature, or forecasts for any city.
---

# Weather Tools

Tools for fetching weather data from the OpenWeatherMap API.

## Requirements

Set environment variable:
- `OPENWEATHER_API_KEY`: Your OpenWeatherMap API key (free tier supported)

## Current Weather

```python
result = await openweather_get_current(
    city="London",
    units="metric"
)
```

### Response format

```json
{
  "success": true,
  "data": {
    "city": "London",
    "country": "GB",
    "temperature": 15.2,
    "feels_like": 14.1,
    "humidity": 72,
    "pressure": 1013,
    "wind_speed": 3.6,
    "conditions": [
      {
        "main": "Clouds",
        "description": "scattered clouds",
        "icon": "03d"
      }
    ],
    "units": "metric"
  }
}
```

## Weather Forecast

```python
result = await openweather_get_forecast(
    city="New York",
    days=3,
    units="imperial"
)
```

Returns 3-hour interval forecasts for the specified number of days (max 5).

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| city | str | City name (required) |
| days | int | Forecast days, 1-5 (default: 5) |
| units | str | "metric", "imperial", or "standard" |

## Units

| Value | Temperature | Wind Speed |
|-------|-------------|------------|
| metric | Celsius | m/s |
| imperial | Fahrenheit | mph |
| standard | Kelvin | m/s |

## When to Use

- Checking current weather for a city
- Planning activities based on weather forecasts
- Comparing weather across different locations
- Getting temperature, humidity, and wind data
