"""Pydantic output schemas for weather tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# OpenWeatherMap Schemas
# =============================================================================


class WeatherCondition(BaseModel):
    """Weather condition details from OpenWeatherMap."""

    main: str = Field(
        ..., description="Weather group (Rain, Snow, Clouds, Clear, etc.)"
    )
    description: str = Field(..., description="Detailed weather condition description")
    icon: str = Field(..., description="Weather icon ID (e.g. '01d', '10n')")


class CurrentWeatherData(BaseModel):
    """Output data for openweather_get_current tool."""

    city: str = Field(..., description="City name")
    country: str = Field("", description="ISO 3166-1 alpha-2 country code")
    temperature: float = Field(..., description="Current temperature")
    feels_like: float = Field(
        ..., description="Perceived temperature accounting for wind/humidity"
    )
    temp_min: float = Field(..., description="Minimum temperature at the moment")
    temp_max: float = Field(..., description="Maximum temperature at the moment")
    humidity: int = Field(..., description="Humidity percentage (0-100)")
    pressure: int = Field(..., description="Atmospheric pressure in hPa (hectopascals)")
    wind_speed: float = Field(
        ..., description="Wind speed (m/s for metric, mph for imperial)"
    )
    wind_deg: int | None = Field(
        None,
        description="Wind direction in meteorological degrees (0=N, 90=E, 180=S, 270=W)",
    )
    wind_gust: float | None = Field(None, description="Wind gust speed")
    visibility: int | None = Field(None, description="Visibility in meters (max 10km)")
    clouds: int | None = Field(None, description="Cloudiness percentage (0-100)")
    conditions: list[WeatherCondition] = Field(
        default_factory=list, description="Weather conditions"
    )
    units: str = Field(
        "metric", description="Units of measurement used (metric, imperial, standard)"
    )
    sunrise: int | None = Field(None, description="Sunrise time as Unix UTC timestamp")
    sunset: int | None = Field(None, description="Sunset time as Unix UTC timestamp")


class ForecastEntry(BaseModel):
    """A single forecast time slot (3-hour interval)."""

    dt: int = Field(..., description="Unix UTC timestamp for this forecast point")
    dt_txt: str = Field(
        ..., description="Human-readable date/time string (YYYY-MM-DD HH:MM:SS)"
    )
    temperature: float = Field(..., description="Forecasted temperature")
    feels_like: float = Field(..., description="Perceived temperature")
    temp_min: float = Field(..., description="Minimum temperature in this interval")
    temp_max: float = Field(..., description="Maximum temperature in this interval")
    humidity: int = Field(..., description="Humidity percentage (0-100)")
    pressure: int = Field(..., description="Atmospheric pressure in hPa")
    wind_speed: float = Field(..., description="Wind speed")
    wind_deg: int | None = Field(None, description="Wind direction in degrees")
    pop: float | None = Field(
        None, description="Probability of precipitation (0.0-1.0)"
    )
    conditions: list[WeatherCondition] = Field(
        default_factory=list, description="Weather conditions"
    )


class ForecastWeatherData(BaseModel):
    """Output data for openweather_get_forecast tool."""

    city: str = Field(..., description="City name")
    country: str = Field("", description="Country code")
    days: int = Field(..., description="Number of days requested")
    units: str = Field("metric", description="Units of measurement used")
    forecasts: list[ForecastEntry] = Field(
        default_factory=list, description="List of forecast entries (3-hour intervals)"
    )


class AirPollutionComponent(BaseModel):
    """Individual air quality component measurement."""

    co: float | None = Field(None, description="Carbon monoxide concentration in ug/m3")
    no: float | None = Field(
        None, description="Nitrogen monoxide concentration in ug/m3"
    )
    no2: float | None = Field(
        None, description="Nitrogen dioxide concentration in ug/m3"
    )
    o3: float | None = Field(None, description="Ozone concentration in ug/m3")
    so2: float | None = Field(
        None, description="Sulphur dioxide concentration in ug/m3"
    )
    pm2_5: float | None = Field(
        None, description="Fine particulate matter (PM2.5) in ug/m3"
    )
    pm10: float | None = Field(
        None, description="Coarse particulate matter (PM10) in ug/m3"
    )
    nh3: float | None = Field(None, description="Ammonia concentration in ug/m3")


class AirPollutionData(BaseModel):
    """Output data for openweather_get_air_pollution tool."""

    city: str = Field(..., description="City name")
    country: str = Field("", description="Country code")
    aqi: int = Field(
        ...,
        description="Air Quality Index (1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor)",
    )
    components: AirPollutionComponent = Field(
        ..., description="Pollutant concentrations"
    )
    dt: int | None = Field(None, description="Unix UTC timestamp of the measurement")


class GeocodingResult(BaseModel):
    """A single geocoding result."""

    name: str = Field(..., description="Location name")
    country: str = Field("", description="Country code")
    state: str | None = Field(None, description="State or region name")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")


class GeocodingData(BaseModel):
    """Output data for openweather_geocode tool."""

    query: str = Field(..., description="Original search query")
    results: list[GeocodingResult] = Field(
        default_factory=list, description="List of matching locations"
    )
    count: int = Field(..., description="Number of results returned")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class CurrentWeatherResponse(ToolResponse[CurrentWeatherData]):
    """Response schema for openweather_get_current tool."""

    pass


class ForecastWeatherResponse(ToolResponse[ForecastWeatherData]):
    """Response schema for openweather_get_forecast tool."""

    pass


class AirPollutionResponse(ToolResponse[AirPollutionData]):
    """Response schema for openweather_get_air_pollution tool."""

    pass


class GeocodingResponse(ToolResponse[GeocodingData]):
    """Response schema for openweather_geocode tool."""

    pass
