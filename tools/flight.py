from langchain_core.tools import tool

SITE_ITINERARIES = {
    "vilnius old town": {
        "7-10": [
            ("09:00", "Arrive at Cathedral Square - Iron Wolf legend storytelling"),
            ("09:45", "Walk to Gediminas Tower - climb up and draw the view"),
            ("11:00", "Explore Gediminas Avenue and spot architectural styles"),
            ("12:00", "Lunch break at Cathedral Square area"),
            ("13:00", "Visit Gate of Dawn - discuss religious tolerance"),
            ("13:45", "Walk through Old Town streets to St. Anne's Church"),
            ("14:30", "Free exploration time in supervised pairs"),
            ("15:00", "Gather at Cathedral Square - quiz and debrief"),
            ("15:30", "Depart"),
        ],
        "11-14": [
            ("09:00", "Arrive Cathedral Square - Baltic Way 1989 introduction"),
            ("09:30", "Gediminas Tower - Grand Duchy of Lithuania discussion"),
            ("10:30", "Jewish heritage walk - former ghetto area"),
            ("11:30", "Vilnius University courtyards - history of education"),
            ("12:30", "Lunch break"),
            ("13:30", "Gate of Dawn and religious diversity discussion"),
            ("14:15", "Soviet Vilnius - compare old photos with present"),
            ("15:00", "Užupis Republic - creative writing activity"),
            ("15:45", "Debrief and discussion"),
            ("16:00", "Depart"),
        ],
        "15-19": [
            ("09:00", "Arrive Cathedral Square - independence movement introduction"),
            ("09:30", "Gediminas Tower - Grand Duchy geopolitical analysis"),
            ("10:30", "Jewish heritage walk - Holocaust in Lithuania seminar"),
            ("11:30", "Vilnius University - academic history discussion"),
            ("12:30", "Lunch break"),
            ("13:30", "Soviet occupation sites - primary source analysis"),
            ("14:30", "Baltic Way 1989 - political significance debate"),
            ("15:30", "Academic debrief and essay planning"),
            ("16:00", "Depart"),
        ]
    },
    "trakai castle": {
        "7-10": [
            ("09:00", "Depart by bus"),
            ("09:40", "Arrive Trakai - walk to castle via wooden bridge"),
            ("10:00", "Castle exterior - draw defensive features"),
            ("10:45", "Castle museum - object handling session"),
            ("12:00", "Lunch - try Karaim kibinai pastries"),
            ("13:00", "Karaim settlement walk and kenesa visit"),
            ("14:00", "Lake activity - birdwatching or nature walk"),
            ("14:45", "Quiz and debrief by the lake"),
            ("15:15", "Bus back"),
        ],
        "11-14": [
            ("09:00", "Depart by bus"),
            ("09:40", "Arrive Trakai - Battle of Grunwald introduction"),
            ("10:00", "Castle analysis - defensive architecture activity"),
            ("11:00", "Castle museum - primary source analysis"),
            ("12:30", "Lunch break"),
            ("13:15", "Karaim culture research activity"),
            ("14:15", "Lake geography - why was this location chosen?"),
            ("15:00", "Group debrief and discussion"),
            ("15:30", "Bus back"),
        ],
        "15-19": [
            ("09:00", "Depart by bus"),
            ("09:40", "Arrive Trakai - medieval Lithuania geopolitics"),
            ("10:00", "Castle architecture - European comparative analysis"),
            ("11:00", "Castle museum - historiographical debate"),
            ("12:30", "Lunch break"),
            ("13:15", "Karaim minority - multiculturalism seminar"),
            ("14:15", "Battle of Grunwald - European significance debate"),
            ("15:00", "Academic debrief and essay planning"),
            ("15:30", "Bus back"),
        ]
    },
}

