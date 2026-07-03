import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8081/api/v1")

THEME_PALETTES = {
    "dark": {
        "bg": "#121212",
        "bg_secondary": "#181818",
        "bg_tertiary": "#282828",
        "text": "#FFFFFF",
        "text_muted": "#B3B3B3",
        "border": "#404040",
        "accent": "#1DB954",
        "accent_hover": "#1ED760",
        "sidebar_bg": "#000000",
        "header_bg": "#000000",
        "user_bubble": "#2B2B2B",
        "assistant_bubble": "#181818",
        "chart_font": "#FFFFFF",
        "grid": "#333333",
        "shadow": "rgba(0, 0, 0, 0.35)",
        "clear_btn_bg": "#282828",
        "clear_btn_text": "#B3B3B3",
        "clear_btn_hover": "#E22134",
    },
    "light": {
        "bg": "#FFFFFF",
        "bg_secondary": "#F6F6F6",
        "bg_tertiary": "#EFEFEF",
        "text": "#191414",
        "text_muted": "#535353",
        "border": "#D9D9D9",
        "accent": "#1DB954",
        "accent_hover": "#1AA34A",
        "sidebar_bg": "#F6F6F6",
        "header_bg": "#FFFFFF",
        "user_bubble": "#E8F5E9",
        "assistant_bubble": "#F6F6F6",
        "chart_font": "#191414",
        "grid": "#E5E5E5",
        "shadow": "rgba(0, 0, 0, 0.08)",
        "clear_btn_bg": "#EFEFEF",
        "clear_btn_text": "#535353",
        "clear_btn_hover": "#E22134",
    },
}


