# Google Maps Static API image generation for location check-ins
import logging
import re

import requests

logger = logging.getLogger(__name__)

STATIC_MAP_BASE_URL = 'https://maps.googleapis.com/maps/api/staticmap'
MAP_SIZE = '600x400'
MAP_ZOOM = '10'

_DIRECTIONAL_COORDINATES = re.compile(
    r"""
    ^\s*
    (?P<lat>\d+(?:\.\d+)?)\s*°?\s*(?P<lat_dir>[NS])
    (?:\s*,\s*|\s+)
    (?P<lon>\d+(?:\.\d+)?)\s*°?\s*(?P<lon_dir>[EW])
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)
_SIGNED_COORDINATES = re.compile(
    r"""
    ^\s*
    (?P<lat>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<lon>[+-]?\d+(?:\.\d+)?)
    \s*$
    """,
    re.VERBOSE,
)


def parse_gps_coordinates(location: str) -> tuple[float, float]:
    """Parse a GPS location string into (latitude, longitude).

    Supports:
    - Directional values like ``47.6 N, 122.3 W`` (case-insensitive, comma optional)
    - Signed decimal values like ``47.6, -122.3``
    """
    directional_match = _DIRECTIONAL_COORDINATES.match(location)
    if directional_match:
        lat = float(directional_match.group('lat'))
        if directional_match.group('lat_dir').upper() == 'S':
            lat = -lat

        lon = float(directional_match.group('lon'))
        if directional_match.group('lon_dir').upper() == 'W':
            lon = -lon
    else:
        signed_match = _SIGNED_COORDINATES.match(location)
        if not signed_match:
            raise ValueError(f"Could not parse GPS coordinates from: {location!r}")

        lat = float(signed_match.group('lat'))
        lon = float(signed_match.group('lon'))

    if not -90 <= lat <= 90:
        raise ValueError(f"Latitude out of range: {lat}")
    if not -180 <= lon <= 180:
        raise ValueError(f"Longitude out of range: {lon}")

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
