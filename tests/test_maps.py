from unittest.mock import MagicMock, patch

import pytest

from zoleotracker import maps


# --- parse_gps_coordinates ---

def test_parse_gps_coordinates_north_west():
    lat, lon = maps.parse_gps_coordinates('47.6 N, 122.3 W')
    assert lat == pytest.approx(47.6)
    assert lon == pytest.approx(-122.3)


def test_parse_gps_coordinates_south_east():
    lat, lon = maps.parse_gps_coordinates('33.9 S, 18.4 E')
    assert lat == pytest.approx(-33.9)
    assert lon == pytest.approx(18.4)


def test_parse_gps_coordinates_north_east():
    lat, lon = maps.parse_gps_coordinates('51.5 N, 0.1 E')
    assert lat == pytest.approx(51.5)
    assert lon == pytest.approx(0.1)


def test_parse_gps_coordinates_south_west():
    lat, lon = maps.parse_gps_coordinates('34.6 S, 58.4 W')
    assert lat == pytest.approx(-34.6)
    assert lon == pytest.approx(-58.4)


def test_parse_gps_coordinates_raises_on_invalid_string():
    with pytest.raises(ValueError, match="Could not parse GPS coordinates"):
        maps.parse_gps_coordinates('not a coordinate')


# --- build_static_map_url ---

def test_build_static_map_url_contains_coordinates():
    url = maps.build_static_map_url(47.6, -122.3, 'TEST_KEY')
    assert '47.6,-122.3' in url
    assert 'TEST_KEY' in url
    assert url.startswith('https://maps.googleapis.com/')


def test_build_static_map_url_contains_size_and_zoom():
    url = maps.build_static_map_url(47.6, -122.3, 'TEST_KEY')
    assert maps.MAP_SIZE in url
    assert maps.MAP_ZOOM in url


# --- fetch_map_image ---

def test_fetch_map_image_returns_response_content():
    fake_image = b'\x89PNG\r\nfake image bytes'
    mock_response = MagicMock()
    mock_response.content = fake_image

    with patch('zoleotracker.maps.requests.get', return_value=mock_response) as mock_get:
        result = maps.fetch_map_image(47.6, -122.3, 'TEST_KEY')

    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    assert result == fake_image


def test_fetch_map_image_raises_on_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception('HTTP 403')

    with patch('zoleotracker.maps.requests.get', return_value=mock_response):
        with pytest.raises(Exception, match='HTTP 403'):
            maps.fetch_map_image(47.6, -122.3, 'BAD_KEY')