def render_theme_css(theme: str) -> None:
    palette = THEME_PALETTES.get(theme, THEME_PALETTES["dark"])
    st.markdown(
        f"""
<style>
    :root {{
        --bg: {palette["bg"]};
        --bg-secondary: {palette["bg_secondary"]};
        --bg-tertiary: {palette["bg_tertiary"]};
        --text: {palette["text"]};
        --text-muted: {palette["text_muted"]};
        --border: {palette["border"]};
        --accent: {palette["accent"]};
        --accent-hover: {palette["accent_hover"]};
        --sidebar-bg: {palette["sidebar_bg"]};
        --header-bg: {palette["header_bg"]};
        --user-bubble: {palette["user_bubble"]};
        --assistant-bubble: {palette["assistant_bubble"]};
        --shadow: {palette["shadow"]};
    }}

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {{
        background-color: var(--bg);
        color: var(--text);
    }}

    .main .block-container {{
        background-color: var(--bg);
        color: var(--text);
        padding-top: 2rem !important;
    }}

    [data-testid="stHeader"] {{
        display: none !important;
    }}

    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {{
        background-color: var(--sidebar-bg);
    }}

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] .stMarkdown {{
        color: var(--text) !important;
    }}

    html, body, [data-testid="stAppViewContainer"] {{
        font-size: 14px !important;
    }}

    h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown {{
        color: var(--text) !important;
    }}

    h1, h1 span, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h1 span {{
        font-size: 40px !important;
        color: var(--text) !important;
    }}

    h2, h2 span, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h2 span {{
        font-size: 32px !important;
        color: var(--text) !important;
    }}

    h3, h3 span, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h3 span {{
        font-size: 1.25rem !important;
        color: var(--text) !important;
    }}

    h4, h4 span, [data-testid="stMarkdownContainer"] h4, [data-testid="stMarkdownContainer"] h4 span {{
        font-size: 1.1rem !important;
        color: var(--text) !important;
    }}

    p, label, span, .stMarkdown, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span {{
        font-size: 0.9rem !important;
        color: var(--text) !important;
    }}

    .stCaption, [data-testid="stCaptionContainer"] {{
        color: var(--text-muted) !important;
    }}

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    input, textarea, select {{
        background-color: var(--bg-secondary) !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        border-color: var(--border) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus,
    input:focus, textarea:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(29, 185, 84, 0.25) !important;
    }}

    input::placeholder, textarea::placeholder {{
        color: var(--text-muted) !important;
        -webkit-text-fill-color: var(--text-muted) !important;
        opacity: 0.7 !important;
    }}

    [data-testid="InputInstructions"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid var(--border);
        border-radius: 8px;
    }}

    button[data-testid="stBaseButton-primary"],
    button[kind="primary"] {{
        background-color: var(--accent) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 999px !important;
        font-weight: 600 !important;
        padding: 0.5rem 2rem !important;
        transition: all 0.3s ease !important;
    }}

    button[data-testid="stBaseButton-primary"]:hover,
    button[kind="primary"]:hover {{
        background-color: var(--accent-hover) !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 12px rgba(29, 185, 84, 0.4) !important;
        transform: translateY(-1px) !important;
    }}

    button[data-testid="stBaseButton-secondary"],
    button[kind="secondary"] {{
        background-color: var(--bg-tertiary) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 999px !important;
        font-weight: 600 !important;
        padding: 0.5rem 2rem !important;
        transition: all 0.3s ease !important;
    }}

    button[data-testid="stBaseButton-secondary"]:hover,
    button[kind="secondary"]:hover {{
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        transform: translateY(-1px) !important;
    }}

    .metric-card {{
        background-color: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.25rem !important;
        text-align: center;
        box-shadow: 0 4px 12px var(--shadow);
        transition: all 0.3s ease;
    }}

    .metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 20px var(--shadow);
        border-color: var(--accent) !important;
    }}

    .metric-value {{
        font-size: 2.0rem !important;
        font-weight: bold;
        color: var(--accent);
        margin-bottom: 0.5rem;
    }}

    .metric-label {{
        font-size: 0.8rem !important;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    .chat-bubble {{
        padding: 1.25rem;
        border-radius: 16px;
        margin-bottom: 1.25rem;
        line-height: 1.6;
        color: var(--text);
        box-shadow: 0 4px 12px var(--shadow);
        border: 1px solid var(--border);
    }}

    .user-bubble {{
        background-color: var(--user-bubble);
        border-bottom-right-radius: 4px;
        border-left: 4px solid var(--accent);
    }}

    .assistant-bubble {{
        background-color: var(--assistant-bubble);
        border-bottom-left-radius: 4px;
        border-left: 4px solid var(--border);
    }}

    button[title="Clear search and start a new question"] {{
        min-width: 2.5rem;
        padding: 0.4rem 0.6rem;
        background-color: {palette["clear_btn_bg"]} !important;
        color: {palette["clear_btn_text"]} !important;
        border: 1px solid var(--border) !important;
        border-radius: 50% !important;
        font-size: 1.1rem;
        line-height: 1;
    }}

    button[title="Clear search and start a new question"]:hover {{
        background-color: {palette["clear_btn_hover"]} !important;
        color: #FFFFFF !important;
        border-color: {palette["clear_btn_hover"]} !important;
    }}

    .st-key-theme_toggle {{
        position: fixed !important;
        top: 0.6rem !important;
        right: 1rem !important;
        z-index: 1000000 !important;
        width: auto !important;
        min-width: 7rem;
        background-color: var(--bg-secondary) !important;
        padding: 0.15rem 0.75rem !important;
        border-radius: 999px !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 2px 8px var(--shadow);
    }}

    .st-key-theme_toggle label {{
        color: var(--text) !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }}

    /* Hide Streamlit's default header buttons (Hamburger, Deploy, Stop, etc.) */
    [data-testid="stHeaderDropdownMenu"],
    [data-testid="stHeaderDeployButton"],
    [data-testid="stHeaderActionButton"],
    #MainMenu,
    .stDeployButton,
    button[aria-label="open user menu"] {{
        display: none !important;
        visibility: hidden !important;
    }}
</style>
        """,
        unsafe_allow_html=True,
    )


def plotly_layout(theme: str) -> dict:
    palette = THEME_PALETTES.get(theme, THEME_PALETTES["dark"])
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": palette["chart_font"]},
        "xaxis": {
            "gridcolor": palette["grid"],
            "linecolor": palette["grid"],
            "tickfont": {"color": palette["chart_font"]},
            "title": {"font": {"color": palette["chart_font"]}}
        },
        "yaxis": {
            "gridcolor": palette["grid"],
            "linecolor": palette["grid"],
            "tickfont": {"color": palette["chart_font"]},
            "title": {"font": {"color": palette["chart_font"]}}
        },
    }