DEFAULT_ITINERARY = {
    "7-10": [
        ("09:00", "Arrive at site - introduction and safety briefing"),
        ("09:30", "Guided tour of main features"),
        ("11:00", "Hands-on activity or workshop"),
        ("12:30", "Lunch break"),
        ("13:30", "Exploration activity in supervised groups"),
        ("14:30", "Creative response - drawing, writing or quiz"),
        ("15:15", "Group debrief and discussion"),
        ("15:30", "Depart"),
    ],
    "11-14": [
        ("09:00", "Arrive at site - historical context introduction"),
        ("09:30", "Guided tour with research tasks"),
        ("11:00", "Primary source or fieldwork activity"),
        ("12:30", "Lunch break"),
        ("13:30", "Group research and discussion activity"),
        ("14:30", "Presentation or debate activity"),
        ("15:15", "Debrief and reflection"),
        ("15:30", "Depart"),
    ],
    "15-19": [
        ("09:00", "Arrive at site - academic context introduction"),
        ("09:30", "Independent research tour with guided questions"),
        ("11:00", "Primary source analysis or fieldwork"),
        ("12:30", "Lunch break"),
        ("13:30", "Group debate or seminar activity"),
        ("14:30", "Essay plan or presentation preparation"),
        ("15:15", "Academic debrief and discussion"),
        ("15:30", "Depart"),
    ],
}


@tool
def build_itinerary(site: str, age_group: str, duration_hours: int) -> str:
    """
    Build a day itinerary for a school excursion to a Lithuanian historical site.

    Args:
        site: The name of the historical site
        age_group: Age group - '7-10' for primary, '11-14' for middle school,
                   '15-19' for high school
        duration_hours: Duration of the visit in hours (typically 3-7)

    Returns:
        A structured day itinerary as a string
    """
    site_lower = site.lower().strip()

    age = age_group.strip()
    if age not in ["7-10", "11-14", "15-19"]:
        age = "11-14"

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
        "rundālės pils": "rundale palace",
        "siguldos pilis": "sigulda castle",
        "cėsio pilis": "cesis castle",
        "jūrmala": "jurmala",
        "talino senamiestis": "tallinn old town",
        "pärnu": "parnu",
        "haapsalu pilis": "haapsalu castle",
    }

    if site_lower in lt_to_en:
        site_lower = lt_to_en[site_lower]

    matched_site = None
    for key in SITE_ITINERARIES:
        if key in site_lower or site_lower in key:
            matched_site = key
            break

    if matched_site:
        if age in SITE_ITINERARIES[matched_site]:
            schedule = SITE_ITINERARIES[matched_site][age]
        else:
            schedule = DEFAULT_ITINERARY[age]
    else:
        schedule = DEFAULT_ITINERARY[age]
        matched_site = site

    result = (
        f"School Excursion Itinerary\n"
        f"Site: {matched_site.title()}\n"
        f"Age group: {age} years\n"
        f"Duration: approximately {duration_hours} hours\n"
        f"{'=' * 40}\n"
    )

    # Trim schedule to fit duration_hours
    # Each step is ~45-60 min on average; parse start times to cut off realistically
    trimmed_schedule = schedule
    if duration_hours <= 4 and len(schedule) > 5:
        trimmed_schedule = schedule[:5]
        # Replace last entry with departure
        trimmed_schedule = list(trimmed_schedule[:-1]) + [(trimmed_schedule[-1][0], "Depart")]
    elif duration_hours <= 6 and len(schedule) > 7:
        trimmed_schedule = schedule[:7]
        trimmed_schedule = list(trimmed_schedule[:-1]) + [(trimmed_schedule[-1][0], "Depart")]

    for time_slot, activity in trimmed_schedule:
        result += f"{time_slot}  {activity}\n"

    if duration_hours <= 4 and len(schedule) > 5:
        result += f"\n💡 Half-day note: Schedule shortened to fit {duration_hours}h. Some activities omitted.\n"

    result += (
        f"{'=' * 40}\n"
        f"Tips:\n"
        f"- Confirm opening times and book in advance\n"
        f"- Arrange toilet stops every 1.5-2 hours\n"
        f"- Bring first aid kit and emergency contacts\n"
        f"- Check weather forecast and dress appropriately\n"
    )

    return result