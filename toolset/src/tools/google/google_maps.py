"""Google Maps tools for geocoding, directions, and place search."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from src.humcp.decorator import tool
from src.tools.google.schemas.maps import (
    DirectionRoute,
    DirectionsData,
    DirectionsResponse,
    DirectionStep,
    GeocodeData,
    GeocodeResponse,
    GeocodeResult,
    GeoLocation,
    PlaceResult,
    PlacesSearchData,
    PlacesSearchResponse,
    ReverseGeocodeData,
    ReverseGeocodeResponse,
)

logger = logging.getLogger("humcp.tools.google.maps")

_MAPS_API_BASE = "https://maps.googleapis.com/maps/api"


def _get_api_key() -> str | None:
    """Get the Google Maps API key from environment."""
    return os.getenv("GOOGLE_MAPS_API_KEY")


async def _maps_request(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    """Make an HTTP request to the Google Maps API.

    Args:
        endpoint: API endpoint path (e.g., "geocode/json").
        params: Query parameters to include.

    Returns:
        Parsed JSON response.

    Raises:
        httpx.HTTPStatusError: If the API returns an error HTTP status.
        ValueError: If the API key is not configured.
    """
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable is not set")

    params["key"] = api_key
    url = f"{_MAPS_API_BASE}/{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def _parse_geocode_results(results: list[dict[str, Any]]) -> list[GeocodeResult]:
    """Parse raw geocode API results into GeocodeResult models."""
    return [
        GeocodeResult(
            formatted_address=r.get("formatted_address", ""),
            location=GeoLocation(
                lat=r.get("geometry", {}).get("location", {}).get("lat", 0.0),
                lng=r.get("geometry", {}).get("location", {}).get("lng", 0.0),
            ),
            place_id=r.get("place_id", ""),
            address_types=r.get("types", []),
        )
        for r in results
    ]


@tool()
async def google_maps_geocode(address: str) -> GeocodeResponse:
    """Convert an address into geographic coordinates using Google Maps Geocoding API.

    Takes a human-readable address and returns latitude/longitude coordinates
    along with formatted address information.

    Args:
        address: The address to geocode (e.g., "1600 Amphitheatre Parkway, Mountain View, CA").

    Returns:
        Geocoding results with coordinates and formatted address.
    """
    try:
        logger.info("Geocoding address: %s", address)

        data = await _maps_request("geocode/json", {"address": address})

        if data.get("status") != "OK":
            return GeocodeResponse(
                success=False,
                error=f"Geocoding failed: {data.get('status')} - {data.get('error_message', '')}",
            )

        results = _parse_geocode_results(data.get("results", []))

        return GeocodeResponse(
            success=True,
            data=GeocodeData(
                address=address,
                results=results,
                result_count=len(results),
            ),
        )
    except Exception as e:
        logger.exception("Geocoding failed")
        return GeocodeResponse(success=False, error=str(e))


@tool()
async def google_maps_reverse_geocode(lat: float, lng: float) -> ReverseGeocodeResponse:
    """Convert geographic coordinates into an address using Google Maps Reverse Geocoding API.

    Takes latitude and longitude and returns human-readable address information.

    Args:
        lat: Latitude of the location.
        lng: Longitude of the location.

    Returns:
        Reverse geocoding results with address information.
    """
    try:
        logger.info("Reverse geocoding lat=%f lng=%f", lat, lng)

        data = await _maps_request("geocode/json", {"latlng": f"{lat},{lng}"})

        if data.get("status") != "OK":
            return ReverseGeocodeResponse(
                success=False,
                error=f"Reverse geocoding failed: {data.get('status')} - {data.get('error_message', '')}",
            )

        results = _parse_geocode_results(data.get("results", []))

        return ReverseGeocodeResponse(
            success=True,
            data=ReverseGeocodeData(
                lat=lat,
                lng=lng,
                results=results,
                result_count=len(results),
            ),
        )
    except Exception as e:
        logger.exception("Reverse geocoding failed")
        return ReverseGeocodeResponse(success=False, error=str(e))


@tool()
async def google_maps_directions(
    origin: str,
    destination: str,
    mode: str = "driving",
) -> DirectionsResponse:
    """Get directions between two locations using Google Maps Directions API.

    Returns step-by-step directions, distance, and duration for a route.

    Args:
        origin: Starting point address or coordinates.
        destination: Destination address or coordinates.
        mode: Travel mode. Options: "driving", "walking", "bicycling", "transit". Defaults to "driving".

    Returns:
        Route information including steps, distance, and duration.
    """
    try:
        logger.info(
            "Getting directions from %s to %s via %s",
            origin,
            destination,
            mode,
        )

        data = await _maps_request(
            "directions/json",
            {
                "origin": origin,
                "destination": destination,
                "mode": mode,
            },
        )

        if data.get("status") != "OK":
            return DirectionsResponse(
                success=False,
                error=f"Directions failed: {data.get('status')} - {data.get('error_message', '')}",
            )

        routes: list[DirectionRoute] = []
        for route in data.get("routes", []):
            legs = route.get("legs", [{}])
            leg = legs[0] if legs else {}

            steps = [
                DirectionStep(
                    instruction=step.get("html_instructions", ""),
                    distance=step.get("distance", {}).get("text", ""),
                    duration=step.get("duration", {}).get("text", ""),
                    travel_mode=step.get("travel_mode", ""),
                )
                for step in leg.get("steps", [])
            ]

            routes.append(
                DirectionRoute(
                    summary=route.get("summary", ""),
                    distance=leg.get("distance", {}).get("text", ""),
                    duration=leg.get("duration", {}).get("text", ""),
                    start_address=leg.get("start_address", ""),
                    end_address=leg.get("end_address", ""),
                    steps=steps,
                )
            )

        return DirectionsResponse(
            success=True,
            data=DirectionsData(
                origin=origin,
                destination=destination,
                mode=mode,
                routes=routes,
            ),
        )
    except Exception as e:
        logger.exception("Directions request failed")
        return DirectionsResponse(success=False, error=str(e))


@tool()
async def google_maps_search_places(
    query: str,
    location: str | None = None,
    radius: int = 5000,
) -> PlacesSearchResponse:
    """Search for places using Google Maps Places API.

    Searches for places matching the query string, optionally near a specific location.

    Args:
        query: The search query (e.g., "restaurants near Central Park").
        location: Optional center point as "lat,lng" string to bias results.
        radius: Search radius in meters around the location (default: 5000).

    Returns:
        List of matching places with name, address, rating, and location.
    """
    try:
        logger.info("Searching places: %s", query)

        params: dict[str, Any] = {"query": query}
        if location:
            params["location"] = location
            params["radius"] = radius

        data = await _maps_request("place/textsearch/json", params)

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            return PlacesSearchResponse(
                success=False,
                error=f"Places search failed: {data.get('status')} - {data.get('error_message', '')}",
            )

        results: list[PlaceResult] = []
        for place in data.get("results", []):
            geo_loc = place.get("geometry", {}).get("location", {})
            location_data = None
            if geo_loc:
                location_data = GeoLocation(
                    lat=geo_loc.get("lat", 0.0),
                    lng=geo_loc.get("lng", 0.0),
                )

            results.append(
                PlaceResult(
                    name=place.get("name", ""),
                    address=place.get("formatted_address", ""),
                    place_id=place.get("place_id", ""),
                    rating=place.get("rating"),
                    user_ratings_total=place.get("user_ratings_total"),
                    types=place.get("types", []),
                    location=location_data,
                )
            )

        return PlacesSearchResponse(
            success=True,
            data=PlacesSearchData(
                query=query,
                results=results,
                result_count=len(results),
            ),
        )
    except Exception as e:
        logger.exception("Places search failed")
        return PlacesSearchResponse(success=False, error=str(e))
