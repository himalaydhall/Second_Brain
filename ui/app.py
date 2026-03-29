# ─────────────────────────────────────────────────────────────────
#  ui/app.py  —  Second Brain  |  Redesigned UI
#  Run with:  streamlit run ui/app.py
# ─────────────────────────────────────────────────────────────────

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import json
import re
from datetime import datetime

import config
from agent.prompts import (
    SIMPLE_SYNTHESIS_PROMPT,
    COMPARE_SYNTHESIS_PROMPT,
    CONTRADICT_SYNTHESIS_PROMPT,
)

# ─── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title  = "Second Brain",
    page_icon   = "🧠",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

# ─── Global CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0a0a !important;
    color: #e8e0d5 !important;
    font-family: 'DM Sans', sans-serif;
}

#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], .stDeployButton { display: none !important; }

[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 1px solid #1e1e1e !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }

.sidebar-header {
    padding: 2rem 1.5rem 1rem;
    border-bottom: 1px solid #1e1e1e;
    margin-bottom: 1rem;
}
.sidebar-logo {
    font-family: 'Instrument Serif', serif;
    font-size: 1.6rem;
    color: #e8e0d5;
    letter-spacing: -0.02em;
    line-height: 1;
}
.sidebar-logo span { color: #c4a35a; }
.sidebar-tagline {
    font-size: 0.72rem;
    color: #555;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.35rem;
    font-family: 'DM Mono', monospace;
}
.sidebar-section { padding: 0.75rem 1.5rem; margin-bottom: 0.25rem; }
.sidebar-section-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 0.75rem;
}
.stat-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem; }
.stat-label { font-size: 0.8rem; color: #777; }
.stat-value { font-family: 'DM Mono', monospace; font-size: 0.85rem; color: #c4a35a; font-weight: 500; }
.period-chip {
    display: inline-block;
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 3px;
    padding: 0.2rem 0.5rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #888;
    margin: 0.15rem 0.15rem 0.15rem 0;
}
.topic-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.2rem 0;
    border-bottom: 1px solid #181818;
}
.topic-name { font-size: 0.78rem; color: #999; }
.topic-count { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: #444; }

[data-testid="stMainBlockContainer"] {
    max-width: 820px !important;
    margin: 0 auto !important;
    padding: 2rem 1.5rem !important;
}

.hero { text-align: center; padding: 4rem 0 3rem; }
.hero-title {
    font-family: 'Instrument Serif', serif;
    font-size: 3.2rem;
    color: #e8e0d5;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 0.5rem;
}
.hero-title em { color: #c4a35a; font-style: italic; }
.hero-subtitle {
    font-size: 0.9rem;
    color: #555;
    max-width: 420px;
    margin: 0 auto 2.5rem;
    line-height: 1.6;
}

.msg-user { display: flex; justify-content: flex-end; margin-bottom: 1rem; }
.msg-user-bubble {
    background: #161616;
    border: 1px solid #222;
    border-radius: 16px 16px 4px 16px;
    padding: 0.75rem 1.1rem;
    max-width: 75%;
    font-size: 0.9rem;
    color: #ccc;
    line-height: 1.5;
}
.msg-assistant { display: flex; gap: 0.75rem; align-items: flex-start; margin-bottom: 0.5rem; }
.msg-avatar {
    width: 28px; height: 28px;
    background: linear-gradient(135deg, #c4a35a22, #c4a35a44);
    border: 1px solid #c4a35a44;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; flex-shrink: 0; margin-top: 2px;
}
.msg-content { flex: 1; min-width: 0; }
.msg-meta { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem; }
.msg-name {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem; color: #444;
    letter-spacing: 0.05em; text-transform: uppercase;
}
.mode-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.mode-simple   { background: #1a2a1a; color: #5a9a5a; border: 1px solid #2a3a2a; }
.mode-compare  { background: #1a1a2a; color: #5a7ac4; border: 1px solid #2a2a3a; }
.mode-contradict { background: #2a1a1a; color: #c45a5a; border: 1px solid #3a2a2a; }

.sources-row {
    display: flex; flex-wrap: wrap; gap: 0.35rem;
    margin-top: 0.75rem; padding-top: 0.75rem;
    border-top: 1px solid #1e1e1e;
}
.source-tag {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: #131313; border: 1px solid #2a2a2a;
    border-radius: 4px; padding: 0.2rem 0.5rem;
    font-family: 'DM Mono', monospace; font-size: 0.68rem; color: #666;
}
.source-dot { width: 5px; height: 5px; background: #c4a35a; border-radius: 50%; opacity: 0.6; }

.chat-divider { border: none; border-top: 1px solid #181818; margin: 1.5rem 0; }

[data-testid="stChatInput"] {
    background: #111 !important; border: 1px solid #222 !important;
    border-radius: 12px !important; color: #e8e0d5 !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #c4a35a44 !important;
    box-shadow: 0 0 0 3px #c4a35a11 !important;
}
[data-testid="stChatInputSubmitButton"] { color: #c4a35a !important; }

.stButton > button {
    background: #111 !important; border: 1px solid #222 !important;
    color: #888 !important; border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.8rem !important;
    transition: all 0.15s !important; width: 100% !important;
}
.stButton > button:hover {
    border-color: #c4a35a44 !important; color: #c4a35a !important;
    background: #161616 !important;
}
.stToggle > label { color: #888 !important; font-size: 0.82rem !important; }
.stSpinner > div { border-color: #c4a35a transparent transparent transparent !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 2px; }

.thinking { display: flex; gap: 4px; align-items: center; padding: 0.5rem 0; }
.thinking-dot {
    width: 6px; height: 6px; background: #c4a35a;
    border-radius: 50%; animation: pulse 1.2s infinite; opacity: 0.4;
}
.thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse {
    0%, 100% { opacity: 0.2; transform: scale(0.8); }
    50% { opacity: 1; transform: scale(1.1); }
}
.llm-info {
    font-family: 'DM Mono', monospace; font-size: 0.68rem;
    color: #444; padding: 0 1.5rem 1rem; line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────

def extract_sources(text: str) -> list:
    return list(dict.fromkeys(re.findall(r'\[([^\]]+\.pdf)\]', text)))

def render_sources(sources: list) -> str:
    if not sources:
        return ""
    tags = "".join(
        f'<span class="source-tag"><span class="source-dot"></span>{s}</span>'
        for s in sources
    )
    return f'<div class="sources-row">{tags}</div>'

def mode_badge(mode: str) -> str:
    icons = {"simple": "◆", "compare": "⬡", "contradict": "⚡"}
    return f'<span class="mode-badge mode-{mode}">{icons.get(mode, "·")} {mode}</span>'

def get_library_stats():
    try:
        from agent.tools import list_available_periods, list_topics
        periods = json.loads(list_available_periods())
        topics  = json.loads(list_topics())
        total   = sum(p["chunk_count"] for p in periods)
        return periods, topics, total
    except Exception:
        return [], [], 0


# ─── Session state ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "hitl_enabled" not in st.session_state:
    st.session_state.hitl_enabled = False
if "quick_query" not in st.session_state:
    st.session_state.quick_query = None


# ─── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div class="sidebar-logo">Second <span>Brain</span></div>
        <div class="sidebar-tagline">PDF Insight Surfer</div>
    </div>
    """, unsafe_allow_html=True)

    periods, topics, total_chunks = get_library_stats()

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-title">Library</div>', unsafe_allow_html=True)

    if total_chunks:
        st.markdown(f"""
        <div class="stat-row">
            <span class="stat-label">Indexed chunks</span>
            <span class="stat-value">{total_chunks:,}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Time periods</span>
            <span class="stat-value">{len(periods)}</span>
        </div>
        """, unsafe_allow_html=True)
        period_html = "".join(
            f'<span class="period-chip">{p["period"]}</span>'
            for p in sorted(periods, key=lambda x: x["period"], reverse=True)[:8]
        )
        st.markdown(f'<div style="margin-top:0.5rem">{period_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="stat-label">No PDFs indexed yet.</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if topics:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section-title">Topics</div>', unsafe_allow_html=True)
        for t in topics[:8]:
            st.markdown(f"""
            <div class="topic-row">
                <span class="topic-name">{t['topic']}</span>
                <span class="topic-count">{t['chunk_count']}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-title">Settings</div>', unsafe_allow_html=True)
    st.session_state.hitl_enabled = st.toggle(
        "Human-in-the-Loop",
        value=st.session_state.hitl_enabled,
        help="Agent pauses to ask you before resolving conflicts",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="llm-info">
        LLM &nbsp;·&nbsp; {config.LLM_PROVIDER.upper()}<br>
        Embed &nbsp;·&nbsp; {config.EMBEDDING_PROVIDER}
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-title">Actions</div>', unsafe_allow_html=True)
    if st.button("🗑  Clear conversation"):
        st.session_state.messages = []
        st.rerun()
    if st.button("📋  List all topics"):
        st.session_state.quick_query = "What topics are covered across all my notes?"
    if st.button("🔀  Find contradictions"):
        st.session_state.quick_query = "What are the biggest contradictions across my notes over time?"
    st.markdown('</div>', unsafe_allow_html=True)


# ─── Main area ────────────────────────────────────────────────────

if not st.session_state.messages:
    st.markdown("""
    <div class="hero">
        <div class="hero-title">Your notes,<br><em>reasoned</em>.</div>
        <div class="hero-subtitle">
            Ask anything about your PDF library. Second Brain searches,
            compares, and surfaces contradictions across your notes.
        </div>
    </div>
    """, unsafe_allow_html=True)

    suggestions = [
        ("◆", "What is alpha-beta pruning?"),
        ("⬡", "Compare A* and minimax algorithms"),
        ("◆", "How does the genetic algorithm avoid conflicts?"),
        ("⬡", "What search algorithms are in my notes?"),
    ]
    cols = st.columns(2)
    for i, (icon, text) in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(f"{icon}  {text}", key=f"sug_{i}"):
                st.session_state.quick_query = text

# Render history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="msg-user">
            <div class="msg-user-bubble">{msg['content']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        sources  = extract_sources(msg["content"])
        badge    = mode_badge(msg.get("mode", "simple"))
        src_html = render_sources(sources)
        st.markdown(f"""
        <div class="msg-assistant">
            <div class="msg-avatar">🧠</div>
            <div class="msg-content">
                <div class="msg-meta">
                    <span class="msg-name">Second Brain</span>
                    {badge}
                </div>
        """, unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown(f"{src_html}</div></div><hr class='chat-divider'>", unsafe_allow_html=True)


# ─── Query handling ───────────────────────────────────────────────
query = st.chat_input("Ask your Second Brain...") or st.session_state.pop("quick_query", None)

if query:
    st.markdown(f"""
    <div class="msg-user">
        <div class="msg-user-bubble">{query}</div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": query})

    st.markdown("""
    <div class="msg-assistant">
        <div class="msg-avatar">🧠</div>
        <div class="msg-content">
            <div class="msg-meta"><span class="msg-name">Second Brain</span></div>
    """, unsafe_allow_html=True)

    placeholder = st.empty()
    placeholder.markdown("""
    <div class="thinking">
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
    </div>
    """, unsafe_allow_html=True)

    try:
        from agent.workflow import (
            classify_query, get_llm_for_mode,
            search_simple, search_compare, search_contradict,
            maybe_clarify, _setup,
        )
        _setup()
        classify_llm = config.get_llm()
        mode         = classify_query(classify_llm, query)
        llm          = get_llm_for_mode(mode)

        if mode == "simple":
            context = search_simple(query)
            prompt  = SIMPLE_SYNTHESIS_PROMPT.format(query=query, context=context)
        elif mode == "compare":
            context = search_compare(llm, query)
            prompt  = COMPARE_SYNTHESIS_PROMPT.format(query=query, context=context)
        else:
            context, _ = search_contradict(llm, query)
            prompt  = context

        answer = ""
        for chunk in llm.stream_complete(prompt):
            answer += chunk.delta
            placeholder.markdown(answer + "▌")
        placeholder.markdown(answer)

    except Exception as exc:
        answer = f"⚠️ **Error:** `{exc}`"
        mode   = "simple"
        placeholder.markdown(answer)

    sources  = extract_sources(answer)
    src_html = render_sources(sources)
    badge    = mode_badge(mode)

    st.markdown(f"""
        {src_html}
        </div>
    </div>
    <hr class='chat-divider'>
    """, unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant", "content": answer, "mode": mode,
    })