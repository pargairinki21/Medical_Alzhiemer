import streamlit as st
import asyncio
import os
from google.adk.runners import InMemoryRunner
from google.genai import types
from clinical_agent.orchestrator import coordinator

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Alzheimer's Clinical Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PREMIUM CLINICAL CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&family=DM+Serif+Display:ital@0;1&display=swap');

/* ── Global Reset ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0e1a !important;
    color: #e2e8f4 !important;
}

/* ── Hide Streamlit Chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1528 0%, #0a1020 100%) !important;
    border-right: 1px solid rgba(100, 149, 237, 0.15) !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}

/* ── Radio Buttons → Nav Items ── */
[data-testid="stSidebar"] .stRadio label {
    display: flex !important;
    align-items: center !important;
    padding: 10px 20px !important;
    border-radius: 8px !important;
    margin: 2px 8px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    color: #8a9bbf !important;
    border: 1px solid transparent !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(100, 149, 237, 0.08) !important;
    color: #c8d8f5 !important;
    border-color: rgba(100, 149, 237, 0.2) !important;
}
[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div + div,
[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label {
    background: rgba(100, 149, 237, 0.15) !important;
    color: #6495ed !important;
}
/* Hide native radio dots */
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child { display: none !important; }

/* ── Main content area ── */
.main-content {
    background-color: #0d1223;
    min-height: 100vh;
    padding: 32px 40px;
}

/* ── Stat Cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 28px;
}
.stat-card {
    background: linear-gradient(135deg, #111827 0%, #0f1520 100%);
    border: 1px solid rgba(100, 149, 237, 0.18);
    border-radius: 14px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.stat-card:hover {
    transform: translateY(-2px);
    border-color: rgba(100, 149, 237, 0.35);
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 14px 14px 0 0;
}
.stat-card.blue::before { background: linear-gradient(90deg, #3b82f6, #6495ed); }
.stat-card.teal::before { background: linear-gradient(90deg, #14b8a6, #2dd4bf); }
.stat-card.amber::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.stat-card.rose::before { background: linear-gradient(90deg, #f43f5e, #fb7185); }

.stat-label {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #4a5a7a;
    margin-bottom: 8px;
}
.stat-value {
    font-family: 'DM Serif Display', serif;
    font-size: 30px;
    color: #e2e8f4;
    line-height: 1;
    margin-bottom: 6px;
}
.stat-sub {
    font-size: 12px;
    color: #4a6a8a;
}
.stat-icon {
    position: absolute;
    top: 18px; right: 18px;
    font-size: 22px;
    opacity: 0.25;
}

/* ── Section Headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}
.section-title {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4a5a7a;
}
.section-line {
    flex: 1;
    height: 1px;
    background: rgba(100, 149, 237, 0.12);
}

/* ── Chat Messages ── */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 20px;
    max-height: 480px;
    overflow-y: auto;
    padding-right: 6px;
    scrollbar-width: thin;
    scrollbar-color: rgba(100, 149, 237, 0.2) transparent;
}
.chat-bubble {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    animation: fadeSlideIn 0.3s ease;
}
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.chat-bubble.user { flex-direction: row-reverse; }

.chat-avatar {
    width: 34px; height: 34px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
    font-weight: 600;
}
.chat-avatar.user-av {
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    color: white;
}
.chat-avatar.ai-av {
    background: linear-gradient(135deg, #0f766e, #14b8a6);
    color: white;
    font-size: 16px;
}

.chat-body {
    max-width: 78%;
}
.chat-meta {
    font-size: 11px;
    color: #3a4a6a;
    margin-bottom: 5px;
    font-weight: 500;
    letter-spacing: 0.04em;
}
.chat-bubble.user .chat-meta { text-align: right; }

.chat-text {
    padding: 13px 16px;
    border-radius: 14px;
    font-size: 14px;
    line-height: 1.65;
    color: #c8d5ed;
}
.chat-text.user-msg {
    background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(99,102,241,0.15));
    border: 1px solid rgba(99,102,241,0.25);
    border-top-right-radius: 4px;
}
.chat-text.ai-msg {
    background: linear-gradient(135deg, #111827, #0f1829);
    border: 1px solid rgba(100, 149, 237, 0.15);
    border-top-left-radius: 4px;
}

/* ── Source Tag ── */
.source-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    margin-top: 8px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
    background: rgba(20, 184, 166, 0.1);
    border: 1px solid rgba(20, 184, 166, 0.2);
    color: #2dd4bf;
}

/* ── Input Area ── */
.stTextInput > div > div > input,
.stChatInput textarea,
[data-testid="stChatInput"] textarea {
    background: #0d1223 !important;
    border: 1px solid rgba(100, 149, 237, 0.2) !important;
    border-radius: 14px !important;
    color: #e2e8f4 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 14px 20px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stChatInput"] textarea:focus,
.stTextInput > div > div > input:focus {
    border-color: rgba(100, 149, 237, 0.5) !important;
    box-shadow: 0 0 0 3px rgba(100, 149, 237, 0.08) !important;
    outline: none !important;
}
[data-testid="stChatInputSubmitButton"] button {
    background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
}

/* ── Status / Spinner ── */
[data-testid="stStatusWidget"] {
    background: #111827 !important;
    border: 1px solid rgba(100, 149, 237, 0.2) !important;
    border-radius: 12px !important;
    color: #8a9bbf !important;
    font-size: 13px !important;
}

/* ── Sidebar Logo Area ── */
.sidebar-logo {
    padding: 28px 20px 20px;
    border-bottom: 1px solid rgba(100, 149, 237, 0.1);
    margin-bottom: 8px;
}
.sidebar-app-name {
    font-size: 13px;
    font-weight: 600;
    color: #e2e8f4;
    letter-spacing: 0.02em;
    margin-top: 10px;
    display: block;
}
.sidebar-app-sub {
    font-size: 11px;
    color: #3a4a6a;
    margin-top: 2px;
    display: block;
}
.sidebar-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-top: 10px;
    padding: 3px 8px;
    background: rgba(20, 184, 166, 0.12);
    border: 1px solid rgba(20, 184, 166, 0.25);
    border-radius: 20px;
    font-size: 10px;
    font-weight: 600;
    color: #2dd4bf;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.sidebar-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: #2dd4bf;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── Page title ── */
.page-header {
    margin-bottom: 28px;
}
.page-title {
    font-family: 'DM Serif Display', serif;
    font-size: 28px;
    color: #e2e8f4;
    margin: 0 0 4px;
    line-height: 1.2;
}
.page-subtitle {
    font-size: 13px;
    color: #3a4a6a;
}

/* ── Info Panel ── */
.info-panel {
    background: linear-gradient(135deg, #0c1520, #091220);
    border: 1px solid rgba(100, 149, 237, 0.15);
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 20px;
}
.info-panel-title {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #3b82f6;
    margin-bottom: 10px;
}
.knowledge-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(100, 149, 237, 0.07);
    font-size: 12px;
    color: #6a7a9a;
}
.knowledge-item:last-child { border-bottom: none; }
.knowledge-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #3b82f6;
    flex-shrink: 0;
}

/* ── Settings Page ── */
.settings-group {
    background: #111827;
    border: 1px solid rgba(100, 149, 237, 0.12);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
}
.settings-group-title {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #3b82f6;
    margin-bottom: 14px;
}
.stSlider > div > div { background: rgba(100, 149, 237, 0.2) !important; }
.stSlider > div > div > div { background: #3b82f6 !important; }
.stCheckbox label { color: #8a9bbf !important; font-size: 14px !important; }

/* ── Subheader override ── */
h1, h2, h3 {
    font-family: 'DM Serif Display', serif !important;
    color: #e2e8f4 !important;
}
.stSubheader { color: #e2e8f4 !important; }

/* ── Search Page ── */
.search-hint {
    font-size: 12px;
    color: #3a4a6a;
    margin-top: 6px;
    padding-left: 2px;
}

/* ── Divider ── */
hr { border-color: rgba(100, 149, 237, 0.1) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(100, 149, 237, 0.2); border-radius: 4px; }

</style>
""", unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- ASYNC AGENT WRAPPER ---
async def call_agent(query):
    APP_NAME = "alzheimer_app"
    runner = InMemoryRunner(agent=coordinator, app_name=APP_NAME)
    USER_ID = "navneet_user"
    SESSION_ID = "alzheimer_session_001"
    await runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    user_message = types.Content(role='user', parts=[types.Part(text=query)])
    event_stream = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=user_message)
    final_text = ""
    async for event in event_stream:
        if event.is_final_response() and event.content:
            final_text = event.content.parts[0].text
    return final_text

# ─────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <img src="https://cdn-icons-png.flaticon.com/512/2491/2491314.png" width="44" style="opacity:0.9; filter: drop-shadow(0 0 8px rgba(100,149,237,0.4));">
        <span class="sidebar-app-name">Clinical Intelligence</span>
        <span class="sidebar-app-sub">Alzheimer's Research System</span>
        <div class="sidebar-badge">
            <div class="sidebar-dot"></div>
            Live · 2026
        </div>
    </div>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "Navigation",
        [" Dashboard", "  Search", "  Reports", "  Settings"],
        label_visibility="hidden"
    )

    st.divider()

    st.markdown("""
    <div class="info-panel">
        <div class="info-panel-title">Knowledge Vault</div>
        <div class="knowledge-item">
            <div class="knowledge-dot"></div>
            alzheimers-facts-2024.pdf
        </div>
        <div class="knowledge-item">
            <div class="knowledge-dot" style="background:#2dd4bf"></div>
            2025-special-report.pdf
        </div>
        <div class="knowledge-item">
            <div class="knowledge-dot" style="background:#f59e0b"></div>
            Live Web Search
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
#  MAIN CONTENT
# ─────────────────────────────────────────
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# ── DASHBOARD ──────────────────────────
if "Dashboard" in menu:

    st.markdown("""
    <div class="page-header">
        <p class="page-title"> Alzheimer's Hybrid Agentic System</p>
        <p class="page-subtitle">Combined RAG (Internal Archive) + Live Web Search · Updated April 2026</p>
    </div>
    """, unsafe_allow_html=True)

    # Stat cards
    st.markdown("""
    <div class="stat-grid">
        <div class="stat-card blue">
            <div class="stat-icon"></div>
            <div class="stat-label">Global Prevalence</div>
            <div class="stat-value">6.9M</div>
            <div class="stat-sub">Americans aged 65+ · 2024</div>
        </div>
        <div class="stat-card teal">
            <div class="stat-icon"></div>
            <div class="stat-label">Documents Indexed</div>
            <div class="stat-value">2</div>
            <div class="stat-sub">PDF reports · RAG active</div>
        </div>
        <div class="stat-card amber">
            <div class="stat-icon"></div>
            <div class="stat-label">Data Sources</div>
            <div class="stat-value">Hybrid</div>
            <div class="stat-sub">Archive + Live web 2026</div>
        </div>
        <div class="stat-card rose">
            <div class="stat-icon"></div>
            <div class="stat-label">Session Queries</div>
            <div class="stat-value">{count}</div>
            <div class="stat-sub">This session</div>
        </div>
    </div>
    """.format(count=len([m for m in st.session_state.messages if m["role"] == "user"])), unsafe_allow_html=True)

    # Chat history
    st.markdown("""
    <div class="section-header">
        <span class="section-title">Clinical Analysis</span>
        <div class="section-line"></div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.messages:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-bubble user">
                    <div class="chat-avatar user-av">U</div>
                    <div class="chat-body">
                        <div class="chat-meta">You</div>
                        <div class="chat-text user-msg">{msg['content']}</div>
                    </div>
                </div>"""
            else:
                content = msg['content'].replace('\n', '<br>')
                chat_html += f"""
                <div class="chat-bubble">
                    <div class="chat-avatar ai-av">⚕</div>
                    <div class="chat-body">
                        <div class="chat-meta">Clinical AI</div>
                        <div class="chat-text ai-msg">{content}</div>
                        <div class="source-tag">
                            <span style="width:5px;height:5px;border-radius:50%;background:#2dd4bf;display:inline-block"></span>
                            RAG + Live Search
                        </div>
                    </div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center;
                    padding: 60px 20px; opacity: 0.4;">
            <div style="font-size: 40px; margin-bottom: 12px;"></div>
            <div style="font-size: 14px; color: #4a5a7a; text-align: center; line-height: 1.6;">
                Ask a clinical question to begin your research.<br>
                The system will query internal PDFs and live 2026 data.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Input
    if prompt := st.chat_input("Ask a clinical question about Alzheimer's..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.status(" Orchestrating research agents...", expanded=True) as status:
            st.write(" Librarian scanning internal PDFs...")
            response = asyncio.run(call_agent(prompt))
            st.write(" Researcher verifying live 2026 evidence...")
            status.update(label=" Analysis complete", state="complete")
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# ── SEARCH ─────────────────────────────
elif "Search" in menu:
    st.markdown("""
    <div class="page-header">
        <p class="page-title">🔍 Deep Archive Search</p>
        <p class="page-subtitle">Full-text search across indexed PDF documents</p>
    </div>
    """, unsafe_allow_html=True)

    kw = st.text_input("", placeholder="Search keyword or clinical term...")
    st.markdown('<p class="search-hint">Searches: alzheimers-facts-2024.pdf · 2025-special-report.pdf</p>', unsafe_allow_html=True)

    if kw:
        st.markdown(f"""
        <div class="settings-group" style="margin-top:16px">
            <div class="settings-group-title">Search Results</div>
            <div style="color:#4a5a7a; font-size:13px; padding:12px 0;">
                No results yet — connect to your RAG pipeline to retrieve matches for
                <span style="color:#6495ed; font-weight:500;">"{kw}"</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── REPORTS ────────────────────────────
elif "Reports" in menu:
    st.markdown("""
    <div class="page-header">
        <p class="page-title"> Knowledge Vault</p>
        <p class="page-subtitle">Loaded documents available for retrieval-augmented queries</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="settings-group">
        <div class="settings-group-title">Indexed Documents</div>
        <div class="knowledge-item" style="padding:12px 0;">
            <div class="knowledge-dot"></div>
            <div>
                <div style="font-size:13px; color:#c8d5ed; font-weight:500;">alzheimers-facts-and-figures-2024.pdf</div>
                <div style="font-size:11px; color:#3a4a6a; margin-top:2px;">Alzheimer's Association · 2024 Annual Report · Indexed ✓</div>
            </div>
        </div>
        <div class="knowledge-item" style="padding:12px 0;">
            <div class="knowledge-dot" style="background:#2dd4bf"></div>
            <div>
                <div style="font-size:13px; color:#c8d5ed; font-weight:500;">2025-special-report.pdf</div>
                <div style="font-size:11px; color:#3a4a6a; margin-top:2px;">Alzheimer's Association · Special Report 2025 · Indexed ✓</div>
            </div>
        </div>
    </div>

    <div class="settings-group">
        <div class="settings-group-title">Live Web Retrieval</div>
        <div style="font-size:13px; color:#6a7a9a; line-height:1.7;">
            Hybrid agent will supplement archived knowledge with live 2026 web data when queries 
            require up-to-date clinical findings, trial results, or recent statistics.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── SETTINGS ───────────────────────────
elif "Settings" in menu:
    st.markdown("""
    <div class="page-header">
        <p class="page-title"> System Configuration</p>
        <p class="page-subtitle">Tune retrieval and inference parameters</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="settings-group"><div class="settings-group-title">Retrieval Parameters</div>', unsafe_allow_html=True)
    lam = st.slider("Retrieval Sensitivity (Lambda)", 0.0, 1.0, 0.7, step=0.05)
    st.markdown(f'<p style="font-size:12px; color:#3a4a6a; margin-top:-8px; margin-bottom:12px;">Higher values weight archived PDFs more heavily over live web search.</p>', unsafe_allow_html=True)
    top_k = st.slider("Top-K Document Chunks", 1, 20, 5, step=1)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="settings-group"><div class="settings-group-title">Agent Configuration</div>', unsafe_allow_html=True)
    web_on = st.checkbox("Enable Live Web Researcher (2026)", value=True)
    rag_on = st.checkbox("Enable Internal RAG Librarian", value=True)
    verbose = st.checkbox("Verbose Agent Logging", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button(" Save Configuration"):
        st.success("Configuration saved.")

st.markdown('</div>', unsafe_allow_html=True)