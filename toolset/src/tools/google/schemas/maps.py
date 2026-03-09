"""Pydantic output schemas for Google Maps tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Geocode Schemas
# =============================================================================


class GeoLocation(BaseModel):
    """Geographic coordinates."""

    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")


class GeocodeResult(BaseModel):
    """A single geocoding result."""

    formatted_address: str = Field(..., description="Formatted address string")
    location: GeoLocation = Field(..., description="Geographic coordinates")
    place_id: str = Field("", description="Google Place ID")
    address_types: list[str] = Field(
        default_factory=list, description="Address type classifications"
    )


class GeocodeData(BaseModel):
    """Output data for google_maps_geocode tool."""

    address: str = Field(..., description="The input address that was geocoded")
    results: list[GeocodeResult] = Field(..., description="List of geocoding results")
    result_count: int = Field(..., description="Number of results returned")


class ReverseGeocodeData(BaseModel):
    """Output data for google_maps_reverse_geocode tool."""

    lat: float = Field(..., description="Input latitude")
    lng: float = Field(..., description="Input longitude")
    results: list[GeocodeResult] = Field(
        ..., description="List of reverse geocoding results"
    )
    result_count: int = Field(..., description="Number of results returned")


# =============================================================================
# Directions Schemas
# =============================================================================


class DirectionStep(BaseModel):
    """A single step in a route."""

    instruction: str = Field(..., description="HTML instruction text")
    distance: str = Field(..., description="Distance text (e.g., '1.2 km')")
    duration: str = Field(..., description="Duration text (e.g., '5 mins')")
    travel_mode: str = Field("", description="Travel mode for this step")


class DirectionRoute(BaseModel):
    """A single route from directions response."""

    summary: str = Field("", description="Route summary")
    distance: str = Field(..., description="Total distance text")
    duration: str = Field(..., description="Total duration text")
    start_address: str = Field("", description="Starting address")
    end_address: str = Field("", description="Ending address")
    steps: list[DirectionStep] = Field(default_factory=list, description="Route steps")


class DirectionsData(BaseModel):
    """Output data for google_maps_directions tool."""

    origin: str = Field(..., description="Origin address or coordinates")
    destination: str = Field(..., description="Destination address or coordinates")
    mode: str = Field(..., description="Travel mode used")
    routes: list[DirectionRoute] = Field(..., description="List of possible routes")


# =============================================================================
# Places Search Schemas
# =============================================================================


class PlaceResult(BaseModel):
    """A single place from search results."""

    name: str = Field(..., description="Place name")
    address: str = Field("", description="Formatted address")
    place_id: str = Field("", description="Google Place ID")
    rating: float | None = Field(None, description="Average rating")
    user_ratings_total: int | None = Field(
        None, description="Total number of user ratings"
    )
    types: list[str] = Field(
        default_factory=list, description="Place type classifications"
    )
    location: GeoLocation | None = Field(None, description="Geographic coordinates")


class PlacesSearchData(BaseModel):
    """Output data for google_maps_search_places tool."""

    query: str = Field(..., description="The search query used")
    results: list[PlaceResult] = Field(..., description="List of place results")
    result_count: int = Field(..., description="Number of results returned")


# =============================================================================
# Distance Matrix Schemas
# =============================================================================


class DistanceMatrixElement(BaseModel):
    """A single origin-destination pair result."""

    origin: str = Field(..., description="Origin address")
    destination: str = Field(..., description="Destination address")
    distance: str = Field("", description="Distance text (e.g., '12.3 km')")
    distance_meters: int | None = Field(None, description="Distance in meters")
    duration: str = Field("", description="Duration text (e.g., '15 mins')")
    duration_seconds: int | None = Field(None, description="Duration in seconds")
    status: str = Field("", description="Element status (OK, NOT_FOUND, etc.)")


class DistanceMatrixData(BaseModel):
    """Output data for google_maps_distance_matrix tool."""

    origins: list[str] = Field(..., description="Origin addresses used")
    destinations: list[str] = Field(..., description="Destination addresses used")
    mode: str = Field("driving", description="Travel mode used")
    elements: list[DistanceMatrixElement] = Field(
        ..., description="Distance/duration results for each origin-destination pair"
    )


# =============================================================================
# Response Wrappers
# =============================================================================


class GeocodeResponse(ToolResponse[GeocodeData]):
    """Response schema for google_maps_geocode tool."""

    pass


class ReverseGeocodeResponse(ToolResponse[ReverseGeocodeData]):
    """Response schema for google_maps_reverse_geocode tool."""

    pass


class DirectionsResponse(ToolResponse[DirectionsData]):
    """Response schema for google_maps_directions tool."""

    pass


class PlacesSearchResponse(ToolResponse[PlacesSearchData]):
    """Response schema for google_maps_search_places tool."""

    pass


class DistanceMatrixResponse(ToolResponse[DistanceMatrixData]):
    """Response schema for google_maps_distance_matrix tool."""

    pass
