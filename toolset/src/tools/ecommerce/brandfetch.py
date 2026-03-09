"""Brandfetch API tool for retrieving brand data by domain."""

from __future__ import annotations

import logging
import os

import httpx

from src.humcp.decorator import tool
from src.tools.ecommerce.schemas import (
    BrandfetchBrandData,
    BrandfetchBrandResponse,
    BrandfetchColor,
    BrandfetchLogo,
)

logger = logging.getLogger("humcp.tools.brandfetch")

BRANDFETCH_API_URL = "https://api.brandfetch.io/v2/brands"


@tool()
async def brandfetch_get_brand(domain: str) -> BrandfetchBrandResponse:
    """
    Get brand data (logos, colors, description, links) for a domain using the Brandfetch API.

    Retrieves comprehensive brand information including logos in multiple formats,
    brand colors, descriptions, social links, and company details.

    Args:
        domain: The brand domain to look up (e.g., 'nike.com', 'apple.com').
               Also accepts brand IDs, ISINs, or stock tickers.

    Returns:
        Brand data including logos, colors, and company info, or error message.
    """
    try:
        api_key = os.getenv("BRANDFETCH_API_KEY")
        if not api_key:
            return BrandfetchBrandResponse(
                success=False,
                error="BRANDFETCH_API_KEY not configured. Contact administrator.",
            )

        if not domain.strip():
            return BrandfetchBrandResponse(
                success=False,
                error="Domain parameter cannot be empty.",
            )

        logger.info("Fetching brand data for %s", domain)

        url = f"{BRANDFETCH_API_URL}/{domain}"
        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        logos = [
            BrandfetchLogo(
                type=logo.get("type"),
                theme=logo.get("theme"),
                formats=logo.get("formats", []),
            )
            for logo in data.get("logos", [])
        ]

        colors = [
            BrandfetchColor(
                hex=color.get("hex"),
                type=color.get("type"),
                brightness=color.get("brightness"),
            )
            for color in data.get("colors", [])
        ]

        brand_data = BrandfetchBrandData(
            name=data.get("name"),
            domain=data.get("domain"),
            description=data.get("description"),
            long_description=data.get("longDescription"),
            logos=logos,
            colors=colors,
            links=data.get("links", []),
            company=data.get("company"),
        )

        return BrandfetchBrandResponse(
            success=True,
            data=brand_data,
        )
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 404:
            logger.warning("Brand not found for domain %s", domain)
            return BrandfetchBrandResponse(
                success=False,
                error=f"Brand not found for domain: {domain}",
            )
        if status == 401:
            logger.error("Invalid Brandfetch API key")
            return BrandfetchBrandResponse(
                success=False,
                error="Invalid BRANDFETCH_API_KEY. Check your API key configuration.",
            )
        if status == 429:
            logger.warning("Brandfetch rate limit exceeded")
            return BrandfetchBrandResponse(
                success=False,
                error="Brandfetch rate limit exceeded. Please try again later.",
            )
        logger.exception("HTTP error fetching brand for %s", domain)
        return BrandfetchBrandResponse(
            success=False,
            error=f"Brandfetch API error ({status}): {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to fetch brand data for %s", domain)
        return BrandfetchBrandResponse(
            success=False,
            error=f"Error fetching brand data for {domain}: {e}",
        )
