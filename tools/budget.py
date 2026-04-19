import os
import json
import requests
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


config = load_config()
ENTRY_FEES = config["entry_fees"]
SITE_COORDINATES = {k: tuple(v) for k, v in config["site_coordinates"].items()}
BUS_COST_PER_KM = config["transport"]["bus_cost_per_km"]

# Food cost by duration
FOOD_BY_DURATION = {
    "half": 4.0,   # Half day: snack only
    "full": 8.0,   # Full day: lunch + snack
    "two":  20.0,  # Two days: lunch + dinner + breakfast + snack
}

# Accommodation cost per person for 2-day trips
ACCOMMODATION_PER_PERSON = 35.0


def geocode_city(city_name: str) -> tuple:
    """Convert city/village name to coordinates using OpenRouteService."""
    api_key = os.getenv("OPENROUTESERVICE_API_KEY")
    if not api_key:
        return None

    try:
        url = "https://api.openrouteservice.org/geocode/search"
        params = {
            "api_key": api_key,
            "text": city_name,
            "size": 1
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("features"):
            coords = data["features"][0]["geometry"]["coordinates"]
            return (coords[0], coords[1])
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
    starting_city: str,
    bus_cost_per_km: float = None,
    duration: str = "full"
) -> str:
    """
    Calculate estimated excursion budget for a school group visiting
    a Baltic historical or cultural site.

    Args:
        site: The name of the historical site
        pupils: Number of pupils in the group
        teachers: Number of teachers accompanying the group
        starting_city: The city or village the group is travelling from
        bus_cost_per_km: Optional custom bus cost per km (default from config)
        duration: Trip duration - 'half' (4h), 'full' (8h), or 'two' (2 days)

    Returns:
        A detailed budget estimate as a string
    """
    site_lower = site.lower().strip()
    total_people = pupils + teachers

    # Use custom bus cost if provided, otherwise use config value
    cost_per_km = bus_cost_per_km if bus_cost_per_km is not None else BUS_COST_PER_KM

    # Lithuanian to English site name mapping
    lt_to_en = {
        "trakų pilis": "trakai castle",
        "vilniaus senamiestis": "vilnius old town",
        "kryžių kalnas": "hill of crosses",
        "kuršių nerija": "curonian spit",
        "kauno senamiestis": "kaunas old town",
        "kernavė": "kernave",
        "okupacijų muziejus": "museum of occupations",
        "palangos gintaro muziejus": "palanga amber museum",
        "rygos senamiestis": "riga old town",
        "talino senamiestis": "tallinn old town",
        "rundālės pils": "rundale palace",
        "siguldos pilis": "sigulda castle",
        "cėsio pilis": "cesis castle",
        "jūrmala": "jurmala",
        "pärnu": "parnu",
        "haapsalu pilis": "haapsalu castle",
    }

    if site_lower in lt_to_en:
        site_lower = lt_to_en[site_lower]

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

    site_coords = SITE_COORDINATES.get(matched_site)
    origin_coords = geocode_city(starting_city)

    # Max realistic one-way distance by duration
    # "two" days has no limit - Latvia, Estonia fully realistic for school trips
    DISTANCE_LIMITS = {
        "half": 75,   # 4h visit: ~1.5h travel each way
        "full": 200,  # 8h visit: up to ~3h travel each way
    }

    if origin_coords and site_coords:
        distance_km = get_road_distance(origin_coords, site_coords)

        if distance_km is not None:
            if distance_km < 2:
                transport_total = 0
                transport_note = "No transport needed - site is in your city."
            else:
                transport_total = round(cost_per_km * distance_km * 2, 2)
                per_person = round(transport_total / total_people, 2)
                transport_note = (
                    f"~{distance_km}km each way by school bus "
                    f"(€{cost_per_km}/km, €{per_person} per person)"
                )

            # Duration vs distance validation
            dur_check = duration.lower()
            if "two" in dur_check or "2" in dur_check:
                dur_check = "two"
            elif "half" in dur_check:
                dur_check = "half"
            else:
                dur_check = "full"

            max_km = DISTANCE_LIMITS.get(dur_check, 150)
            if distance_km > max_km:
                duration_labels = {"half": "half day (4h)", "full": "full day (8h)", "two": "two days"}
                transport_note += (
                    f"\n  ⚠️  WARNING: {distance_km}km is too far for a {duration_labels.get(dur_check, duration)} trip! "
                    f"Recommended max is {max_km}km one way. "
                    f"Consider {'a full day or two-day' if dur_check == 'half' else 'a two-day'} trip "
                    f"or choose a closer destination."
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

    fee_info = ENTRY_FEES[matched_site]
    entry_price = fee_info["price"]
    entry_pupils = entry_price * pupils
    entry_teachers = entry_price * teachers
    entry_total = entry_pupils + entry_teachers

    # Food cost based on duration
    duration_key = duration.lower()
    if "two" in duration_key or "2" in duration_key:
        duration_key = "two"
        duration_label = "Two days"
        food_note = "€20/person (lunch + dinner + breakfast + snack)"
    elif "half" in duration_key:
        duration_key = "half"
        duration_label = "Half day"
        food_note = "€4/person (snack only)"
    else:
        duration_key = "full"
        duration_label = "Full day"
        food_note = "€8/person (lunch + snack)"

    food_per_person = FOOD_BY_DURATION.get(duration_key, 8.0)
    food_total = round(food_per_person * total_people, 2)

    # Accommodation for 2-day trips
    accommodation_total = None
    accommodation_line = ""
    if duration_key == "two":
        accommodation_total = round(ACCOMMODATION_PER_PERSON * total_people, 2)
        accommodation_line = (
            f"- Accommodation (1 night): €{accommodation_total} "
            f"(€{ACCOMMODATION_PER_PERSON}/person, hostel/budget hotel estimate)\n"
        )

    # Calculate totals
    extras = (accommodation_total or 0)
    if transport_total is not None:
        grand_total = round(transport_total + entry_total + food_total + extras, 2)
        per_pupil = round(
            (transport_total + entry_pupils + food_per_person * pupils +
             (ACCOMMODATION_PER_PERSON * pupils if duration_key == "two" else 0))
            / pupils, 2
        ) if pupils > 0 else 0
        transport_line = f"- Bus transport: €{transport_total} ({transport_note})"
        total_line = f"- TOTAL: €{grand_total}"
        per_pupil_line = f"- Estimated cost per pupil: €{per_pupil}"
    else:
        grand_total = round(entry_total + food_total + extras, 2)
        transport_line = f"- Bus transport: Unknown ({transport_note})"
        total_line = f"- TOTAL (excl. transport): €{grand_total}"
        per_pupil_line = (
            f"- Cost per pupil (excl. transport): "
            f"€{round(grand_total / pupils, 2)}"
        )

    return (
        f"Budget Estimate: {matched_site.title()}\n"
        f"Group: {pupils} pupils + {teachers} teachers "
        f"from {starting_city.title()} | {duration_label}\n"
        f"{'=' * 40}\n"
        f"{transport_line}\n"
        f"- Entry fees (pupils): €{entry_pupils} (€{entry_price} each)\n"
        f"- Entry fees (teachers): €{entry_teachers} (€{entry_price} each)\n"
        f"  ℹ️  {fee_info['note']}\n"
        f"  🌐 Official website: {fee_info['website']}\n"
        f"- Food & drinks: €{food_total} ({food_note})\n"
        f"{accommodation_line}"
        f"{'=' * 40}\n"
        f"{total_line}\n"
        f"{per_pupil_line}\n"
        f"\n⚠️ Prices are estimates. Always verify current "
        f"prices directly with the site before booking."
    )
