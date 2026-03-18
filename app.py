from rag_evaluator import evaluate_rag_response, format_score_emoji
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

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .main-header h1 { font-size: 2.5rem; font-weight: 800; margin: 0; }
    .main-header p { font-size: 1.1rem; opacity: 0.9; margin: 0.5rem 0 0 0; }

    .feature-card {
        background: #F1F8E9;
        border: 1px solid #C8E6C9;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #2E7D32;
        cursor: default;
    }
    .feature-card h4 { margin: 0 0 0.3rem 0; color: #2E7D32; font-size: 1rem; }
    .feature-card p { margin: 0; color: #555; font-size: 0.9rem; }

    .dest-badge {
        display: inline-block;
        background: #E8F5E9;
        border: 1px solid #A5D6A7;
        color: #2E7D32;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.2rem;
        font-weight: 500;
    }

    .stat-card {
        background: #F1F8E9;
        border: 1px solid #C8E6C9;
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .stat-card .stat-number { font-size: 1.5rem; font-weight: 700; color: #2E7D32; }
    .stat-card .stat-label { font-size: 0.75rem; color: #777; margin-top: 0.2rem; }

    .example-q {
        background: #F9FBF9;
        border: 1px solid #C8E6C9;
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.3rem 0;
        font-size: 0.85rem;
        color: #444;
        cursor: default;
    }

    .footer {
        text-align: center;
        color: #999;
        font-size: 0.75rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #E8F5E9;
    }

    [data-testid="stSidebar"] {
        background: #FAFFFE !important;
        border-right: 1px solid #C8E6C9 !important;
    }
    hr { border-color: #C8E6C9 !important; }

    .stChatFloatingInputContainer {
        bottom: 0;
        position: sticky !important;
    }
</style>
""", unsafe_allow_html=True)


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


# ---- UI TRANSLATIONS ----
UI_TEXT = {
    "English": {
        "title": "🏰 ExcursionBot",
        "subtitle": "AI-powered school excursion planner for Lithuanian historical sites",
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
Vilnius Old Town, Trakai Castle, Hill of Crosses,
Curonian Spit, Kaunas Old Town, Kernavė,
Museum of Occupations, Palanga Amber Museum

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
        "card1_text": "Detailed guides for 8 Lithuanian historical and cultural sites with educational context",
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
            "🌊 Is Curonian Spit suitable for primary school?",
            "🏰 Compare Trakai and Kernavė for history class",
        ],
        "sites": [
            "🏛️ Vilnius Old Town", "🏰 Trakai Castle",
            "✝️ Hill of Crosses", "🌊 Curonian Spit",
            "🏙️ Kaunas Old Town", "⛏️ Kernavė",
            "🔒 Museum of Occupations", "🟡 Palanga Amber Museum",
        ],
        "quick_actions": [
            ("🗓️ Plan Excursion", "I want to plan a school excursion. Can you help me?"),
            ("💰 Calculate Budget", "Calculate the budget for my school group excursion."),
            ("🎯 Suggest Activities", "Suggest age-appropriate activities for my school group."),
            ("🏛️ Site Guide", "Tell me about the best Lithuanian historical sites for school visits."),
            ("⚠️ Safety Tips", "What safety tips should I know for school excursions?"),
        ],
        "tab_chat": "💬 Chat",
        "tab_planner": "📋 Trip Planner",
        "form_title": "### 📋 Plan Your Excursion",
        "form_subtitle": "Fill in the details and I'll generate a complete excursion plan!",
        "form_destination": "🏛️ Destination",
        "form_grade": "🎓 School Grade",
        "form_pupils": "👥 Number of Pupils",
        "form_teachers": "👩‍🏫 Number of Teachers",
        "form_city": "📍 Travelling From (city or village)",
        "form_button": "🗓️ Generate Excursion Plan",
        "form_error": "⚠️ Please fill in all fields before generating a plan.",
        "error_msg": "⚠️ Sorry, I ran into an issue processing your request. Please try again.",
        "cleared_cache": "Cleared {} cached responses",
        "plan_title": "### 📋 Your Excursion Plan",
    },
    "Lithuanian": {
        "title": "🏰 ExcursionBot",
        "subtitle": "DI pagalbininkas mokyklinių ekskursijų planavimui Lietuvos istorinėse vietose",
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
Vilniaus senamiestis, Trakų pilis, Kryžių kalnas,
Kuršių nerija, Kauno senamiestis, Kernavė,
Okupacijų muziejus, Palangos gintaro muziejus

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
        "card1_text": "Išsamūs gidai apie 8 Lietuvos istorines ir kultūrines vietas",
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
            "🌊 Ar Kuršių nerija tinka pradinukams?",
            "🏰 Palyginti Trakus ir Kernavę istorijos pamokoms",
        ],
        "sites": [
            "🏛️ Vilniaus senamiestis", "🏰 Trakų pilis",
            "✝️ Kryžių kalnas", "🌊 Kuršių nerija",
            "🏙️ Kauno senamiestis", "⛏️ Kernavė",
            "🔒 Okupacijų muziejus", "🟡 Palangos gintaro muziejus",
        ],
        "quick_actions": [
            ("🗓️ Planuoti ekskursiją", "Noriu planuoti mokyklinę ekskursiją. Ar galite padėti?"),
            ("💰 Skaičiuoti biudžetą", "Apskaičiuokite biudžetą mano mokyklos grupės ekskursijai."),
            ("🎯 Veiklų pasiūlymai", "Pasiūlykite amžiui tinkamas veiklas mano mokyklos grupei."),
            ("🏛️ Vietovių gidas", "Papasakokite apie geriausias Lietuvos istorines vietas mokyklinėms išvykoms."),
            ("⚠️ Saugos patarimai", "Kokius saugos patarimus turėčiau žinoti mokyklinėms ekskursijoms?"),
        ],
        "tab_chat": "💬 Pokalbis",
        "tab_planner": "📋 Ekskursijos planuotojas",
        "form_title": "### 📋 Planuokite ekskursiją",
        "form_subtitle": "Užpildykite detales ir sugeneruosiu išsamų ekskursijos planą!",
        "form_destination": "🏛️ Vietovė",
        "form_grade": "🎓 Mokyklos klasė",
        "form_pupils": "👥 Mokinių skaičius",
        "form_teachers": "👩‍🏫 Mokytojų skaičius",
        "form_city": "📍 Išvykimo miestas ar kaimas",
        "form_button": "🗓️ Generuoti ekskursijos planą",
        "form_error": "⚠️ Prieš generuodami planą užpildykite visus laukus.",
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
                "build_itinerary": "🗓️ Itinerary Builder"
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
        [f"<span class='dest-badge'>{s}</span>" for s in t["sites"]]
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

    # ---- DOCUMENT UPLOAD ----
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
                    <h4>{t['card1_title']}</h4>
                    <p>{t['card1_text']}</p>
                </div>
                <div class='feature-card'>
                    <h4>{t['card2_title']}</h4>
                    <p>{t['card2_text']}</p>
                </div>
                <div class='feature-card'>
                    <h4>{t['card3_title']}</h4>
                    <p>{t['card3_text']}</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class='feature-card'>
                    <h4>{t['card4_title']}</h4>
                    <p>{t['card4_text']}</p>
                </div>
                <div class='feature-card'>
                    <h4>{t['card5_title']}</h4>
                    <p>{t['card5_text']}</p>
                </div>
                <div class='feature-card'>
                    <h4>{t['card6_title']}</h4>
                    <p>{t['card6_text']}</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
            <div style='text-align:center; margin-top: 1.5rem;
            color: #2E7D32; font-weight: 600; font-size: 1.1rem;'>
                {t['start_prompt']}
            </div>
        """, unsafe_allow_html=True)
        st.divider()

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
                            response, prompt_tokens, completion_tokens, sources, tools_used, chunks = chat(
                                user_input,
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
        destination = st.selectbox(
            t["form_destination"],
            options=t["sites"]
        )

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

    st.divider()

    if st.button(t["form_button"], use_container_width=True, type="primary"):
        if not city.strip():
            st.warning(t["form_error"])
        else:
            if st.session_state.language == "English":
                generated_prompt = (
                    f"Please plan a full school excursion to {destination} "
                    f"for {grade}, {pupils} pupils and {teachers} teachers, "
                    f"travelling from {city}. "
                    f"Include a day itinerary, budget estimate, and activity suggestions."
                )
            else:
                generated_prompt = (
                    f"Prašau suplanuoti visą mokyklinę ekskursiją į {destination} "
                    f"{grade}, {pupils} mokiniams ir {teachers} mokytojams, "
                    f"keliaujant iš {city}. "
                    f"Įtraukite dienos maršrutą, biudžeto įvertinimą ir veiklų pasiūlymus."
                )

            st.info(f"✅ Generating plan for: **{destination}**, {grade}, {pupils} pupils from {city}")

            with st.spinner(t["thinking"]):
                try:
                    response, prompt_tokens, completion_tokens, sources, tools_used, chunks = chat(
                        generated_prompt,
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
# Add to chat history so it appears in export
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
           