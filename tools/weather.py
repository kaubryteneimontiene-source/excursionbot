from langchain_core.tools import tool

SITE_ACTIVITIES = {
    "vilnius old town": {
        "7-10": [
            "Iron Wolf legend storytelling tour",
            "Find the miracle tile in Cathedral Square",
            "Spot different roof shapes and building styles",
            "Visit Gediminas Tower and draw the view",
            "Count how many church towers you can see",
        ],
        "11-14": [
            "Grand Duchy of Lithuania map activity",
            "Baltic Way 1989 - trace the human chain route",
            "Compare Soviet vs modern Vilnius using old photos",
            "Architectural styles treasure hunt",
            "Jewish heritage walking tour of former ghetto",
        ],
        "15-19": [
            "Baltic Way 1989 - primary source analysis and debate",
            "Soviet vs independent Lithuania - political history essay",
            "Jewish heritage of Vilnius - research and presentation",
            "Analysis of Lithuanian independence movement 1988-1991",
            "Urban planning - how cities reflect political history",
        ]
    },
    "trakai castle": {
        "7-10": [
            "Knight and castle role play activity",
            "Draw the castle from different angles",
            "Try traditional Karaim kibinai pastries",
            "Count the windows and towers",
            "Museum object handling session",
        ],
        "11-14": [
            "Castle defence analysis - why was the island location chosen?",
            "Battle of Grunwald 1410 - map and strategy activity",
            "Karaim culture research activity",
            "Primary source analysis in the museum",
            "Sketch and annotate castle defensive features",
        ],
        "15-19": [
            "Battle of Grunwald - European geopolitical consequences",
            "Karaim minority - multiculturalism in medieval Lithuania",
            "Comparative castle architecture - European context",
            "Vytautas the Great - leadership and legacy debate",
            "Medieval diplomacy - how did Lithuania expand its territory?",
        ]
    },
    "hill of crosses": {
        "7-10": [
            "Count and categorise different types of crosses",
            "Draw your own cross design",
            "Listen to stories of brave Lithuanians",
            "Quiet reflection and creative writing activity",
            "Photograph the most interesting crosses",
        ],
        "11-14": [
            "Soviet occupation discussion and debate",
            "Passive resistance - compare with other historical examples",
            "Personal testimony reading activity",
            "Creative writing - imagine rebuilding crosses at night",
            "Compare this memorial with others around the world",
        ],
        "15-19": [
            "Cold War context - Lithuania under Soviet occupation",
            "Passive resistance theory - compare Gandhi, Mandela, Lithuania",
            "Deportations to Siberia - statistical and personal analysis",
            "Religious freedom as human right - philosophical debate",
            "Memorial sites globally - comparative research project",
        ]
    },
    "curonian spit": {
        "7-10": [
            "Sand dune climbing on designated paths",
            "Birdwatching with identification sheets",
            "Beach nature collection and identification",
            "Draw the landscape from Parnidis Dune",
            "Measure dune heights and record data",
        ],
        "11-14": [
            "Dune formation geography fieldwork",
            "Ecosystem survey of lagoon vs Baltic Sea side",
            "Climate change impact assessment activity",
            "Reforestation history research",
            "Traditional fishing culture investigation",
        ],
        "15-19": [
            "Climate change threat analysis and mitigation strategies",
            "Ecosystem services - economic value of the Curonian Spit",
            "UNESCO World Heritage criteria - why was it listed?",
            "Sustainable tourism debate - balancing access and conservation",
            "Geological history since the Ice Age - research project",
        ]
    },
    "kaunas old town": {
        "7-10": [
            "Medieval castle exploration and drawing",
            "Town Hall Square market role play",
            "Architecture spotting on Freedom Avenue",
            "Story of Lithuanian independence",
            "Modernist building colour and shape hunt",
        ],
        "11-14": [
            "Interwar architecture analysis and photography",
            "Why was Kaunas the capital? Research activity",
            "Ninth Fort memorial visit with preparation",
            "Nation building discussion - how do countries create identity?",
            "Compare Kaunas modernist buildings with European examples",
        ],
        "15-19": [
            "Interwar Lithuania - democracy, authoritarianism and identity",
            "Holocaust in Lithuania - Ninth Fort historical analysis",
            "Modernist architecture as political statement - essay",
            "Kaunas as temporary capital - geopolitical context",
            "Lithuanian national identity formation 1918-1940",
        ]
    },
    "kernave": {
        "7-10": [
            "Archaeology dig simulation activity",
            "Handle replica ancient objects",
            "Climb the hillfort mounds",
            "Draw what you think the ancient town looked like",
            "Museum object detective activity",
        ],
        "11-14": [
            "Archaeological stratigraphy activity",
            "Early Lithuanian statehood evidence analysis",
            "Teutonic Knights threat - map and strategy",
            "Dating methods in archaeology",
            "Fieldwork sketching of hillforts",
        ],
        "15-19": [
            "Archaeological methodology - how do we reconstruct the past?",
            "Early Lithuanian state formation - historiographical debate",
            "Teutonic Knights - crusading ideology and geopolitics",
            "Comparative archaeology - Baltic vs European Iron Age",
            "Primary source analysis - medieval chronicles on Lithuania",
        ]
    },
    "museum of occupations": {
        "7-10": [
            "Age-appropriate deportation stories",
            "What is freedom? Discussion activity",
            "Brave Lithuanians stories",
            "Note: Consult museum staff for suitable sections",
        ],
        "11-14": [
            "KGB cells visit with reflection activity",
            "Deportation testimony analysis",
            "Forest Brothers resistance research",
            "Sąjūdis and the road to independence",
            "Human rights discussion - then and now",
        ],
        "15-19": [
            "Soviet totalitarianism - ideology, methods and legacy",
            "KGB operations - surveillance state analysis",
            "Armed resistance vs passive resistance - ethical debate",
            "Comparative occupation - Nazi vs Soviet methods",
            "Transitional justice - how Lithuania dealt with its past",
        ]
    },
    "palanga amber museum": {
        "7-10": [
            "Spot insects and plants in amber specimens",
            "Amber sorting by colour and transparency",
            "Static electricity demonstration with amber",
            "Amber jewellery making workshop",
            "Walk through the botanical garden to the beach",
        ],
        "11-14": [
            "Geological timeline of amber formation",
            "Amber Road prehistoric trade network mapping",
            "Ecosystem reconstruction from amber inclusions",
            "Baltic amber in the ancient world research",
            "Amber chemistry - why does it preserve so well?",
        ],
        "15-19": [
            "Geological time and amber formation - deep time concept",
            "Prehistoric trade networks - economic history analysis",
            "Amber inclusions as scientific evidence - research methods",
            "Baltic amber in ancient civilisations - cross-cultural connections",
            "The Amber Room - art, war and cultural heritage theft",
        ]
    },
}


@tool
def suggest_activities(site: str, age_group: str) -> str:
    """
    Suggest age-appropriate educational activities for a school excursion.

    Args:
        site: The name of the historical site
        age_group: Age group - '7-10' for primary, '11-14' for middle school,
                   '15-19' for high school

    Returns:
        A list of suggested activities as a string
    """
    site_lower = site.lower().strip()

    matched_site = None
    for key in SITE_ACTIVITIES:
        if key in site_lower or site_lower in key:
            matched_site = key
            break

    if not matched_site:
        available = ", ".join(SITE_ACTIVITIES.keys())
        return (
            f"Sorry, I don't have activity data for '{site}'. "
            f"Available sites: {available}"
        )

    age = age_group.strip()
    if age not in ["7-10", "11-14", "15-19"]:
        age = "11-14"

    activities = SITE_ACTIVITIES[matched_site][age]

    result = (
        f"Suggested activities at {matched_site.title()} "
        f"for ages {age}:\n"
    )
    for i, activity in enumerate(activities, 1):
        result += f"{i}. {activity}\n"

    return result