# Google Maps Static API image generation for location check-ins
import logging
import re

import requests

logger = logging.getLogger(__name__)

STATIC_MAP_BASE_URL = 'https://maps.googleapis.com/maps/api/staticmap'
MAP_SIZE = '600x400'
MAP_ZOOM = '10'


def parse_gps_coordinates(location: str) -> tuple[float, float]:
    """Parse a GPS location string like '47.6 N, 122.3 W' into (latitude, longitude).

    North and East values are positive; South and West values are negative.
    """
    pattern = r'([\d.]+)\s*([NS])\s*,\s*([\d.]+)\s*([EW])'
    match = re.match(pattern, location.strip())
    if not match:
        raise ValueError(f"Could not parse GPS coordinates from: {location!r}")

    lat = float(match.group(1))
    if match.group(2) == 'S':
        lat = -lat

    lon = float(match.group(3))
    if match.group(4) == 'W':
        lon = -lon

    return lat, lon


def build_static_map_url(lat: float, lon: float, api_key: str) -> str:
    """Build a Google Maps Static API URL for the given coordinates."""
    center = f'{lat},{lon}'
    marker = f'color:red|{center}'
    url = (
        f'{STATIC_MAP_BASE_URL}'
        f'?center={center}'
        f'&zoom={MAP_ZOOM}'
        f'&size={MAP_SIZE}'
        f'&markers={marker}'
        f'&key={api_key}'
    )
    return url


def fetch_map_image(lat: float, lon: float, api_key: str) -> bytes:
    """Fetch a map image from the Google Maps Static API and return the raw bytes."""
    url = build_static_map_url(lat, lon, api_key)
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.content
