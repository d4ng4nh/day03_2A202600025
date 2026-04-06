# geo_tools.py

from typing import TypedDict
import math
import os
import re


class Location(TypedDict):
    lat: float
    lon: float


def _load_cities() -> dict:
    """Load city coordinates from database.md"""
    db_path = os.path.join(os.path.dirname(__file__), "database.md")
    city_map = {}

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    with open(db_path, 'r') as f:
        content = f.read()

    # Extract Cities section
    cities_section = re.search(r'## Cities\n(.*?)\n## ', content, re.DOTALL)
    if not cities_section:
        raise ValueError("Cities section not found in database.md")

    lines = cities_section.group(1).strip().split('\n')
    for line in lines:
        # Skip header and separator lines
        if line.startswith('|') and not line.startswith('| City') and '-' not in line:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) == 3 and parts[1] and parts[2]:  # Ensure parts are not empty
                city, lat, lon = parts
                try:
                    city_map[city.lower()] = {"lat": float(lat), "lon": float(lon)}
                except ValueError:
                    # Skip lines that can't be parsed as floats
                    pass

    return city_map


def geocode(city: str) -> Location:
    city_map = _load_cities()
    key = city.lower()
    if key not in city_map:
        raise ValueError(f"Unknown city: '{city}'. Known cities: {list(city_map.keys())}")
    return city_map[key]


def haversine(loc1: Location, loc2: Location) -> float:
    R = 6371
    phi1    = math.radians(loc1["lat"])
    phi2    = math.radians(loc2["lat"])
    dphi    = math.radians(loc2["lat"] - loc1["lat"])
    dlambda = math.radians(loc2["lon"] - loc1["lon"])
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def get_distance(city1: str, city2: str) -> str:
    loc1 = geocode(city1)
    loc2 = geocode(city2)
    km   = haversine(loc1, loc2)
    return f"{km} km"


# Tool definition — includes "fn" so the agent can call it directly
tool_schema = {
    "name":        "get_distance",
    "description": "Calculate the distance in km between two cities by name.",
    "fn":          get_distance,          # ← callable attached here
    "parameters": {
        "type": "object",
        "properties": {
            "city1": {"type": "string"},
            "city2": {"type": "string"},
        },
        "required": ["city1", "city2"],
    },
}


if __name__ == "__main__":
    print(get_distance("Hanoi", "Ho Chi Minh City"))
