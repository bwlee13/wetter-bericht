import requests
import constants

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


class GeocodeError(Exception):
    pass


def _parse_city_state(payload: str) -> tuple[str, str]:
    """
    Parses 'City, ST' into ('City', 'ST')
    """

    if "," not in payload:
        raise GeocodeError(
            "Invalid location format. Use 'City, ST' (e.g. Charlotte, NC)"
        )

    city, state = payload.split(",", 1)
    city = city.strip()
    state = state.strip().upper()

    if not city or not state or len(state) != 2:
        raise GeocodeError(
            "Invalid location format. Use 'City, ST' (e.g. Charlotte, NC)"
        )

    return city, state


def resolve_city(payload: str, country: str = "US"):
    """
    Resolves a city/state string (e.g. 'Charlotte, NC') to lat/lon using Open-Meteo.
    Returns: (city, state, lat, lon)


    GEOCODE RESULTS:  [{'id': 4460243, 'name': 'Charlotte', 'latitude': 35.22709, 'longitude': -80.84313, 'elevation': 229.0, 'feature_code': 'PPLA2', 'country_code': 'US',
    'admin1_id': 4482348, 'admin2_id': 4478884, 'timezone': 'America/New_York', 'population': 874579,
    'country_id': 6252001, 'country': 'United States', 'admin1': 'North Carolina', 'admin2': 'Mecklenburg'},
    """

    city, state = _parse_city_state(payload)

    params = {
        "name": city,
        "country": country,
        "count": 5,
        "language": "en",
        "format": "json",
    }

    response = requests.get(GEOCODE_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    results = data.get("results")
    print("GEOCODE RESULTS: ", results)

    if not results:
        raise GeocodeError(f"No geocoding results for '{payload}'")

    # Prefer exact state match if available
    match = None
    for r in results:
        if r.get("admin1") == constants.US_STATE_MAP.get(state):
            match = r
            break

    # Fallback to first result
    if not match:
        match = results[0]

    lat = match.get("latitude")
    lon = match.get("longitude")

    if lat is None or lon is None:
        raise GeocodeError(f"Geocoding result missing lat/lon for '{payload}'")

    return lat, lon
