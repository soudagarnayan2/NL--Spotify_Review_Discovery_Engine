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
    initial_sidebar_state="expanded",
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "theme_toggle" not in st.session_state:
    st.session_state.theme_toggle = True

st.session_state.theme = "dark" if st.session_state.theme_toggle else "light"
render_theme_css(st.session_state.theme)

# Wanderer session states
if "wanderer_chat_history" not in st.session_state:
    st.session_state.wanderer_chat_history = []
if "wanderer_current_recommendations" not in st.session_state:
    st.session_state.wanderer_current_recommendations = []
if "wanderer_current_mood" not in st.session_state:
    st.session_state.wanderer_current_mood = None
if "wanderer_context" not in st.session_state:
    st.session_state.wanderer_context = {}

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

def fetch_moods():
    try:
        response = requests.get(f"{API_BASE_URL}/moods", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Backend offline: {e}")
    return {}

def fetch_mood_songs(mood: str, limit: int = 10):
    try:
        response = requests.get(f"{API_BASE_URL}/moods/{mood}/songs", params={"limit": limit}, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Backend offline: {e}")
    return []

def send_mood_feedback(song_id: str, feedback_type: str):
    try:
        response = requests.post(f"{API_BASE_URL}/songs/{song_id}/mood-feedback", 
                                json={"feedback_type": feedback_type}, timeout=5)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Backend offline: {e}")
    return False

# ---------------------------------------------------------------------------
# Wanderer Helper Functions
# ---------------------------------------------------------------------------
def process_wanderer_message(message: str) -> str:
    """Process user message and generate response."""
    message_lower = message.lower()
    
    # Check for correction patterns
    if any(phrase in message_lower for phrase in ["too safe", "too boring", "more exciting", "more energy"]):
        return handle_correction("more_energy")
    elif any(phrase in message_lower for phrase in ["too intense", "too loud", "calm down", "chill out"]):
        return handle_correction("less_energy")
    elif any(phrase in message_lower for phrase in ["keep this mood", "stay like this", "more like this"]):
        return handle_correction("keep_mood")
    elif any(phrase in message_lower for phrase in ["why this", "why did you", "explain this"]):
        return handle_correction("explain")
    
    # Check for mood requests
    moods_data = fetch_moods()
    if moods_data:
        # Handle both dict and list formats
        if isinstance(moods_data, dict):
            mood_items = moods_data.items()
        elif isinstance(moods_data, list):
            mood_items = [(m.get("key", m.get("id", str(i))), m) for i, m in enumerate(moods_data)]
        else:
            mood_items = []
        
        for mood_key, mood_info in mood_items:
            mood_name = mood_info.get("display_name", mood_info.get("name", mood_key))
            if mood_name and (mood_name.lower() in message_lower or mood_key.lower() in message_lower):
                return get_mood_recommendations(mood_key, mood_name)
    
    # Default: try to discover music
    try:
        payload = {
            "query": message,
            "session_id": st.session_state.session_id,
            "history": []
        }
        res = requests.post(f"{API_BASE_URL}/discover", json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            tracks = data.get("tracks", [])
            if tracks:
                st.session_state.wanderer_current_recommendations = tracks[:5]
                st.session_state.wanderer_current_mood = "discovered"
                explanations = generate_explanations(tracks, message)
                return f"I found some songs that match what you're looking for! Here are my top picks:\n\n{explanations}"
            else:
                return "I couldn't find any songs that match that description. Try describing the mood differently, or tell me about a specific genre or artist you enjoy."
    except Exception as e:
        return f"I'm having trouble connecting to my music database right now. Let me try a different approach. Could you tell me about a specific mood you're in? For example: 'I need something upbeat' or 'I want to feel nostalgic'."

def handle_correction(correction_type: str) -> str:
    """Handle user corrections to recommendations."""
    if correction_type == "more_energy":
        if st.session_state.wanderer_current_mood:
            # Adjust to higher energy mood
            current_mood = st.session_state.wanderer_current_mood
            mood_map = {
                "chill": "energetic",
                "focus": "upbeat",
                "sad": "hopeful",
                "relaxed": "energetic"
            }
            new_mood = mood_map.get(current_mood, "energetic")
            return get_mood_recommendations(new_mood, new_mood.title(), correction_context="more energy")
        return "I'll find something with more energy for you!"
    
    elif correction_type == "less_energy":
        if st.session_state.wanderer_current_mood:
            current_mood = st.session_state.wanderer_current_mood
            mood_map = {
                "energetic": "chill",
                "upbeat": "focus",
                "hopeful": "relaxed",
                "party": "chill"
            }
            new_mood = mood_map.get(current_mood, "chill")
            return get_mood_recommendations(new_mood, new_mood.title(), correction_context="less energy")
        return "I'll dial it down and find something more chill for you!"
    
    elif correction_type == "keep_mood":
        return "Got it! I'll keep exploring within this same mood. Let me find more songs like these."
    
    elif correction_type == "explain":
        if st.session_state.wanderer_current_recommendations:
            track = st.session_state.wanderer_current_recommendations[0]
            explanation = track.get('explanation', 'This song was selected based on its audio features matching your current mood preferences.')
            return f"Here's why I picked this one: {explanation}\n\nThe combination of energy, tempo, and mood characteristics makes it a great fit for what you're looking for."
        return "I'd be happy to explain! Could you tell me which song you're curious about?"

def get_mood_recommendations(mood_key: str, mood_name: str, correction_context: str = None) -> str:
    """Get recommendations for a specific mood."""
    songs = fetch_mood_songs(mood_key, limit=5)
    
    if songs:
        st.session_state.wanderer_current_recommendations = songs
        st.session_state.wanderer_current_mood = mood_key
        
        prefix = ""
        if correction_context:
            prefix = f"Adjusting for {correction_context}... "
        
        explanations = generate_explanations(songs, mood_name)
        return f"{prefix}I found some perfect {mood_name} songs for you! Here's what I picked and why:\n\n{explanations}"
    else:
        return f"I couldn't find any songs in the {mood_name} category right now. Try a different mood or describe what you're looking for in your own words."

def generate_explanations(tracks: list, context: str) -> str:
    """Generate natural language explanations for tracks."""
    explanations = []
    for idx, track in enumerate(tracks[:3]):
        name = track.get("name", "Unknown")
        artist = track.get("artist", "Unknown")
        energy = track.get("energy", 0.5)
        tempo = track.get("tempo", 120)
        
        energy_desc = "high-energy" if energy > 0.7 else "moderate-energy" if energy > 0.4 else "chill"
        tempo_desc = "fast-paced" if tempo > 140 else "moderate tempo" if tempo > 100 else "slow and steady"
        
        explanation = f"**{idx + 1}. {name} by {artist}** — This track has a {energy_desc} vibe with {tempo_desc} ({int(tempo)} BPM), which perfectly matches your {context} mood."
        explanations.append(explanation)
    
    return "\n\n".join(explanations)

def process_feedback(song_id: str, feedback_type: str) -> str:
    """Process user feedback on a specific song."""
    if feedback_type == "keep":
        send_mood_feedback(song_id, "positive")
        return "Great! I'll remember you like this style and find more similar songs."
    elif feedback_type == "skip":
        send_mood_feedback(song_id, "negative")
        return "Got it, I'll skip this one and find something different for you."
    elif feedback_type == "why":
        track = next((t for t in st.session_state.wanderer_current_recommendations if t.get('id') == song_id), None)
        if track:
            energy = track.get("energy", 0.5)
            tempo = track.get("tempo", 120)
            return f"I picked this because it has {int(energy * 100)}% energy and {int(tempo)} BPM, which aligns with your current mood preferences. The combination creates the perfect atmosphere for what you're looking for."
        return "This song was selected based on how well its characteristics match your current mood preferences."

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

def clear_wanderer_session():
    st.session_state.wanderer_chat_history = []
    st.session_state.wanderer_current_recommendations = []
    st.session_state.wanderer_current_mood = None
    st.session_state.wanderer_context = {}

# ---------------------------------------------------------------------------
# Main View: Spotify AI-Powered Review Discovery Engine
# ---------------------------------------------------------------------------
st.toggle("Dark", key="theme_toggle", value=True, help="Toggle dark/light theme")

# Sidebar for navigation
with st.sidebar:
    st.title("🎵 Spotify Discovery")
    st.markdown("---")
    
    page = st.radio(
        "Navigate",
        ["🔍 Discovery Engine", "🧭 Wanderer"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        """
        **Discovery Engine**: Analyze reviews and discover music through AI-powered search.
        
        **Wanderer**: Conversational agent that explains recommendations and adapts to your feedback in natural language.
        """
    )

if page == "🔍 Discovery Engine":
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
        
        # Custom HTML for recommended song cards - matching screenshot design
        cards_html = "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; margin-top: 1rem;'>"
        for idx, t in enumerate(st.session_state.discovered_tracks):
            name = t.get("track_name", t.get("name", "Unknown Track"))
            artist = t.get("artist", "Unknown Artist")
            genre = t.get("genre", "General")
            subgenre = t.get("subgenre", "")
            energy = t.get("energy", 0.5)
            tempo = t.get("tempo_bpm", t.get("tempo", 120))
            energy_pct = int(energy * 100)
            
            subgenre_badge = f"<span style='font-size: 0.6rem; background: rgba(29, 185, 84, 0.15); border: 1px solid rgba(29, 185, 84, 0.4); border-radius: 999px; padding: 0.1rem 0.4rem; color: #1DB954; font-weight: 600; margin-left: 0.25rem;'>{subgenre}</span>" if subgenre else ""
            
            cards_html += f"""
            <div style='background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; display: flex; flex-direction: column; gap: 0.75rem; box-shadow: 0 4px 16px var(--shadow); transition: all 0.3s ease; position: relative; overflow: hidden;'>
                <div style='position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #1DB954 0%, #1ED760 100%);'></div>
                <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                    <div style='display: flex; align-items: center; gap: 0.5rem;'>
                        <span style='font-size: 1.8rem; font-weight: 800; color: #1DB954; line-height: 1;'>{idx + 1}</span>
                        <div style='display: flex; gap: 0.25rem; flex-wrap: wrap;'>
                            <span style='font-size: 0.6rem; background: rgba(29, 185, 84, 0.2); border: 1px solid rgba(29, 185, 84, 0.4); border-radius: 999px; padding: 0.1rem 0.4rem; color: #1DB954; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>{genre}</span>
                            {subgenre_badge}
                        </div>
                    </div>
                </div>
                <div style='margin-top: 0.25rem;'>
                    <div style='font-size: 1.1rem; font-weight: 700; color: var(--text); margin-bottom: 0.25rem; line-height: 1.3;'>{name}</div>
                    <div style='font-size: 0.85rem; color: var(--text-muted); font-weight: 500;'>{artist}</div>
                </div>
                <div style='display: flex; flex-direction: column; gap: 0.5rem; margin-top: auto;'>
                    <div style='display: flex; align-items: center; gap: 0.5rem;'>
                        <span style='font-size: 0.7rem; color: var(--text-muted); font-weight: 600; min-width: 45px;'>ENERGY</span>
                        <div style='flex: 1; height: 6px; background: var(--bg); border-radius: 3px; overflow: hidden;'>
                            <div style='height: 100%; background: linear-gradient(90deg, #1DB954 0%, #1ED760 100%); width: {energy_pct}%; border-radius: 3px;'></div>
                        </div>
                        <span style='font-size: 0.7rem; color: var(--text); font-weight: 700; min-width: 35px; text-align: right;'>{energy_pct}%</span>
                    </div>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='font-size: 0.7rem; color: var(--text-muted); font-weight: 600;'>TEMPO</span>
                        <span style='font-size: 0.7rem; color: var(--text); font-weight: 700;'>{tempo} BPM</span>
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

elif page == "🧭 Wanderer":
    st.markdown("### 🧭 Wanderer")
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, rgba(29, 185, 84, 0.1) 0%, rgba(29, 185, 84, 0.05) 100%); border: 1px solid rgba(29, 185, 84, 0.3); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;'>
            <strong style='color: #1DB954; font-size: 1.1rem;'>Conversational Music Agent</strong><br/>
            <span style='color: var(--text-muted); font-size: 0.9rem;'>Tell me what you're in the mood for, and I'll recommend songs with clear explanations. You can correct me naturally — say things like "too safe," "keep this mood," or "why this?" and I'll adjust immediately.</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Chat interface with improved styling
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        if not st.session_state.wanderer_chat_history:
            st.markdown(
                """
                <div style='text-align: center; padding: 2rem; color: var(--text-muted);'>
                    <div style='font-size: 3rem; margin-bottom: 1rem;'>🎵</div>
                    <div style='font-size: 1.1rem; font-weight: 500;'>Start a conversation</div>
                    <div style='font-size: 0.9rem;'>Tell me what you're in the mood for</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            for msg in st.session_state.wanderer_chat_history:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-bubble user-bubble"><strong>YOU</strong>:<br/>{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bubble assistant-bubble"><strong>WANDERER</strong>:<br/>{msg["content"]}</div>', unsafe_allow_html=True)
    
    # Input area with improved styling
    st.markdown("---")
    input_col, clear_col, send_col = st.columns([10, 1, 1])
    
    with input_col:
        wanderer_input = st.text_input(
            "Tell me what you're feeling or ask about a recommendation:",
            placeholder="e.g., I need something energetic for a workout, or Why did you pick this song?",
            key="wanderer_input",
            label_visibility="collapsed"
        )
    
    with clear_col:
        st.markdown("<div style='height: 2.5rem'></div>", unsafe_allow_html=True)
        if st.button("🗑️", key="clear_wanderer", help="Start fresh", type="secondary"):
            clear_wanderer_session()
            st.rerun()
    
    with send_col:
        st.markdown("<div style='height: 2.5rem'></div>", unsafe_allow_html=True)
        send_clicked = st.button("Send", type="primary", key="send_wanderer")
    
    # Process user input
    if send_clicked and wanderer_input:
        user_message = wanderer_input.strip()
        if not user_message:
            st.warning("Please say something!")
        else:
            # Add user message to chat
            st.session_state.wanderer_chat_history.append({"role": "user", "content": user_message})
            
            # Process the message
            with st.spinner("Thinking..."):
                response = process_wanderer_message(user_message)
                st.session_state.wanderer_chat_history.append({"role": "assistant", "content": response})
            
            st.rerun()
    
    # Display current recommendations if available
    if st.session_state.wanderer_current_recommendations:
        st.markdown("---")
        st.markdown("### 🎵 Current Recommendations")
        
        # Custom HTML cards matching the screenshot design
        cards_html = "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; margin-top: 1rem;'>"
        for idx, track in enumerate(st.session_state.wanderer_current_recommendations):
            name = track.get("name", track.get("track_name", "Unknown Track"))
            artist = track.get("artist", "Unknown Artist")
            genre = track.get("genre", "General")
            energy = track.get("energy", 0.5)
            tempo = track.get("tempo", track.get("tempo_bpm", 120))
            energy_pct = int(energy * 100)
            
            cards_html += f"""
            <div style='background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; display: flex; flex-direction: column; gap: 0.75rem; box-shadow: 0 4px 16px var(--shadow); transition: all 0.3s ease; position: relative; overflow: hidden;'>
                <div style='position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #1DB954 0%, #1ED760 100%);'></div>
                <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                    <div style='display: flex; align-items: center; gap: 0.5rem;'>
                        <span style='font-size: 1.8rem; font-weight: 800; color: #1DB954; line-height: 1;'>{idx + 1}</span>
                        <span style='font-size: 0.6rem; background: rgba(29, 185, 84, 0.2); border: 1px solid rgba(29, 185, 84, 0.4); border-radius: 999px; padding: 0.1rem 0.4rem; color: #1DB954; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>{genre}</span>
                    </div>
                </div>
                <div style='margin-top: 0.25rem;'>
                    <div style='font-size: 1.1rem; font-weight: 700; color: var(--text); margin-bottom: 0.25rem; line-height: 1.3;'>{name}</div>
                    <div style='font-size: 0.85rem; color: var(--text-muted); font-weight: 500;'>{artist}</div>
                </div>
                <div style='display: flex; flex-direction: column; gap: 0.5rem; margin-top: auto;'>
                    <div style='display: flex; align-items: center; gap: 0.5rem;'>
                        <span style='font-size: 0.7rem; color: var(--text-muted); font-weight: 600; min-width: 45px;'>ENERGY</span>
                        <div style='flex: 1; height: 6px; background: var(--bg); border-radius: 3px; overflow: hidden;'>
                            <div style='height: 100%; background: linear-gradient(90deg, #1DB954 0%, #1ED760 100%); width: {energy_pct}%; border-radius: 3px;'></div>
                        </div>
                        <span style='font-size: 0.7rem; color: var(--text); font-weight: 700; min-width: 35px; text-align: right;'>{energy_pct}%</span>
                    </div>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='font-size: 0.7rem; color: var(--text-muted); font-weight: 600;'>TEMPO</span>
                        <span style='font-size: 0.7rem; color: var(--text); font-weight: 700;'>{tempo} BPM</span>
                    </div>
                </div>
            </div>
            """
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)
        
        # Feedback section
        st.markdown("### 💬 Feedback")
        st.markdown("Tell me what you think of these recommendations:")
        
        for idx, track in enumerate(st.session_state.wanderer_current_recommendations):
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"👍 Keep {idx + 1}", key=f"keep_{track.get('id', idx)}", type="secondary"):
                    feedback = process_feedback(track.get('id'), "keep")
                    st.session_state.wanderer_chat_history.append({"role": "assistant", "content": feedback})
                    st.rerun()
            with col2:
                if st.button(f"❌ Skip {idx + 1}", key=f"skip_{track.get('id', idx)}", type="secondary"):
                    feedback = process_feedback(track.get('id'), "skip")
                    st.session_state.wanderer_chat_history.append({"role": "assistant", "content": feedback})
                    st.rerun()
            with col3:
                if st.button(f"❓ Why {idx + 1}?", key=f"why_{track.get('id', idx)}", type="secondary"):
                    feedback = process_feedback(track.get('id'), "why")
                    st.session_state.wanderer_chat_history.append({"role": "assistant", "content": feedback})
                    st.rerun()