# Set Page Config
st.set_page_config(
    page_title="Spotify AI-Powered Review Discovery Engine",
    layout="wide",
    page_icon="🎵",
    initial_sidebar_state="collapsed",
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "theme_toggle" not in st.session_state:
    st.session_state.theme_toggle = True

st.session_state.theme = "dark" if st.session_state.theme_toggle else "light"
render_theme_css(st.session_state.theme)

# ---------------------------------------------------------------------------
# API Helper Functions
# ---------------------------------------------------------------------------
def fetch_insights():
    try:
        response = requests.get(f"{API_BASE_URL}/insights", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Backend offline: {e}")
    return None

# Initialize Session States
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(datetime.now().timestamp())}"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "discovered_tracks" not in st.session_state:
    st.session_state.discovered_tracks = []
if "parsed_intent" not in st.session_state:
    st.session_state.parsed_intent = {}
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "user_query_input" not in st.session_state:
    st.session_state.user_query_input = ""
if "spotify_auth" not in st.session_state:
    st.session_state.spotify_auth = False

def clear_discovery_session():
    if "user_query_input" in st.session_state:
        st.session_state["user_query_input"] = ""

def clear_search_results():
    st.session_state.chat_history = []
    st.session_state.discovered_tracks = []
    st.session_state.parsed_intent = {}
    st.session_state.last_query = ""
    st.session_state.session_id = f"session_{int(datetime.now().timestamp())}"

# ---------------------------------------------------------------------------
# Main View: Spotify AI-Powered Review Discovery Engine
# ---------------------------------------------------------------------------
st.toggle("Dark", key="theme_toggle", value=True, help="Toggle dark/light theme")

st.title("🔍 Spotify AI-Powered Review Discovery Engine")
st.markdown(
    "Quantify user sentiment from App Store, Google Play, Twitter, and Reddit — "
    "then ask review research questions or explore music through the AI assistant."
)

st.markdown("## 💬 Review Discovery Assistant")

# 1. Search Input Bar at the top
input_col, clear_col = st.columns([11, 1])
with input_col:
    user_query = st.text_input(
        "Ask a review question or describe music you're looking for:",
        placeholder="e.g., What unmet needs emerge across reviews? or Chill lofi beats for studying",
        key="user_query_input",
    )
with clear_col:
    st.markdown("<div style='height: 1.75rem'></div>", unsafe_allow_html=True)
    st.button(
        "✕",
        key="clear_search_btn",
        help="Clear search and start a new question",
        type="secondary",
        on_click=clear_discovery_session,
    )

# 2. Search / Refine Buttons below the input
col_q1, col_q2, col_q3 = st.columns(3)
with col_q1:
    search_submitted = st.button("Search", type="primary")
with col_q2:
    refine_submitted = st.button("Apply as Refinement", type="secondary")
with col_q3:
    clear_results_submitted = st.button("Clear search result", type="secondary")

if clear_results_submitted:
    clear_search_results()
    st.rerun()

# 3. Action trigger logic
if search_submitted and user_query:
    with st.spinner("Analyzing intent and searching vector space..."):
        payload = {
            "query": user_query,
            "session_id": st.session_state.session_id,
            "history": [h for h in st.session_state.chat_history]
        }
        res = requests.post(f"{API_BASE_URL}/discover", json=payload)
        if res.status_code == 200:
            data = res.json()
            st.session_state.discovered_tracks = data.get("tracks", [])
            st.session_state.parsed_intent = data.get("parsed_intent", {})
            st.session_state.last_query = user_query
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            st.session_state.chat_history.append({"role": "assistant", "content": data.get("explanation", "")})
            st.rerun()

if refine_submitted and user_query:
    if not st.session_state.parsed_intent:
        st.error("Please run an initial query search first before refining.")
    else:
        with st.spinner("Applying refinement criteria..."):
            payload = {
                "session_id": st.session_state.session_id,
                "refinement": user_query,
                "previous_intent": st.session_state.parsed_intent
            }
            res = requests.post(f"{API_BASE_URL}/discover/refine", json=payload)
            if res.status_code == 200:
                data = res.json()
                st.session_state.discovered_tracks = data.get("tracks", [])
                st.session_state.parsed_intent = data.get("parsed_intent", {})
                st.session_state.chat_history.append({"role": "user", "content": f"Refine: {user_query}"})
                st.session_state.chat_history.append({"role": "assistant", "content": data.get("explanation", "")})
                st.rerun()

# 4. Results display below the buttons
if st.session_state.chat_history:
    latest_msg = st.session_state.chat_history[-1]
    if latest_msg["role"] == "assistant":
        st.markdown(f'<div class="chat-bubble assistant-bubble"><strong>ANALYSIS & FINDINGS</strong>:<br/>{latest_msg["content"]}</div>', unsafe_allow_html=True)

if st.session_state.discovered_tracks:
    st.markdown("### 🎵 Recommended Songs")
    intent = st.session_state.parsed_intent
    st.markdown(f"**Applied Filters**: Genres: `{intent.get('genres')}`, Energy: `{intent.get('energy_range')}`, Tempo: `{intent.get('tempo_range')} BPM`")
    
    # Custom HTML for recommended song cards
    cards_html = "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; margin-top: 1rem;'>"
    for idx, t in enumerate(st.session_state.discovered_tracks):
        name = t.get("track_name", t.get("name", "Unknown Track"))
        artist = t.get("artist", "Unknown Artist")
        genre = t.get("genre", "General")
        subgenre = t.get("subgenre", "")
        energy = t.get("energy", 0.5)
        tempo = t.get("tempo_bpm", t.get("tempo", 120))
        energy_pct = int(energy * 100)
        
        subgenre_badge = f"<span style='font-size: 0.65rem; background: rgba(29, 185, 84, 0.1); border: 1px solid rgba(29, 185, 84, 0.3); border-radius: 999px; padding: 0.15rem 0.5rem; color: #1DB954; font-weight: 600; margin-left: 0.3rem;'>{subgenre}</span>" if subgenre else ""
        
        cards_html += f"""
        <div style='background-color: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 4px 12px var(--shadow); transition: all 0.3s ease;'>
            <div>
                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;'>
                    <span style='font-size: 1.4rem; font-weight: bold; color: #1DB954;'>{idx + 1}</span>
                    <div style='display: flex; gap: 0.2rem; flex-wrap: wrap;'>
                        <span style='font-size: 0.65rem; background: rgba(29, 185, 84, 0.15); border: 1px solid rgba(29, 185, 84, 0.3); border-radius: 999px; padding: 0.15rem 0.5rem; color: #1DB954; font-weight: 600;'>{genre}</span>
                        {subgenre_badge}
                    </div>
                </div>
                <div style='font-size: 1rem; font-weight: bold; color: var(--text); margin-bottom: 0.25rem;'>{name}</div>
                <div style='font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;'>{artist}</div>
            </div>
            <div style='border-top: 1px solid var(--border); padding-top: 0.75rem; display: flex; flex-direction: column; gap: 0.4rem;'>
                <div style='display: flex; align-items: center; justify-content: space-between;'>
                    <span style='font-size: 0.75rem; color: var(--text-muted);'>Energy:</span>
                    <div style='flex: 1; height: 4px; background: var(--bg-tertiary); border-radius: 2px; margin: 0 0.5rem; overflow: hidden;'>
                        <div style='height: 100%; background: #1DB954; width: {energy_pct}%;'></div>
                    </div>
                    <span style='font-size: 0.75rem; color: var(--text); font-weight: 600;'>{energy_pct}%</span>
                </div>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 0.75rem; color: var(--text-muted);'>Tempo:</span>
                    <span style='font-size: 0.75rem; color: var(--text); font-weight: 600;'>{tempo} BPM</span>
                </div>
            </div>
        </div>
        """
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)


# 5. Collapsible historical conversation history
if len(st.session_state.chat_history) > 2:
    with st.expander("Show Conversation History"):
        for msg in st.session_state.chat_history[:-1]:
            bubble_class = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
            st.markdown(f'<div class="chat-bubble {bubble_class}"><strong>{msg["role"].upper()}</strong>:<br/>{msg["content"]}</div>', unsafe_allow_html=True)

