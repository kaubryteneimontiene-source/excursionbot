import os
import requests
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

ENTRY_FEES = {
    "vilnius old town": {
        "price": 5,
        "note": "Gediminas Tower entry. Cathedral free.",
        "website": "www.lnm.lt"
    },
    "trakai castle": {
        "price": 7,
        "note": "Island Castle and museum entry.",
        "website": "www.trakaimuziejus.lt"
    },
    "hill of crosses": {
        "price": 0,
        "note": "Free entry. Donations welcome.",
        "website": "www.kryziukalnas.lt"
    },
    "curonian spit": {
        "price": 4,
        "note": "National Park entrance fee.",
        "website": "www.nerija.lt"
    },
    "kaunas old town": {
        "price": 6,
        "note": "War Museum entry. Castle and streets free.",
        "website": "www.kaunas.lt"
    },
    "kernave": {
        "price": 4,
        "note": "Archaeological museum entry.",
        "website": "www.kernave.org"
    },
    "museum of occupations": {
        "price": 4,
        "note": "Full museum including KGB cells.",
        "website": "www.genocid.lt"
    },
    "palanga amber museum": {
        "price": 5,
        "note": "Palace museum and gardens.",
        "website": "www.pgm.lt"
    },
}

# Coordinates for each site
SITE_COORDINATES = {
    "vilnius old town": (25.2797, 54.6872),
    "trakai castle": (24.9340, 54.6379),
    "hill of crosses": (23.4167, 56.0153),
    "curonian spit": (21.0667, 55.3000),
    "kaunas old town": (23.9036, 54.8985),
    "kernave": (24.8333, 54.8833),
    "museum of occupations": (25.2686, 54.6896),
    "palanga amber museum": (21.0678, 55.9196),
}

BUS_COST_PER_KM = 1.20


def geocode_city(city_name: str) -> tuple:
    """Convert city/village name to coordinates using OpenRouteService."""
    api_key = os.getenv("OPENROUTESERVICE_API_KEY")
    if not api_key:
        return None

    try:
        url = "https://api.openrouteservice.org/geocode/search"
        params = {
            "api_key": api_key,
            "text": f"{city_name}, Lithuania",
            "boundary.country": "LT",
            "size": 1
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("features"):
            coords = data["features"][0]["geometry"]["coordinates"]
            return (coords[0], coords[1])  # (longitude, latitude)
        return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def get_road_distance(origin_coords: tuple, dest_coords: tuple) -> float:
    """Get real road distance in km using OpenRouteService."""
    api_key = os.getenv("OPENROUTESERVICE_API_KEY")
    if not api_key:
        return None

    try:
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        body = {
            "coordinates": [
                [origin_coords[0], origin_coords[1]],
                [dest_coords[0], dest_coords[1]]
            ]
        }
        response = requests.post(url, json=body, headers=headers, timeout=10)
        data = response.json()

        if "routes" in data:
            distance_meters = data["routes"][0]["summary"]["distance"]
            return round(distance_meters / 1000, 1)
        return None
    except Exception as e:
        print(f"Routing error: {e}")
        return None


@tool
def calculate_group_budget(
    site: str,
    pupils: int,
    teachers: int,
    starting_city: str
) -> str:
    """
    Calculate estimated excursion budget for a school group.

    Args:
        site: The name of the historical site
        pupils: Number of pupils in the group
        teachers: Number of teachers accompanying the group
        starting_city: The city or village the group is travelling from

    Returns:
        A detailed budget estimate as a string
    """
    site_lower = site.lower().strip()
    total_people = pupils + teachers

    # Match site
    matched_site = None
    for key in ENTRY_FEES:
        if key in site_lower or site_lower in key:
            matched_site = key
            break

    if not matched_site:
        available = ", ".join(ENTRY_FEES.keys())
        return (
            f"Sorry, I don't have cost data for '{site}'. "
            f"Available sites: {available}"
        )

    # Get site coordinates
    site_coords = SITE_COORDINATES.get(matched_site)

    # Geocode starting city
    origin_coords = geocode_city(starting_city)

    # Calculate transport
    if origin_coords and site_coords:
        distance_km = get_road_distance(origin_coords, site_coords)

        if distance_km is not None:
            if distance_km < 2:
                transport_total = 0
                transport_note = "No transport needed - site is in your city."
            else:
                transport_total = round(
                    BUS_COST_PER_KM * distance_km * 2, 2
                )
                per_person = round(transport_total / total_people, 2)
                transport_note = (
                    f"~{distance_km}km each way by school bus "
                    f"(€{per_person} per person)"
                )
        else:
            transport_total = None
            transport_note = "Could not calculate route. Please check manually."
    else:
        transport_total = None
        transport_note = (
            f"Could not find '{starting_city}' on the map. "
            f"Please check the spelling."
        )

    # Entry fees
    fee_info = ENTRY_FEES[matched_site]
    entry_price = fee_info["price"]
    entry_pupils = entry_price * pupils
    entry_teachers = entry_price * teachers
    entry_total = entry_pupils + entry_teachers

    # Food
    food_per_person = 8
    food_total = food_per_person * total_people

    # Total
    if transport_total is not None:
        grand_total = transport_total + entry_total + food_total
        per_pupil = round(
            (transport_total + entry_pupils + food_per_person * pupils)
            / pupils, 2
        ) if pupils > 0 else 0
        transport_line = f"- Bus transport: €{transport_total} ({transport_note})"
        total_line = f"- TOTAL: €{grand_total}"
        per_pupil_line = f"- Estimated cost per pupil: €{per_pupil}"
    else:
        grand_total = entry_total + food_total
        transport_line = f"- Bus transport: Unknown ({transport_note})"
        total_line = f"- TOTAL (excl. transport): €{grand_total}"
        per_pupil_line = (
            f"- Cost per pupil (excl. transport): "
            f"€{round(grand_total / pupils, 2)}"
        )

    return (
        f"Budget Estimate: {matched_site.title()}\n"
        f"Group: {pupils} pupils + {teachers} teachers "
        f"from {starting_city.title()}\n"
        f"{'=' * 40}\n"
        f"{transport_line}\n"
        f"- Entry fees (pupils): €{entry_pupils} "
        f"(€{entry_price} each)\n"
        f"- Entry fees (teachers): €{entry_teachers} "
        f"(€{entry_price} each)\n"
        f"  ℹ️  {fee_info['note']}\n"
        f"  🌐 Official website: {fee_info['website']}\n"
        f"- Lunch and snacks: €{food_total} "
        f"(€{food_per_person} per person)\n"
        f"{'=' * 40}\n"
        f"{total_line}\n"
        f"{per_pupil_line}\n"
        f"\n⚠️ Prices are estimates. Always verify current "
        f"prices directly with the site before booking."
    )
