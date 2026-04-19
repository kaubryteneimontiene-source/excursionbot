from rag_evaluator import evaluate_rag_response, format_score_emoji
import json
import os
import time
import streamlit as st
from datetime import datetime
from agent import initialize, chat
from pdf_export import generate_pdf
from cache import get_cache_stats, clear_cache

# Page configuration
st.set_page_config(
    page_title="ExcursionBot 🏰",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS — modern dark-accent design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #00473E 0%, #00695C 50%, #2E7D32 100%);
        padding: 1rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,71,62,0.2);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 200px;
        height: 200px;
        background: rgba(255,255,255,0.05);
        border-radius: 50%;
    }
    .main-header h1 { font-size: 1.8rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .main-header p { font-size: 0.9rem; opacity: 0.85; margin: 0.2rem 0 0 0; font-weight: 400; }

    .feature-card {
        background: white;
        border: 1px solid #E0F2F1;
        border-radius: 10px;
        padding: 0.55rem 0.9rem;
        margin-bottom: 0.4rem;
        border-left: 3px solid #00695C;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .feature-card h4 { margin: 0; color: #00473E; font-size: 0.85rem; font-weight: 600; white-space: nowrap; }
    .feature-card p { margin: 0; color: #607D8B; font-size: 0.78rem; }

    .dest-badge {
        display: inline-block;
        background: #E0F2F1;
        border: 1px solid #80CBC4;
        color: #00473E;
        padding: 0.25rem 0.7rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.2rem;
        font-weight: 500;
    }

    .stat-card {
        background: white;
        border: 1px solid #E0F2F1;
        border-radius: 12px;
        padding: 0.9rem;
        text-align: center;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .stat-card .stat-number { font-size: 1.5rem; font-weight: 700; color: #00695C; }
    .stat-card .stat-label { font-size: 0.72rem; color: #90A4AE; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.5px; }

    .example-q {
        background: #F9FFFE;
        border: 1px solid #E0F2F1;
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.3rem 0;
        font-size: 0.84rem;
        color: #37474F;
    }

    .footer {
        text-align: center;
        color: #B0BEC5;
        font-size: 0.72rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #E0F2F1;
    }

    [data-testid="stSidebar"] {
        background: #FAFFFE !important;
        border-right: 1px solid #E0F2F1 !important;
    }
    hr { border-color: #E0F2F1 !important; }

    .stChatFloatingInputContainer {
        bottom: 0;
        position: sticky !important;
    }
</style>
""", unsafe_allow_html=True)


# ---- LOAD SITES FROM CONFIG ----
def load_sites_from_config():
    """Load site list from config.json."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        sites_en = []
        sites_lt = []
        emoji_map = {
            "vilnius old town": "🏛️",
            "trakai castle": "🏰",
            "hill of crosses": "✝️",
            "curonian spit": "🌊",
            "kaunas old town": "🏙️",
            "kernave": "⛏️",
            "museum of occupations": "🔒",
            "palanga amber museum": "🟡",
            "riga old town": "🇱🇻",
            "rundale palace": "🏯",
            "sigulda castle": "🌲",
            "cesis castle": "🏰",
            "jurmala": "🏖️",
            "tallinn old town": "🇪🇪",
            "tartu": "🎓",
            "parnu": "🌅",
            "haapsalu castle": "🏰",
        }
        lt_names = {
            "vilnius old town": "Vilniaus senamiestis",
            "trakai castle": "Trakų pilis",
            "hill of crosses": "Kryžių kalnas",
            "curonian spit": "Kuršių nerija",
            "kaunas old town": "Kauno senamiestis",
            "kernave": "Kernavė",
            "museum of occupations": "Okupacijų muziejus",
            "palanga amber museum": "Palangos gintaro muziejus",
            "riga old town": "Rygos senamiestis",
            "rundale palace": "Rundālės pils",
            "sigulda castle": "Siguldos pilis",
            "cesis castle": "Cėsio pilis",
            "jurmala": "Jūrmala",
            "tallinn old town": "Talino senamiestis",
            "tartu": "Tartu",
            "parnu": "Pärnu",
            "haapsalu castle": "Haapsalu pilis",
        }
        for key in config["entry_fees"]:
            emoji = emoji_map.get(key, "🏛️")
            en_name = key.title()
            lt_name = lt_names.get(key, en_name)
            sites_en.append(f"{emoji} {en_name}")
            sites_lt.append(f"{emoji} {lt_name}")
        # Add "Other" option at the end
        sites_en.append("✏️ Other (type below)")
        sites_lt.append("✏️ Kita (įrašykite žemiau)")
        return sites_en, sites_lt
    except Exception:
        # Fallback if config not found
        sites_en = [
            "🏛️ Vilnius Old Town", "🏰 Trakai Castle",
            "✝️ Hill of Crosses", "🌊 Curonian Spit",
            "🏙️ Kaunas Old Town", "⛏️ Kernavė",
            "🔒 Museum of Occupations", "🟡 Palanga Amber Museum",
            "✏️ Other (type below)",
        ]
        sites_lt = [
            "🏛️ Vilniaus senamiestis", "🏰 Trakų pilis",
            "✝️ Kryžių kalnas", "🌊 Kuršių nerija",
            "🏙️ Kauno senamiestis", "⛏️ Kernavė",
            "🔒 Okupacijų muziejus", "🟡 Palangos gintaro muziejus",
            "✏️ Kita (įrašykite žemiau)",
        ]
        return sites_en, sites_lt


SITES_EN, SITES_LT = load_sites_from_config()

# ---- INITIALIZE AGENT ----
if "initialized" not in st.session_state:
    with st.spinner("Starting ExcursionBot... 🏰"):
        try:
            initialize()
            st.session_state.initialized = True
        except Exception as e:
            st.error(f"⚠️ Failed to start ExcursionBot: {str(e)}")
            st.stop()

# ---- SESSION STATE ----
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "total_prompt_tokens" not in st.session_state:
    st.session_state.total_prompt_tokens = 0
if "total_completion_tokens" not in st.session_state:
    st.session_state.total_completion_tokens = 0
if "total_messages" not in st.session_state:
    st.session_state.total_messages = 0
if "message_timestamps" not in st.session_state:
    st.session_state.message_timestamps = []
if "language" not in st.session_state:
    st.session_state.language = "English"
if "quick_action_input" not in st.session_state:
    st.session_state.quick_action_input = ""
if "last_response_data" not in st.session_state:
    st.session_state.last_response_data = None
if "custom_fees" not in st.session_state:
    # Load default fees from config as starting point
    try:
        _cfg = json.load(open(os.path.join(os.path.dirname(__file__), "config.json"), encoding="utf-8"))
        st.session_state.custom_fees = {k: v["price"] for k, v in _cfg["entry_fees"].items()}
    except Exception:
        st.session_state.custom_fees = {}


# ---- UI TRANSLATIONS ----
UI_TEXT = {
    "English": {
        "title": "🏰 ExcursionBot",
        "subtitle": "AI-powered school excursion planner for Baltic historical sites",
        "welcome": "### 👋 Hello, Teacher! How can I help you plan today?",
        "chat_input": "Ask me about planning a school excursion... 🏰",
        "thinking": "Thinking... 🏰",
        "tools_used": "🔧 Tools used",
        "sources_used": "📚 Sources used",
        "rag_process": "🔍 RAG Process - Retrieved chunks",
        "rag_note": "*These are the knowledge base chunks used to answer your question:*",
        "export_txt": "📥 Export as TXT",
        "export_pdf": "📄 Export as PDF",
        "clear": "🗑️ Clear Conversation",
        "clear_cache": "🗑️ Clear Cache",
        "available_sites": "**🏛️ Available Sites**",
        "try_asking": "**💡 Try asking...**",
        "session_stats": "**📊 Session Stats**",
        "messages": "Messages",
        "tokens": "Tokens",
        "cost": "Estimated API Cost",
        "cached": "Cached Responses",
        "how_to": "❓ How to use ExcursionBot",
        "how_to_content": """
**Step 1 — Describe your excursion:**
Tell me the site, grade, number of pupils and where you're travelling from.

*Example: "I want to plan a trip to Trakai Castle for 6th graders, 25 pupils, from Kaunas"*

---

**Step 2 — Get your plan:**
I'll automatically generate:
- 🗓️ A day itinerary with timings
- 💰 A group budget estimate
- 🎯 Age-appropriate activities

---

**Step 3 — Explore the details:**
After each answer check:
- 🔧 **Tools used** — what was calculated
- 📚 **Sources used** — which site guide was referenced
- 🔍 **RAG Process** — actual knowledge chunks retrieved

---

**Step 4 — Export your plan:**
Click **📥 Export Plan** to download the full conversation.

---

**Available sites:**
Lithuania: Vilnius Old Town, Trakai Castle, Hill of Crosses,
Curonian Spit, Kaunas Old Town, Kernavė,
Museum of Occupations, Palanga Amber Museum

Latvia: Riga Old Town, Rundale Palace, Sigulda Castle,
Cēsis Castle, Jūrmala

Estonia: Tallinn Old Town, Tartu, Pärnu, Haapsalu Castle

Or type any Baltic site in the "Other" field!

---

**Age groups supported:**
- 🟢 Primary: grades 1-4 (ages 7-10)
- 🔵 Middle school: grades 5-8 (ages 11-14)
- 🟣 High school: grades 9-12 (ages 15-19)
        """,
        "warning_short": "⚠️ Please enter a valid question.",
        "warning_long": "⚠️ Please keep your message under 500 characters.",
        "rate_limit": "⏳ You've sent too many messages. Please wait {} seconds before sending again.",
        "card1_title": "🏛️ Site Information",
        "card1_text": "Guides for Baltic historical and cultural sites across Lithuania, Latvia and Estonia",
        "card2_title": "💰 Group Budget Calculator",
        "card2_text": "Estimate total costs for your group including transport, entry fees and food",
        "card3_title": "🎯 Age-Appropriate Activities",
        "card3_text": "Tailored activity suggestions for primary, middle school and high school pupils",
        "card4_title": "🗓️ Itinerary Builder",
        "card4_text": "Generate a structured day plan with timings for your school excursion",
        "card5_title": "⚠️ Safety Guidance",
        "card5_text": "Site-specific safety advice and behaviour guidelines for school groups",
        "card6_title": "📚 Curriculum Links",
        "card6_text": "Educational themes and learning objectives for each site by age group",
        "start_prompt": "⬇️ Type your question below to get started!",
        "footer": "Built with LangChain + Streamlit<br>Powered by OpenAI GPT-4o-mini",
        "site_guide": "site guide",
        "chunk": "Chunk",
        "examples": [
            "🗓️ Plan a day trip to Trakai for 6th graders",
            "💰 Budget for 25 pupils to Hill of Crosses",
            "🎯 Activities at Kernavė for ages 7-10",
            "📚 What can pupils learn at Museum of Occupations?",
            "🇱🇻 Plan excursion to Riga Old Town",
            "🇪🇪 Is Tallinn Old Town suitable for primary school?",
        ],
        "sites": SITES_EN,
        "quick_actions": [
            ("🗓️ Plan Excursion", "I want to plan a school excursion. Can you help me?"),
            ("💰 Calculate Budget", "Calculate the budget for my school group excursion."),
            ("🎯 Suggest Activities", "Suggest age-appropriate activities for my school group."),
            ("🏛️ Site Guide", "Tell me about the best Baltic historical sites for school visits."),
            ("⚠️ Safety Tips", "What safety tips should I know for school excursions?"),
        ],
        "tab_chat": "💬 Chat",
        "tab_planner": "📋 Trip Planner",
        "form_title": "### 📋 Plan Your Excursion",
        "form_subtitle": "Fill in the details and I'll generate a complete excursion plan!",
        "form_destination": "🏛️ Destination",
        "form_destination_other": "✏️ Enter destination name:",
        "form_destination_other_placeholder": "e.g. Cēsis Castle, Haapsalu, Tartu...",
        "form_grade": "🎓 School Grade",
        "form_pupils": "👥 Number of Pupils",
        "form_teachers": "👩‍🏫 Number of Teachers",
        "form_city": "📍 Travelling From (city or village)",
        "form_duration": "⏱️ Trip Duration",
        "form_duration_options": ["🌅 Half day (4 hours)", "☀️ Full day (8 hours)", "🌙 Two days"],
        "form_season": "🌤️ Season of Visit",
        "form_season_options": ["🌸 Spring", "☀️ Summer", "🍂 Autumn", "❄️ Winter"],
        "form_extra_site": "➕ Add a Second Site (optional)",
        "form_extra_site_none": "None",
        "form_button": "🗓️ Generate Excursion Plan",
        "form_error": "⚠️ Please fill in all fields before generating a plan.",
        "form_bus_cost": "🚌 Bus cost per km",
        "form_bus_cost_help": "Adjust based on your school's transport quote",
        "form_error_other": "⚠️ Please type a destination name in the field above.",
        "error_msg": "⚠️ Sorry, I ran into an issue processing your request. Please try again.",
        "cleared_cache": "Cleared {} cached responses",
        "plan_title": "### 📋 Your Excursion Plan",
    },
    "Lithuanian": {
        "title": "🏰 ExcursionBot",
        "subtitle": "DI pagalbininkas mokyklinių ekskursijų planavimui Baltijos istorinėse vietose",
        "welcome": "### 👋 Sveiki, mokytojau! Kaip galiu padėti šiandien?",
        "chat_input": "Klauskite apie mokyklinės ekskursijos planavimą... 🏰",
        "thinking": "Galvoju... 🏰",
        "tools_used": "🔧 Naudoti įrankiai",
        "sources_used": "📚 Naudoti šaltiniai",
        "rag_process": "🔍 RAG procesas - rasti fragmentai",
        "rag_note": "*Tai žinių bazės fragmentai, naudoti atsakymui:*",
        "export_txt": "📥 Eksportuoti kaip TXT",
        "export_pdf": "📄 Eksportuoti kaip PDF",
        "clear": "🗑️ Išvalyti pokalbį",
        "clear_cache": "🗑️ Išvalyti talpyklą",
        "available_sites": "**🏛️ Galimos vietovės**",
        "try_asking": "**💡 Pabandykite klausti...**",
        "session_stats": "**📊 Sesijos statistika**",
        "messages": "Žinutės",
        "tokens": "Tokenai",
        "cost": "Numatoma API kaina",
        "cached": "Talpykloje",
        "how_to": "❓ Kaip naudotis ExcursionBot",
        "how_to_content": """
**1 žingsnis — Aprašykite ekskursiją:**
Nurodykite vietovę, klasę, mokinių skaičių ir išvykimo miestą.

*Pavyzdys: "Noriu planuoti išvyką į Trakų pilį 6 klasei, 25 mokiniams, iš Kauno"*

---

**2 žingsnis — Gaukite planą:**
Automatiškai sugeneruosiu:
- 🗓️ Dienos maršrutą su laiko grafiku
- 💰 Grupės biudžeto įvertinimą
- 🎯 Amžiui tinkamas veiklas

---

**3 žingsnis — Išnagrinėkite detales:**
Po kiekvieno atsakymo patikrinkite:
- 🔧 **Naudoti įrankiai** — kas buvo apskaičiuota
- 📚 **Naudoti šaltiniai** — kuris vietovės gidas naudotas
- 🔍 **RAG procesas** — rasti žinių bazės fragmentai

---

**4 žingsnis — Eksportuokite planą:**
Spauskite **📥 Eksportuoti** norėdami atsisiųsti pokalbį.

---

**Galimos vietovės:**
Lietuva: Vilniaus senamiestis, Trakų pilis, Kryžių kalnas,
Kuršių nerija, Kauno senamiestis, Kernavė,
Okupacijų muziejus, Palangos gintaro muziejus

Latvija: Rygos senamiestis, Rundālės pils, Siguldos pilis,
Cėsio pilis, Jūrmala

Estija: Talino senamiestis, Tartu, Pärnu, Haapsalu pilis

Arba įrašykite bet kurią Baltijos vietovę laukelyje „Kita"!

---

**Palaikomos amžiaus grupės:**
- 🟢 Pradinė mokykla: 1-4 klasė (7-10 metų)
- 🔵 Pagrindinė mokykla: 5-8 klasė (11-14 metų)
- 🟣 Vidurinė mokykla: 9-12 klasė (15-19 metų)
        """,
        "warning_short": "⚠️ Įveskite tinkamą klausimą.",
        "warning_long": "⚠️ Žinutė negali būti ilgesnė nei 500 simbolių.",
        "rate_limit": "⏳ Išsiuntėte per daug žinučių. Palaukite {} sekundes.",
        "card1_title": "🏛️ Vietovių informacija",
        "card1_text": "Gidai apie Baltijos istorines ir kultūrines vietas Lietuvoje, Latvijoje ir Estijoje",
        "card2_title": "💰 Grupės biudžeto skaičiuoklė",
        "card2_text": "Įvertinkite grupės išlaidas: transportas, įėjimo mokesčiai ir maistas",
        "card3_title": "🎯 Amžiui tinkamos veiklos",
        "card3_text": "Veiklų pasiūlymai pradinukams, pagrindinės ir vidurinės mokyklos mokiniams",
        "card4_title": "🗓️ Maršruto sudarytojas",
        "card4_text": "Sukurkite struktūruotą dienos planą su laiko grafiku",
        "card5_title": "⚠️ Saugos rekomendacijos",
        "card5_text": "Vietovei būdingi saugos patarimai ir elgesio gairės",
        "card6_title": "📚 Ryšys su ugdymo programa",
        "card6_text": "Edukacinės temos ir mokymosi tikslai pagal amžiaus grupę",
        "start_prompt": "⬇️ Įveskite klausimą žemiau!",
        "footer": "Sukurta su LangChain + Streamlit<br>Veikia OpenAI GPT-4o-mini pagrindu",
        "site_guide": "vietovės gidas",
        "chunk": "Fragmentas",
        "examples": [
            "🗓️ Planuoti išvyką į Trakus 6 klasei",
            "💰 Biudžetas 25 mokiniams į Kryžių kalną",
            "🎯 Veiklos Kernavėje 7-10 metų vaikams",
            "📚 Ko mokiniai gali išmokti Okupacijų muziejuje?",
            "🇱🇻 Planuoti ekskursiją į Rygos senamiestį",
            "🇪🇪 Ar Talino senamiestis tinka pradinukams?",
        ],
        "sites": SITES_LT,
        "quick_actions": [
            ("🗓️ Planuoti ekskursiją", "Noriu planuoti mokyklinę ekskursiją. Ar galite padėti?"),
            ("💰 Skaičiuoti biudžetą", "Apskaičiuokite biudžetą mano mokyklos grupės ekskursijai."),
            ("🎯 Veiklų pasiūlymai", "Pasiūlykite amžiui tinkamas veiklas mano mokyklos grupei."),
            ("🏛️ Vietovių gidas", "Papasakokite apie geriausias Baltijos istorines vietas mokyklinėms išvykoms."),
            ("⚠️ Saugos patarimai", "Kokius saugos patarimus turėčiau žinoti mokyklinėms ekskursijoms?"),
        ],
        "tab_chat": "💬 Pokalbis",
        "tab_planner": "📋 Ekskursijos planuotojas",
        "form_title": "### 📋 Planuokite ekskursiją",
        "form_subtitle": "Užpildykite detales ir sugeneruosiu išsamų ekskursijos planą!",
        "form_destination": "🏛️ Vietovė",
        "form_destination_other": "✏️ Įrašykite vietovę:",
        "form_destination_other_placeholder": "pvz. Cėsio pilis, Haapsalu, Tartu...",
        "form_grade": "🎓 Mokyklos klasė",
        "form_pupils": "👥 Mokinių skaičius",
        "form_teachers": "👩‍🏫 Mokytojų skaičius",
        "form_city": "📍 Išvykimo miestas ar kaimas",
        "form_duration": "⏱️ Kelionės trukmė",
        "form_duration_options": ["🌅 Pusė dienos (4 val.)", "☀️ Visa diena (8 val.)", "🌙 Dvi dienos"],
        "form_season": "🌤️ Metų laikas",
        "form_season_options": ["🌸 Pavasaris", "☀️ Vasara", "🍂 Ruduo", "❄️ Žiema"],
        "form_extra_site": "➕ Pridėti antrą vietovę (neprivaloma)",
        "form_extra_site_none": "Nėra",
        "form_button": "🗓️ Generuoti ekskursijos planą",
        "form_error": "⚠️ Prieš generuodami planą užpildykite visus laukus.",
        "form_bus_cost": "🚌 Autobuso kaina už km",
        "form_bus_cost_help": "Koreguokite pagal jūsų mokyklos transporto pasiūlymą",
        "form_error_other": "⚠️ Įrašykite vietovės pavadinimą laukelyje aukščiau.",
        "error_msg": "⚠️ Atsiprašau, įvyko klaida. Bandykite dar kartą.",
        "cleared_cache": "Išvalyta {} talpykloje esančių atsakymų",
        "plan_title": "### 📋 Jūsų ekskursijos planas",
    }
}


# ---- RATE LIMITING ----
def check_rate_limit() -> tuple[bool, int]:
    now = time.time()
    window = 60
    max_messages = 10

    st.session_state.message_timestamps = [
        ts for ts in st.session_state.message_timestamps
        if now - ts < window
    ]

    if len(st.session_state.message_timestamps) >= max_messages:
        oldest = st.session_state.message_timestamps[0]
        seconds_until_reset = int(window - (now - oldest))
        return False, seconds_until_reset

    return True, 0


# ---- EXPORT FUNCTION ----
def export_chat() -> str:
    if not st.session_state.chat_history:
        return "No conversation to export."
    lines = []
    lines.append("=" * 50)
    lines.append("ExcursionBot Conversation Export")
    lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 50)
    lines.append("")
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            lines.append(f"TEACHER: {message['content']}")
        else:
            lines.append(f"EXCURSIONBOT: {message['content']}")
        lines.append("")
    total = (
        st.session_state.total_prompt_tokens +
        st.session_state.total_completion_tokens
    )
    lines.append("=" * 50)
    lines.append(f"Total messages: {st.session_state.total_messages}")
    lines.append(f"Total tokens used: {total}")
    lines.append("=" * 50)
    return "\n".join(lines)



# ---- FEEDBACK SYSTEM ----
import json as _json

def save_feedback(question: str, answer: str, rating: str):
    """Save user feedback to feedback.json for future analysis."""
    feedback_path = "feedback.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "rating": rating,
        "question": question[:200],
        "answer": answer[:500],
    }
    existing = []
    try:
        with open(feedback_path, "r", encoding="utf-8") as f:
            existing = _json.load(f)
    except Exception:
        pass
    existing.append(entry)
    try:
        with open(feedback_path, "w", encoding="utf-8") as f:
            _json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def show_feedback_buttons(message_idx: int, question: str, answer: str, t: dict):
    """Show thumbs up/down feedback buttons after a response."""
    feedback_key = f"feedback_{message_idx}"
    if st.session_state.get(feedback_key):
        rating = st.session_state[feedback_key]
        if rating == "👍":
            st.caption("✅ Thanks for the feedback!")
        else:
            st.caption("📝 Feedback noted — we'll use this to improve.")
        return

    st.caption("Was this helpful?" if st.session_state.language == "English" else "Ar tai buvo naudinga?")
    col_a, col_b, col_c = st.columns([1, 1, 8])
    with col_a:
        if st.button("👍", key=f"up_{message_idx}", help="Helpful"):
            st.session_state[feedback_key] = "👍"
            save_feedback(question, answer, "positive")
            st.rerun()
    with col_b:
        if st.button("👎", key=f"dn_{message_idx}", help="Not helpful"):
            st.session_state[feedback_key] = "👎"
            save_feedback(question, answer, "negative")
            st.rerun()


# ---- HELPER: SHOW EXPANDERS ----
def show_expanders(data: dict, t: dict):
    """Show tools, sources and RAG expanders."""
    if not data:
        return

    if data.get("tools_used"):
        with st.expander(t["tools_used"]):
            tool_names = {
                "calculate_group_budget": "💰 Budget Calculator",
                "suggest_activities": "🎯 Activity Suggester",
                "build_itinerary": "🗓️ Itinerary Builder",
                "search_site_wikipedia": "🌐 Wikipedia Search",
            }
            for tool in data["tools_used"]:
                display_name = tool_names.get(tool["name"], tool["name"])
                st.markdown(f"**{display_name}**")
                for key, value in tool["args"].items():
                    st.markdown(f"- {key}: `{value}`")

    if data.get("sources"):
        with st.expander(t["sources_used"]):
            for source in data["sources"]:
                st.markdown(f"- 📄 **{source}** {t['site_guide']}")

    if data.get("chunks") and data.get("sources"):
        with st.expander(t["rag_process"]):
            st.markdown(t["rag_note"])
            for i, chunk in enumerate(data["chunks"], 1):
                st.markdown(f"**{t['chunk']} {i}:**")
                st.info(chunk[:300] + "..." if len(chunk) > 300 else chunk)

            st.divider()
            st.markdown("**📊 RAG Quality Evaluation**")
            with st.spinner("Evaluating..."):
                eval_results = evaluate_rag_response(
                    question=data["question"],
                    context_chunks=data["chunks"],
                    answer=data["answer"]
                )
            col1, col2, col3 = st.columns(3)
            with col1:
                score = eval_results["context_relevance"]
                st.metric(
                    f"{format_score_emoji(score)} Context Relevance",
                    f"{score:.0%}"
                )
            with col2:
                score = eval_results["answer_faithfulness"]
                st.metric(
                    f"{format_score_emoji(score)} Faithfulness",
                    f"{score:.0%}"
                )
            with col3:
                score = eval_results["answer_relevance"]
                st.metric(
                    f"{format_score_emoji(score)} Answer Relevance",
                    f"{score:.0%}"
                )
            overall = eval_results["overall"]
            st.markdown(
                f"**Overall RAG Score: {format_score_emoji(overall)} {overall:.0%}**"
            )


# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("""
        <div style='text-align:center; padding: 1rem 0 0.5rem 0;'>
            <span style='font-size: 3rem;'>🏰</span>
            <h2 style='margin: 0.3rem 0 0 0; color: #2E7D32;'>ExcursionBot</h2>
            <p style='color: #888; font-size: 0.85rem; margin: 0;'>
                AI school excursion planner
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("**🌐 Language / Kalba**")
    language = st.radio(
        label="",
        options=["🇬🇧 English", "🇱🇹 Lithuanian"],
        horizontal=True,
        key="lang_radio"
    )
    st.session_state.language = (
        "Lithuanian" if "Lithuanian" in language else "English"
    )
    t = UI_TEXT[st.session_state.language]

    st.divider()

    st.markdown(t["session_stats"])
    cache_stats = get_cache_stats()
    total_tokens = (
        st.session_state.total_prompt_tokens +
        st.session_state.total_completion_tokens
    )
    estimated_cost = (
        (st.session_state.total_prompt_tokens / 1000 * 0.00015) +
        (st.session_state.total_completion_tokens / 1000 * 0.0006)
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{st.session_state.total_messages}</div>
                <div class='stat-label'>{t['messages']}</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{total_tokens}</div>
                <div class='stat-label'>{t['tokens']}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-number'>${estimated_cost:.4f}</div>
            <div class='stat-label'>{t['cost']}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-number'>{cache_stats['valid']}</div>
            <div class='stat-label'>{t['cached']}</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown(t["available_sites"])
    badges_html = "".join(
        [f"<span class='dest-badge'>{s}</span>" for s in t["sites"]
         if "Other" not in s and "Kita" not in s]
    )
    st.markdown(badges_html, unsafe_allow_html=True)
    st.divider()

    st.markdown(t["try_asking"])
    for example in t["examples"]:
        st.markdown(
            f"<div class='example-q'>{example}</div>",
            unsafe_allow_html=True
        )

    st.divider()

    with st.expander(t["how_to"]):
        st.markdown(t["how_to_content"])

    st.divider()

    # ---- ENTRY FEES EDITOR ----
    fees_title = "🎫 Entry Fees" if st.session_state.language == "English" else "🎫 Bilietų kainos"
    with st.expander(fees_title):
        st.caption(
            "⚠️ Prices are estimates. You can update them for this session only — changes reset on page refresh."
            if st.session_state.language == "English" else
            "⚠️ Kainos orientacinės. Galite atnaujinti šiai sesijai — po perkrovimo grįš originalios."
        )
        updated_fees = {}
        for site_key, current_price in st.session_state.custom_fees.items():
            updated_fees[site_key] = st.number_input(
                f"{site_key.title()} (€)",
                min_value=0.0,
                max_value=100.0,
                value=float(current_price),
                step=0.5,
                format="%.2f",
                key=f"fee_{site_key}"
            )
        if st.button("✅ Update Prices" if st.session_state.language == "English" else "✅ Atnaujinti kainas", use_container_width=True):
            st.session_state.custom_fees = updated_fees
            st.success("✅ Prices updated for this session!" if st.session_state.language == "English" else "✅ Kainos atnaujintos šiai sesijai!")

    st.divider()


    upload_title = "📎 Upload Document" if st.session_state.language == "English" else "📎 Įkelti dokumentą"
    upload_help = "Add a PDF or TXT to the knowledge base" if st.session_state.language == "English" else "Pridėti PDF arba TXT į žinių bazę"

    st.markdown(f"**{upload_title}**")
    st.caption(upload_help)

    uploaded_file = st.file_uploader(
        label="",
        type=["pdf", "txt"],
        key="doc_uploader"
    )

    if uploaded_file is not None:
        from document_processor import process_uploaded_file
        from agent import reload_retriever_after_upload
        with st.spinner("Processing..."):
            chunks_added, status = process_uploaded_file(uploaded_file)
        if chunks_added > 0:
            st.success(status)
            reload_retriever_after_upload()
            st.info("✅ Ready! Ask about this document in chat." if st.session_state.language == "English" else "✅ Paruošta! Klauskite apie šį dokumentą pokalbyje.")
        else:
            st.error(status)

    st.divider()

    if st.session_state.chat_history:
        export_text = export_chat()
        st.download_button(
            label=t["export_txt"],
            data=export_text,
            file_name=f"excursion_plan_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.markdown("<div style='margin-top: 0.3rem;'></div>",
                    unsafe_allow_html=True)

        total_tokens_pdf = (
            st.session_state.total_prompt_tokens +
            st.session_state.total_completion_tokens
        )
        pdf_bytes = generate_pdf(
            st.session_state.chat_history,
            st.session_state.total_messages,
            total_tokens_pdf
        )
        st.download_button(
            label=t["export_pdf"],
            data=pdf_bytes,
            file_name=f"excursion_plan_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.markdown("<div style='margin-top: 0.5rem;'></div>",
                    unsafe_allow_html=True)

    if st.button(t["clear"], use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.total_prompt_tokens = 0
        st.session_state.total_completion_tokens = 0
        st.session_state.total_messages = 0
        st.session_state.message_timestamps = []
        st.session_state.last_response_data = None
        st.rerun()

    if st.button(t["clear_cache"], use_container_width=True):
        cleared = clear_cache()
        st.success(t["cleared_cache"].format(cleared))

    st.markdown(f"""
        <div class='footer'>
            {t['footer']}
        </div>
    """, unsafe_allow_html=True)


# ---- MAIN AREA ----
t = UI_TEXT[st.session_state.language]

st.markdown(f"""
    <div class='main-header'>
        <h1>{t['title']}</h1>
        <p>{t['subtitle']}</p>
    </div>
""", unsafe_allow_html=True)

# ---- TABS ----
tab1, tab2 = st.tabs([t["tab_chat"], t["tab_planner"]])

with tab1:
    # ---- QUICK ACTIONS ----
    st.markdown("**⚡ Quick Actions:**")
    qa_cols = st.columns(5)
    for i, (label, prompt) in enumerate(t["quick_actions"]):
        with qa_cols[i]:
            if st.button(label, use_container_width=True, key=f"qa_{i}"):
                st.session_state.quick_action_input = prompt

    st.divider()

    # Welcome screen
    if not st.session_state.chat_history:
        st.markdown(t["welcome"])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class='feature-card'>
                    <h4>{t['card1_title']}</h4><p>{t['card1_text']}</p>
                </div>
                <div class='feature-card'>
                    <h4>{t['card2_title']}</h4><p>{t['card2_text']}</p>
                </div>
                <div class='feature-card'>
                    <h4>{t['card3_title']}</h4><p>{t['card3_text']}</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class='feature-card'>
                    <h4>{t['card4_title']}</h4><p>{t['card4_text']}</p>
                </div>
                <div class='feature-card'>
                    <h4>{t['card5_title']}</h4><p>{t['card5_text']}</p>
                </div>
                <div class='feature-card'>
                    <h4>{t['card6_title']}</h4><p>{t['card6_text']}</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
            <div style='text-align:center; margin: 1rem 0 0.5rem 0;
            background: #E8F5E9; border: 2px solid #00695C; border-radius: 10px;
            padding: 0.6rem 1rem; color: #00473E; font-weight: 700; font-size: 1rem;'>
                {t['start_prompt']}
            </div>
        """, unsafe_allow_html=True)

    # ---- CHAT HISTORY ----
    for idx, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant", avatar="🏰"):
                st.markdown(message["content"])
                is_last = idx == len(st.session_state.chat_history) - 1
                if is_last and st.session_state.last_response_data:
                    show_expanders(st.session_state.last_response_data, t)
                # Feedback buttons for every assistant message
                prev_user = ""
                for m in st.session_state.chat_history[:idx]:
                    if m["role"] == "user":
                        prev_user = m["content"]
                show_feedback_buttons(idx, prev_user, message["content"], t)

    # ---- CHAT INPUT ----
    user_input = st.chat_input(t["chat_input"])

    if st.session_state.quick_action_input:
        user_input = st.session_state.quick_action_input
        st.session_state.quick_action_input = ""

    if user_input:
        if len(user_input.strip()) < 2:
            st.warning(t["warning_short"])
        elif len(user_input) > 500:
            st.warning(t["warning_long"])
        else:
            allowed, wait_seconds = check_rate_limit()
            if not allowed:
                st.warning(t["rate_limit"].format(wait_seconds))
            else:
                st.session_state.message_timestamps.append(time.time())

                with st.chat_message("user"):
                    st.markdown(user_input)

                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input
                })

                response = ""
                sources = []
                tools_used = []
                prompt_tokens = 0
                completion_tokens = 0
                chunks = []

                with st.chat_message("assistant", avatar="🏰"):
                    with st.spinner(t["thinking"]):
                        try:
                            # Inject custom entry fees into context if user has updated them
                            fees_context = ""
                            if st.session_state.custom_fees:
                                fees_lines = ", ".join(
                                    f"{k.title()}: €{v:.2f}"
                                    for k, v in st.session_state.custom_fees.items()
                                )
                                fees_context = f"\n\n[User-updated entry fees for this session: {fees_lines}. Use these prices instead of defaults when calculating budgets.]"
                            response, prompt_tokens, completion_tokens, sources, tools_used, chunks = chat(
                                user_input + fees_context,
                                st.session_state.chat_history[:-1],
                                st.session_state.language
                            )
                        except Exception as e:
                            response = t["error_msg"]
                            tools_used = []
                            chunks = []
                            st.error(f"Error details: {str(e)}")

                    st.markdown(response)

                st.session_state.last_response_data = {
                    "tools_used": tools_used,
                    "sources": sources,
                    "chunks": chunks,
                    "question": user_input,
                    "answer": response
                }

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })

                st.session_state.total_messages += 1
                st.session_state.total_prompt_tokens += prompt_tokens
                st.session_state.total_completion_tokens += completion_tokens
                st.rerun()


with tab2:
    st.markdown(t["form_title"])
    st.markdown(t["form_subtitle"])
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        destination_choice = st.selectbox(
            t["form_destination"],
            options=t["sites"]
        )

        is_other = "Other" in destination_choice or "Kita" in destination_choice
        if is_other:
            custom_destination = st.text_input(
                t["form_destination_other"],
                placeholder=t["form_destination_other_placeholder"]
            )
        else:
            custom_destination = ""

        destination = custom_destination.strip() if is_other and custom_destination.strip() else destination_choice

        grade = st.selectbox(
            t["form_grade"],
            options=[
                "Grade 1", "Grade 2", "Grade 3", "Grade 4",
                "Grade 5", "Grade 6", "Grade 7", "Grade 8",
                "Grade 9", "Grade 10", "Grade 11", "Grade 12",
            ] if st.session_state.language == "English" else [
                "1 klasė", "2 klasė", "3 klasė", "4 klasė",
                "5 klasė", "6 klasė", "7 klasė", "8 klasė",
                "9 klasė", "10 klasė", "11 klasė", "12 klasė",
            ]
        )

        duration = st.selectbox(
            t["form_duration"],
            options=t["form_duration_options"]
        )

        season = st.selectbox(
            t["form_season"],
            options=t["form_season_options"]
        )

    with col2:
        pupils = st.number_input(
            t["form_pupils"],
            min_value=1,
            max_value=100,
            value=25
        )

        teachers = st.number_input(
            t["form_teachers"],
            min_value=1,
            max_value=20,
            value=2
        )

        city = st.text_input(
            t["form_city"],
            placeholder="Vilnius, Kaunas, Klaipėda..."
        )

        bus_cost = st.slider(
            t["form_bus_cost"],
            min_value=0.60,
            max_value=2.50,
            value=1.20,
            step=0.05,
            format="€%.2f/km",
            help=t["form_bus_cost_help"]
        )

        extra_site_options = [t["form_extra_site_none"]] + [
            s for s in t["sites"] if "Other" not in s and "Kita" not in s and s != destination_choice
        ]
        extra_site_choice = st.selectbox(
            t["form_extra_site"],
            options=extra_site_options
        )
        extra_site = "" if extra_site_choice == t["form_extra_site_none"] else extra_site_choice

    st.divider()

    if st.button(t["form_button"], use_container_width=True, type="primary"):
        if not city.strip():
            st.warning(t["form_error"])
        elif is_other and not custom_destination.strip():
            st.warning(t["form_error_other"])
        else:
            extra_site_text = f" Also include a visit to {extra_site}." if extra_site else ""
            extra_site_text_lt = f" Taip pat įtraukite vizitą į {extra_site}." if extra_site else ""

            # Map duration display to tool key
            if "Half" in duration or "Pusė" in duration:
                dur_key = "half"
            elif "Two" in duration or "Dvi" in duration:
                dur_key = "two"
            else:
                dur_key = "full"

            if st.session_state.language == "English":
                generated_prompt = (
                    f"Please plan a full school excursion to {destination} "
                    f"for {grade}, {pupils} pupils and {teachers} teachers, "
                    f"travelling from {city}. "
                    f"Trip duration: {duration} (duration key: {dur_key}). Season: {season}.{extra_site_text} "
                    f"Bus cost is €{bus_cost:.2f} per km. "
                    f"When using the budget calculator tool, use bus_cost_per_km={bus_cost:.2f} and duration={dur_key}. "
                    f"Include a day itinerary, budget estimate, and activity suggestions."
                )
            else:
                generated_prompt = (
                    f"Prašau suplanuoti visą mokyklinę ekskursiją į {destination} "
                    f"{grade}, {pupils} mokiniams ir {teachers} mokytojams, "
                    f"keliaujant iš {city}. "
                    f"Kelionės trukmė: {duration} (duration key: {dur_key}). Metų laikas: {season}.{extra_site_text_lt} "
                    f"Autobuso kaina €{bus_cost:.2f} už km. "
                    f"Naudojant biudžeto skaičiuoklę, naudoti bus_cost_per_km={bus_cost:.2f} ir duration={dur_key}. "
                    f"Įtraukite dienos maršrutą, biudžeto įvertinimą ir veiklų pasiūlymus."
                )

            st.info(f"✅ Generating plan for: **{destination}**, {grade}, {pupils} pupils from {city}")

            with st.spinner(t["thinking"]):
                try:
                    fees_context = ""
                    if st.session_state.custom_fees:
                        fees_lines = ", ".join(
                            f"{k.title()}: €{v:.2f}"
                            for k, v in st.session_state.custom_fees.items()
                        )
                        fees_context = f"\n\n[User-updated entry fees for this session: {fees_lines}. Use these prices instead of defaults when calculating budgets.]"
                    response, prompt_tokens, completion_tokens, sources, tools_used, chunks = chat(
                        generated_prompt + fees_context,
                        [],
                        st.session_state.language
                    )
                except Exception as e:
                    response = t["error_msg"]
                    prompt_tokens = 0
                    completion_tokens = 0
                    sources = []
                    tools_used = []
                    chunks = []

            st.markdown(t["plan_title"])
            st.markdown(response)

            show_expanders({
                "tools_used": tools_used,
                "sources": sources,
                "chunks": chunks,
                "question": generated_prompt,
                "answer": response
            }, t)

            st.session_state.chat_history.append({
                "role": "user",
                "content": generated_prompt
            })
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })

            st.session_state.total_messages += 1
            st.session_state.total_prompt_tokens += prompt_tokens
            st.session_state.total_completion_tokens += completion_tokens
