def get_custom_css() -> str:
    return """
<style>

@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600;8..60,700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --paper: #1C2420;
    --paper-deep: #141B17;
    --card: #25302B;
    --ink: #E8E4D9;
    --ink-soft: #A39E92;
    --amber: #D4A24E;
    --amber-deep: #E8BC6F;
    --sage: #7FA66B;
    --sage-deep: #9BC489;
    --brick: #C16B5E;
    --brick-deep: #D98A7D;
    --slate: #8A9B9E;
    --line: #34423B;
    --line-deep: #455349;
}

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

.stApp {
    background:
        repeating-linear-gradient(0deg, transparent, transparent 27px, rgba(122,139,153,0.05) 28px),
        var(--paper);
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Always show sidebar collapse/expand toggle ───────────────── */
/* Always show sidebar toggle arrow */
/* Hide sidebar collapse arrow so it can never be accidentally hidden */
/* Hide the collapse button */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

/* Prevent sidebar from collapsing */
section[data-testid="stSidebar"] {
    min-width: 300px !important;
    max-width: 300px !important;
}

/* ── Typography ───────────────────────────────────────────── */
h1, h2, h3 {
    font-family: 'Source Serif 4', serif !important;
    color: var(--ink) !important;
    letter-spacing: -0.01em;
}
h1 { font-weight: 600 !important; font-size: 2.3rem !important; }
h2, h3 { font-weight: 500 !important; }
p, span, label, div { color: var(--ink); }

.eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--amber-deep);
    display: inline-block;
    margin-bottom: 6px;
    padding: 3px 10px;
    background: rgba(217,142,62,0.12);
    border-radius: 3px;
}

/* ── Page load animation ─────────────────────────────────────── */
@keyframes riseIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
.block-container { animation: riseIn 0.45s ease-out; }

/* ── Sidebar — looks like a notebook spine ───────────────────── */
section[data-testid="stSidebar"] {
    background: var(--paper-deep) !important;
    border-right: 2px solid var(--line-deep);
}
section[data-testid="stSidebar"] [role="radiogroup"] label {
    background: transparent;
    border-radius: 6px;
    padding: 11px 14px !important;
    margin-bottom: 6px;
    border-left: 3px solid transparent;
    transition: all 0.18s ease;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: var(--card);
    border-left-color: var(--amber);
}
section[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
    background: var(--card);
    border-left-color: var(--amber);
}

/* ── Buttons — tactile, slightly raised ──────────────────────── */
.stButton button {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    border-radius: 7px;
    border: 1.5px solid var(--line-deep);
    background: var(--card);
    color: var(--ink);
    box-shadow: 0 2px 0 var(--line-deep);
    transition: all 0.12s ease;
    padding: 0.5rem 1.2rem;
}
.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 0 var(--line-deep);
}
.stButton button:active {
    transform: translateY(1px);
    box-shadow: 0 1px 0 var(--line-deep);
}
.stButton button[kind="primary"] {
    background: var(--amber);
    color: var(--card);
    border-color: var(--amber-deep);
    box-shadow: 0 2px 0 var(--amber-deep);
}
.stButton button[kind="primary"]:hover {
    box-shadow: 0 4px 0 var(--amber-deep);
}

/* ── Inputs ───────────────────────────────────────────────── */
.stTextInput input, .stSelectbox > div, .stTextArea textarea {
    background: var(--card) !important;
    border: 1.5px solid var(--line-deep) !important;
    border-radius: 7px !important;
    color: var(--ink) !important;
}
.stTextInput input:focus {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 2px rgba(217,142,62,0.25) !important;
}
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background-color: var(--amber) !important;
    border: 2px solid var(--card) !important;
}

/* ── Notebook page card (explanation / summary output) ───────── */
.notebook-page {
    background: var(--card);
    border: 1px solid var(--line-deep);
    border-radius: 4px;
    padding: 32px 36px 32px 56px;
    margin: 18px 0;
    position: relative;
    animation: riseIn 0.4s ease-out;
    box-shadow: 3px 3px 0 var(--line);
}
.notebook-page::before {
    content: "";
    position: absolute;
    left: 32px; top: 0; bottom: 0;
    width: 1.5px;
    background: var(--brick);
    opacity: 0.35;
}
.notebook-page::after {
    content: "";
    position: absolute;
    top: 14px; left: -6px;
    width: 26px; height: 26px;
    background: var(--slate);
    opacity: 0.85;
    border-radius: 2px;
    transform: rotate(-8deg);
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

/* ── Metrics ──────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--card);
    border: 1.5px solid var(--line-deep);
    border-radius: 8px;
    padding: 14px 16px;
    box-shadow: 2px 2px 0 var(--line);
    transition: transform 0.15s ease;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); }
[data-testid="stMetricValue"] {
    font-family: 'Source Serif 4', serif !important;
    color: var(--amber-deep) !important;
}

/* ── Alerts ───────────────────────────────────────────────── */
.stAlert { border-radius: 7px !important; animation: riseIn 0.3s ease-out; }

.streamlit-expanderHeader {
    background: var(--card) !important;
    border-radius: 6px !important;
    border: 1.5px solid var(--line-deep) !important;
}

.stProgress > div > div > div {
    background: var(--amber) !important;
}

/* ══════════════════════════════════════════════════════════
   SIGNATURE — INDEX CARD FLASHCARD
   ══════════════════════════════════════════════════════════ */
.card-stack-wrap {
    perspective: 1400px;
    margin: 22px 0 12px 0;
    position: relative;
}

/* ghost cards peeking behind, like a real stack */
.card-stack-wrap::before, .card-stack-wrap::after {
    content: "";
    position: absolute;
    background: var(--card);
    border: 1.5px solid var(--line-deep);
    border-radius: 10px;
    inset: 0;
    z-index: 0;
}
.card-stack-wrap::before { transform: rotate(-3deg) translateY(4px); opacity: 0.7; }
.card-stack-wrap::after { transform: rotate(2.5deg) translateY(3px); opacity: 0.5; }

.index-card {
    position: relative;
    width: 100%;
    min-height: 230px;
    transition: transform 0.55s cubic-bezier(0.4,0.2,0.2,1);
    transform-style: preserve-3d;
    z-index: 1;
}
.index-card.flipped { transform: rotateY(180deg); }

.index-face {
    position: absolute;
    inset: 0;
    backface-visibility: hidden;
    border-radius: 10px;
    padding: 32px 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    border: 1.5px solid var(--line-deep);
}

.index-face-front {
    background:
        repeating-linear-gradient(0deg, transparent, transparent 31px, rgba(180,72,61,0.07) 32px),
        var(--card);
    box-shadow: 3px 4px 0 var(--line-deep);
}
.index-face-front::before {
    content: "";
    position: absolute;
    top: 0; bottom: 0; left: 26px;
    width: 1.5px;
    background: var(--brick);
    opacity: 0.3;
}
.index-face-front::after {
    content: "TURN OVER →";
    position: absolute;
    bottom: 14px; right: 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.1em;
    color: var(--slate);
    opacity: 0.8;
}

.index-face-back {
    background: #EEF2EA;
    border-color: var(--sage-deep);
    transform: rotateY(180deg);
    box-shadow: 3px 4px 0 var(--sage-deep);
}

.index-face p {
    font-family: 'Source Serif 4', serif;
    font-size: 1.3rem;
    font-weight: 500;
    line-height: 1.5;
    margin: 0;
    padding-left: 14px;
}
.index-face-back p {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.02rem;
    font-weight: 400;
    color: var(--sage-deep);
}

.card-progress-dots {
    display: flex;
    gap: 6px;
    justify-content: center;
    margin: 10px 0 18px 0;
}
.dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--line-deep);
    transition: all 0.25s ease;
}
.dot.active {
    background: var(--amber-deep);
    width: 20px;
    border-radius: 4px;
}

/* ══════════════════════════════════════════════════════════
   SCORE STAMP — quiz result, like an ink stamp
   ══════════════════════════════════════════════════════════ */
.score-stamp-wrap {
    display: flex;
    justify-content: center;
    margin: 22px 0;
}
.score-stamp {
    width: 150px; height: 150px;
    border-radius: 50%;
    border: 4px double currentColor;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transform: rotate(-6deg);
    animation: stampIn 0.4s cubic-bezier(0.3,1.4,0.5,1);
}
@keyframes stampIn {
    from { transform: rotate(-6deg) scale(0.4); opacity: 0; }
    to   { transform: rotate(-6deg) scale(1); opacity: 1; }
}
.score-stamp .pct {
    font-family: 'Source Serif 4', serif;
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1;
}
.score-stamp .label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 4px;
}
.score-stamp.pass { color: var(--sage-deep); }
.score-stamp.fail { color: var(--brick-deep); }

/* ── Hero header ──────────────────────────────────────────── */
.page-hero {
    border-bottom: 2px solid var(--line-deep);
    padding-bottom: 18px;
    margin-bottom: 26px;
    animation: riseIn 0.4s ease-out;
}
.page-hero h1 { margin-bottom: 4px !important; }
.page-hero .subtitle { color: var(--ink-soft); font-size: 0.98rem; }

hr { border-color: var(--line-deep) !important; opacity: 0.6; }

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--paper); }
::-webkit-scrollbar-thumb { background: var(--line-deep); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--amber-deep); }

/* ══════════════════════════════════════════════════════════
   STUDY STREAK WIDGET
   ══════════════════════════════════════════════════════════ */
.streak-badge-wrap {
    display: flex;
    align-items: center;
    gap: 14px;
    background: var(--card);
    border: 1.5px solid var(--line-deep);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 18px;
    animation: riseIn 0.4s ease-out;
}

.streak-flame {
    font-size: 2.4rem;
    line-height: 1;
    animation: flicker 2.4s ease-in-out infinite;
    filter: drop-shadow(0 0 6px rgba(212,162,78,0.4));
}

@keyframes flicker {
    0%, 100% { transform: scale(1) rotate(0deg); }
    25% { transform: scale(1.05) rotate(-2deg); }
    50% { transform: scale(0.97) rotate(1deg); }
    75% { transform: scale(1.03) rotate(-1deg); }
}

.streak-flame.cold {
    filter: grayscale(1) opacity(0.4);
    animation: none;
}

.streak-count {
    font-family: 'Source Serif 4', serif;
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--amber-deep);
    line-height: 1;
}

.streak-text {
    font-size: 0.88rem;
    color: var(--ink-soft);
    margin-top: 2px;
}

.streak-sidebar-mini {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--card);
    border: 1px solid var(--line-deep);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 14px;
}

.streak-sidebar-mini .flame-mini { font-size: 1.3rem; }
.streak-sidebar-mini .num {
    font-family: 'Source Serif 4', serif;
    font-weight: 700;
    font-size: 1.1rem;
    color: var(--amber-deep);
}
.streak-sidebar-mini .txt {
    font-size: 0.72rem;
    color: var(--ink-soft);
    letter-spacing: 0.02em;
}

/* GitHub-style activity grid */
.activity-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 5px;
    margin: 16px 0;
}

.activity-cell {
    aspect-ratio: 1;
    border-radius: 4px;
    background: var(--line);
    border: 1px solid var(--line-deep);
    transition: transform 0.15s ease;
}

.activity-cell.studied {
    background: var(--amber-deep);
    border-color: var(--amber);
}

.activity-cell:hover {
    transform: scale(1.15);
}

.activity-legend {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    color: var(--ink-soft);
    margin-top: 6px;
}
.activity-legend .swatch {
    width: 12px; height: 12px;
    border-radius: 3px;
    display: inline-block;
}

</style>
"""