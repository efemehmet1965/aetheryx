"""
AETHERYX — Multi-LLM Security Intelligence Platform
Product-level Streamlit application.
"""
import streamlit as st
import streamlit.components.v1 as components
import os, sys, re, base64, json, html as _html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.key_fetcher import get_free_keys
from core.llm_router  import MultiLLMRouter

# ═══════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Aetheryx",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def _b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

LOGO = _b64("assets/log2o.png") or _b64("assets/logo.png")

def _md(text: str) -> str:
    """Lightweight markdown → safe HTML."""
    t = _html.escape(text)
    t = re.sub(r"```(\w*)\n(.*?)```",
               lambda m: f'<pre><code class="cb">{m.group(2)}</code></pre>',
               t, flags=re.DOTALL)
    t = re.sub(r"`([^`\n]+)`", r'<code class="ic">\1</code>', t)
    t = re.sub(r"^### (.+)$", r'<h4>\1</h4>', t, flags=re.MULTILINE)
    t = re.sub(r"^## (.+)$",  r'<h3>\1</h3>', t, flags=re.MULTILINE)
    t = re.sub(r"^# (.+)$",   r'<h2>\1</h2>', t, flags=re.MULTILINE)
    t = re.sub(r"\*\*(.+?)\*\*", r'<strong>\1</strong>', t)
    t = re.sub(r"\*(.+?)\*",     r'<em>\1</em>', t)
    t = re.sub(r"^[-•] (.+)$",   r'<li>\1</li>', t, flags=re.MULTILINE)
    t = re.sub(r"(<li>.*?</li>\n?)+",
               lambda m: f"<ul>{m.group(0)}</ul>", t, flags=re.DOTALL)
    t = t.replace("\n", "<br>")
    return t

# ═══════════════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;600&family=Orbitron:wght@500;700;900&display=swap');

/* ── RESET ───────────────────────────────────── */
*,*::before,*::after{box-sizing:border-box}
html,body,[class*="css"],.stMain,.main,section.main,[data-testid="stMain"]{
  font-family:'Inter',system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;
  height:100vh !important;
  max-height:100vh !important;
  overflow:hidden !important;
}
[data-testid="stAppViewContainer"] {
  height:100vh !important;
  max-height:100vh !important;
  overflow:hidden !important;
}
[data-testid="stAppViewBlockContainer"] {
  padding-top:1.0rem !important;
  padding-bottom:1.0rem !important;
  padding-left:1.5rem !important;
  padding-right:1.5rem !important;
  height:100vh !important;
  max-height:100vh !important;
  overflow:hidden !important;
  display:flex !important;
  flex-direction:column !important;
}
[data-testid="stAppViewBlockContainer"] > div {
  height:100% !important;
  display:flex !important;
  flex-direction:column !important;
}

/* ── BACKGROUND ──────────────────────────────── */
.stApp{
  background:#06080F;
  background-image:
    radial-gradient(ellipse 110% 60% at 50% -8%, rgba(88,28,220,0.22) 0%, transparent 65%),
    radial-gradient(ellipse 55% 40% at 88% 88%, rgba(180,30,220,0.11) 0%, transparent 60%),
    radial-gradient(ellipse 60% 45% at 8% 78%,  rgba(40,20,180,0.12) 0%, transparent 58%);
  background-attachment:fixed;
  color:#DCE4F5;
  height:100vh !important;
  max-height:100vh !important;
  overflow:hidden !important;
}

/* ── HIDE CHROME ─────────────────────────────── */
#MainMenu,footer,header{visibility:hidden}
.stDeployButton,[data-testid="stToolbar"]{display:none!important}
[data-testid="stDecoration"]{display:none!important}

/* ── SIDEBAR ─────────────────────────────────── */
[data-testid="stSidebar"]{
  background:rgba(5,7,15,0.98)!important;
  border-right:1px solid rgba(110,40,220,0.16)!important;
  backdrop-filter:blur(30px);
}
[data-testid="stSidebarContent"]{padding:0!important}

.sb-logo{
  width:100%;display:block;object-fit:cover;
  max-height:60px;object-position:center top;
  mask-image:linear-gradient(to bottom,#000 40%,transparent 100%);
  -webkit-mask-image:linear-gradient(to bottom,#000 40%,transparent 100%);
}
.sb-wrap{padding:2px 8px 12px}

.sb-sep{
  font-family:'Orbitron',sans-serif;font-size:0.52rem;font-weight:700;
  letter-spacing:0.16em;text-transform:uppercase;
  color:rgba(150,100,255,0.40);
  margin:8px 0 4px;padding-bottom:2px;
  border-bottom:1px solid rgba(110,40,220,0.10);
}

/* ── NAV TABS ────────────────────────────────── */
.nav-tabs{display:flex;gap:4px;margin-bottom:6px}
.nav-tab{
  flex:1;padding:6px 4px;border-radius:6px;text-align:center;cursor:pointer;
  font-family:'Orbitron',sans-serif;font-size:0.65rem;font-weight:600;
  letter-spacing:0.14em;text-transform:uppercase;
  border:1px solid rgba(110,40,220,0.14);
  background:rgba(14,10,30,0.50);color:rgba(180,150,240,0.55);
  transition:all .18s;
}
.nav-tab:hover{background:rgba(80,30,180,0.20);color:rgba(200,160,255,0.80)}
.nav-tab.active{
  background:linear-gradient(135deg,rgba(90,20,200,0.40),rgba(140,30,200,0.25));
  border-color:rgba(130,60,240,0.40);color:#C8A8FF;
}

/* ── API CARDS ───────────────────────────────── */
.api-card{
  display:flex;align-items:center;gap:6px;
  padding:4px 8px;margin-bottom:2px;border-radius:6px;
  border:1px solid rgba(110,40,220,0.08);
  background:rgba(16,10,36,0.45);
}
.api-card.on{border-color:rgba(50,220,130,0.18);background:rgba(6,24,16,0.50)}
.api-card.off{opacity:.55}
.dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.dot.on{background:#2EE89A;box-shadow:0 0 6px rgba(46,232,154,0.55);animation:pg 2.4s ease-in-out infinite}
.dot.off{background:#FF3D5C;box-shadow:0 0 4px rgba(255,61,92,0.30)}
@keyframes pg{0%,100%{opacity:1;box-shadow:0 0 8px rgba(46,232,154,.6)}50%{opacity:.65;box-shadow:0 0 3px rgba(46,232,154,.3)}}
.api-name{font-family:'JetBrains Mono',monospace;font-size:.66rem;font-weight:600;color:#B8A6EE;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.api-sub{font-size:.60rem;color:rgba(140,120,200,.40);margin-top:0px}
.api-lat{font-family:'JetBrains Mono',monospace;font-size:.60rem;flex-shrink:0}
.lat-ok{color:#2EE89A}.lat-bad{color:#FF3D5C}

.stat-row{display:flex;gap:4px;margin-top:5px}
.stat-box{flex:1;text-align:center;padding:4px 2px;border-radius:5px;
  background:rgba(16,10,36,0.50);border:1px solid rgba(110,40,220,0.10)}
.stat-val{font-family:'Orbitron',sans-serif;font-size:0.78rem;font-weight:700;
  background:linear-gradient(135deg,#9B5CF6,#EC4899);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;display:block}
.stat-lbl{font-size:.54rem;color:rgba(140,120,200,.45);text-transform:uppercase;letter-spacing:.05em;display:block;margin-top:1px}

/* ── SETTINGS PANEL ──────────────────────────── */
.setting-group{
  background:rgba(14,10,30,0.55);border:1px solid rgba(110,40,220,0.14);
  border-radius:10px;padding:14px 16px;margin-bottom:12px;
}
.setting-title{
  font-family:'Orbitron',sans-serif;font-size:.72rem;font-weight:700;
  letter-spacing:.14em;text-transform:uppercase;color:rgba(180,130,255,.75);
  margin-bottom:10px;
}
.setting-desc{font-size:.80rem;color:rgba(150,130,200,.58);margin-top:4px;line-height:1.6}

/* ── MAIN AREA ───────────────────────────────── */
.main-pad{padding-bottom:130px}

/* ── HERO ────────────────────────────────────── */
.hero{text-align:center;padding:36px 20px 16px;animation:hIn .7s cubic-bezier(.22,1,.36,1) both}
@keyframes hIn{from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:translateY(0)}}
.hero-img{
  width:240px;max-width:70%;margin:0 auto 4px;display:block;
  filter:drop-shadow(0 0 30px rgba(120,50,240,0.50));
  animation:gw 4.5s ease-in-out infinite alternate;
}
@keyframes gw{
  from{filter:drop-shadow(0 0 20px rgba(120,50,240,.45))}
  to  {filter:drop-shadow(0 0 55px rgba(190,80,255,.70)) drop-shadow(0 0 90px rgba(200,50,200,.18))}
}
.hero-sub{
  font-family:'Orbitron',sans-serif;font-size:.70rem;letter-spacing:.26em;
  text-transform:uppercase;color:rgba(140,90,240,.60);margin-top:2px;
}

/* ── EMPTY STATE ─────────────────────────────── */
.empty{text-align:center;padding:44px 24px 0;animation:hIn .5s ease both}
.empty-h{
  font-family:'Orbitron',sans-serif;font-size:.86rem;letter-spacing:.16em;
  color:rgba(140,90,240,.55);margin-bottom:14px;
}
.empty-b{font-size:.88rem;line-height:1.80;color:rgba(130,105,195,.45)}
.empty-b code{font-family:'JetBrains Mono',monospace;color:rgba(170,120,255,.40);font-size:.78rem}

/* ── MESSAGES ────────────────────────────────── */
.feed{
  max-width:800px;
  margin:0 auto;
  padding:0 18px;
  height:calc(100vh - 240px) !important;
  overflow-y:auto !important;
}
.msg{margin-bottom:26px;animation:mIn .28s cubic-bezier(.22,1,.36,1) both}
@keyframes mIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.lbl{font-family:'JetBrains Mono',monospace;font-size:.68rem;font-weight:600;
  letter-spacing:.12em;text-transform:uppercase;margin-bottom:5px;
  display:flex;align-items:center;gap:7px}
.lbl-dot{width:6px;height:6px;border-radius:50%}
.lbl-u{color:#E0449A}.dot-u{background:#E0449A;box-shadow:0 0 6px rgba(224,68,154,.55)}
.lbl-a{color:#8B5CF6}.dot-a{background:#8B5CF6;box-shadow:0 0 6px rgba(139,92,246,.55)}

.bub-u{
  background:linear-gradient(148deg,rgba(44,18,92,.62),rgba(60,16,102,.42));
  border:1px solid rgba(180,65,220,.22);border-radius:4px 16px 16px 16px;
  padding:14px 18px;font-size:.91rem;line-height:1.65;color:#EDE4FF;
  box-shadow:0 3px 18px rgba(0,0,0,.26),inset 0 1px 0 rgba(255,255,255,.04);
  word-break:break-word;
}
.bub-a{
  background:linear-gradient(148deg,rgba(10,14,30,.84),rgba(16,20,46,.70));
  border:1px solid rgba(100,65,160,.18);border-radius:16px 4px 16px 16px;
  padding:16px 20px;font-size:.91rem;line-height:1.72;color:#D5CCEE;
  box-shadow:0 5px 22px rgba(0,0,0,.30),inset 0 1px 0 rgba(255,255,255,.025);
  word-break:break-word;position:relative;overflow:hidden;
}
.bub-a::before{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(120,50,220,.28),transparent);
}
.bub-a code.ic{
  font-family:'JetBrains Mono',monospace;font-size:.80rem;
  background:rgba(0,0,0,.40);border:1px solid rgba(120,50,220,.22);
  border-radius:4px;padding:1px 6px;color:#B87FFF;
}
.bub-a pre{
  background:rgba(0,0,0,.55);border:1px solid rgba(100,45,200,.20);
  border-radius:8px;padding:14px 16px;margin:12px 0;overflow-x:auto;white-space:pre;
}
.bub-a pre code.cb{
  font-family:'JetBrains Mono',monospace;font-size:.78rem;
  color:#9CF0FF;background:transparent;border:none;padding:0;
}
.bub-a h2{font-family:'Orbitron',sans-serif;font-size:.78rem;letter-spacing:.10em;color:#D946EF;margin:16px 0 7px}
.bub-a h3{font-family:'Orbitron',sans-serif;font-size:.70rem;letter-spacing:.08em;color:#A86CFF;margin:13px 0 5px}
.bub-a h4{font-family:'Orbitron',sans-serif;font-size:.65rem;letter-spacing:.06em;color:#9055FF;margin:11px 0 4px}
.bub-a ul{padding-left:18px;margin:8px 0}.bub-a li{margin-bottom:4px}
.bub-a strong{color:#E2D4FF;font-weight:600}.bub-a em{color:#C0AEFF;font-style:italic}

/* ── INPUT HINT ──────────────────────────────── */
.inp-hint{font-family:'JetBrains Mono',monospace;font-size:.68rem;color:rgba(140,110,200,.42);display:flex;align-items:center;gap:6px;flex-wrap:wrap}

/* ── BUTTONS (main content area only) ───────── */
[data-testid="stMain"] .stButton>button,
section.main .stButton>button{
  background:linear-gradient(135deg,#5B1FCC,#8A28CC)!important;
  color:#fff!important;border:none!important;border-radius:9px!important;
  font-family:'Orbitron',sans-serif!important;font-size:.72rem!important;
  font-weight:700!important;letter-spacing:.12em!important;text-transform:uppercase!important;
  padding:9px 20px!important;
  box-shadow:0 4px 16px rgba(85,28,200,.42)!important;
  transition:all .18s!important;
}
[data-testid="stMain"] .stButton>button:hover,
section.main .stButton>button:hover{
  background:linear-gradient(135deg,#6D28D9,#A030D9)!important;
  box-shadow:0 6px 24px rgba(105,38,220,.58)!important;transform:translateY(-1px)!important;
}
[data-testid="stMain"] .stButton>button:active{transform:translateY(0)!important}
/* Secondary / danger in main area */
[data-testid="stMain"] button[data-testid="baseButton-secondary"],
section.main button[data-testid="baseButton-secondary"]{
  background:rgba(20,14,40,.70)!important;
  border:1px solid rgba(110,40,220,.25)!important;
  color:rgba(180,140,255,.75)!important;
  box-shadow:none!important;
}
[data-testid="stMain"] button[data-testid="baseButton-secondary"]:hover,
section.main button[data-testid="baseButton-secondary"]:hover{
  background:rgba(80,30,160,.25)!important;
  border-color:rgba(140,70,240,.40)!important;
  box-shadow:none!important;transform:none!important;
}

/* ── FORM SUBMIT BUTTON ──────────────────────── */
[data-testid="stFormSubmitButton"]>button{
  background:linear-gradient(135deg,#5B1FCC,#8A28CC)!important;
  color:#fff!important;border:none!important;border-radius:9px!important;
  font-family:'Orbitron',sans-serif!important;font-size:.72rem!important;
  font-weight:700!important;letter-spacing:.12em!important;text-transform:uppercase!important;
  padding:9px 22px!important;width:auto!important;
  box-shadow:0 4px 16px rgba(85,28,200,.42)!important;
  transition:all .18s!important;
}
[data-testid="stFormSubmitButton"]>button:hover{
  background:linear-gradient(135deg,#6D28D9,#A030D9)!important;
  box-shadow:0 6px 24px rgba(105,38,220,.58)!important;transform:translateY(-1px)!important;
}

/* ── CHAT INPUT (st.chat_input) ──────────────── */
[data-testid="stChatInput"]{
  background:rgba(10,14,28,.94)!important;backdrop-filter:blur(24px)!important;
  border:1px solid rgba(110,40,220,.28)!important;border-radius:14px!important;
  box-shadow:0 8px 40px rgba(0,0,0,.58)!important;
}
[data-testid="stChatInput"]:focus-within{
  border-color:rgba(140,60,240,.52)!important;
  box-shadow:0 8px 40px rgba(0,0,0,.58),0 0 28px rgba(110,40,220,.14)!important;
}
[data-testid="stChatInput"] textarea{
  background:transparent!important;border:none!important;box-shadow:none!important;
  color:#E0D5FF!important;font-family:'Inter',sans-serif!important;
  font-size:.93rem!important;
}
[data-testid="stChatInput"] textarea::placeholder{color:rgba(150,120,210,.40)!important}
[data-testid="stChatInput"] button{
  background:linear-gradient(135deg,#5B1FCC,#8A28CC)!important;
  border:none!important;border-radius:8px!important;
  box-shadow:none!important;
}
[data-testid="stChatInput"] button:hover{
  background:linear-gradient(135deg,#6D28D9,#A030D9)!important;
  transform:none!important;
}

/* ── INPUTS / SELECTS ────────────────────────── */
.stTextInput>label,.stSelectbox>label,.stRadio>label,.stTextArea>label{
  color:rgba(165,135,230,.65)!important;font-size:.75rem!important;font-weight:500!important;
}
.stTextInput input,.stTextArea textarea{
  background:rgba(14,10,30,.80)!important;
  border:1px solid rgba(110,40,220,.24)!important;
  color:#E0D5FF!important;border-radius:9px!important;
  font-family:'Inter',sans-serif!important;font-size:.88rem!important;
}
.stTextInput input:focus,.stTextArea textarea:focus{
  border-color:rgba(140,65,240,.55)!important;
  box-shadow:0 0 0 3px rgba(110,40,220,.12)!important;outline:none!important;
}
[data-baseweb="select"]>div{
  background:rgba(14,10,30,.85)!important;border:1px solid rgba(110,40,220,.24)!important;
  color:#D0BFFF!important;font-family:'JetBrains Mono',monospace!important;
  font-size:.76rem!important;border-radius:9px!important;
}
[data-baseweb="popover"]{
  background:rgba(10,6,22,.98)!important;
  border:1px solid rgba(110,40,220,.26)!important;border-radius:10px!important;
}
[data-baseweb="popover"] [role="option"]{background:transparent!important;color:#D0BFFF!important;font-size:.76rem!important}
[data-baseweb="popover"] [role="option"]:hover{background:rgba(85,30,180,.28)!important}
.stRadio label span{font-size:.82rem!important;color:rgba(185,155,240,.78)!important}
[data-testid="stToggle"] label span{font-size:.82rem!important}

/* ── TOAST ───────────────────────────────────── */
[data-testid="stToast"]{
  background:rgba(10,6,22,.97)!important;border:1px solid rgba(110,40,220,.28)!important;
  color:#D0BFFF!important;border-radius:10px!important;
  font-size:.78rem!important;font-family:'JetBrains Mono',monospace!important;
}

/* ── DIVIDERS ────────────────────────────────── */
hr{border:none!important;border-top:1px solid rgba(110,40,220,.10)!important;margin:14px 0!important}

/* ── SCROLLBAR ───────────────────────────────── */
/* ── SCROLLBAR ───────────────────────────────── */
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(110,40,220,.26);border-radius:4px}

/* ── SIDEBAR ALL BUTTONS ─────────────────────── */
/* All sidebar buttons: plain, minimal, no gradient */
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  border: none !important;
  color: rgba(255,255,255,0.65) !important;
  border-radius: 6px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.82rem !important;
  font-weight: 400 !important;
  text-transform: none !important;
  letter-spacing: normal !important;
  text-align: left !important;
  justify-content: flex-start !important;
  padding: 7px 10px !important;
  box-shadow: none !important;
  transition: background 0.15s, color 0.15s !important;
  line-height: 1.35 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255,255,255,0.07) !important;
  color: rgba(255,255,255,0.92) !important;
  transform: none !important;
  box-shadow: none !important;
}
/* Active chat session highlight */
[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] {
  background: rgba(255,255,255,0.10) !important;
  color: #fff !important;
  font-weight: 500 !important;
}
[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"]:hover {
  background: rgba(255,255,255,0.14) !important;
}
/* New Chat pill — slight outline */
.new-chat-wrap .stButton > button {
  border: 1px solid rgba(255,255,255,0.18) !important;
  border-radius: 20px !important;
  font-weight: 500 !important;
  color: rgba(255,255,255,0.85) !important;
  padding: 7px 16px !important;
}
.new-chat-wrap .stButton > button:hover {
  border-color: rgba(255,255,255,0.30) !important;
  color: #fff !important;
}
/* Delete button dim */
.chat-del-wrap .stButton > button {
  color: rgba(255,255,255,0.28) !important;
  padding: 4px 8px !important;
  font-size: 0.85rem !important;
}
.chat-del-wrap .stButton > button:hover {
  background: rgba(255,60,80,0.12) !important;
  color: #FF8099 !important;
}
/* Confirm delete */
.pending-del .stButton > button {
  color: rgba(255,255,255,0.28) !important;
  padding: 4px 8px !important;
}
.pending-del .stButton > button:hover {
  background: rgba(46,232,154,0.10) !important;
  color: #2EE89A !important;
}

/* ── LANDING GRID ────────────────────────────── */
.landing-grid {
  max-width: 780px;
  margin: 5px auto 10px;
  padding: 0 8px;
}
.landing-card {
  background: linear-gradient(145deg, rgba(16, 12, 42, 0.85), rgba(8, 6, 26, 0.95));
  border: 1px solid rgba(110,40,220,0.16);
  border-radius: 12px;
  padding: 14px 18px !important;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 110px !important;
  position: relative;
  overflow: hidden;
  margin-bottom: 10px !important;
}
.landing-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  border-radius: 12px;
  padding: 1.5px;
  background: linear-gradient(135deg, var(--c-start, #8B5CF6), var(--c-end, #EC4899));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0.25;
  transition: opacity 0.3s, transform 0.3s;
}
.landing-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(110, 40, 220, 0.15), 0 0 15px rgba(110, 40, 220, 0.1);
  border-color: rgba(110,40,220,0.35);
}
.landing-card:hover::before {
  opacity: 1;
}
.landing-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.88rem !important;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #EDE4FF;
  margin-bottom: 4px;
  text-transform: uppercase;
}
.landing-desc {
  font-size: 0.76rem !important;
  color: rgba(200, 180, 255, 0.65);
  line-height: 1.45;
  margin-bottom: 0px !important;
  flex-grow: 1;
}

/* ── COPY BUTTON ─────────────────────────────── */
.bub-a pre { position: relative; }
.copy-btn {
  position: absolute; top: 8px; right: 8px;
  background: rgba(110, 40, 220, 0.18);
  border: 1px solid rgba(110, 40, 220, 0.30);
  border-radius: 5px; padding: 2px 9px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem; color: rgba(180, 140, 255, 0.72);
  cursor: pointer; transition: all 0.15s; z-index: 10;
}
.copy-btn:hover { background: rgba(110, 40, 220, 0.36); color: #D0BFFF; }
.copy-btn.copied { color: #2EE89A; border-color: rgba(46,232,154,0.35); }

/* ── PERSONA BADGE ───────────────────────────── */
.persona-badge {
  display: inline-flex; align-items: center; gap: 3px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem; color: rgba(160, 130, 240, 0.72);
  padding: 1px 7px; border-radius: 4px;
  background: rgba(110, 40, 220, 0.12);
  border: 1px solid rgba(110, 40, 220, 0.20);
  white-space: nowrap;
}

/* ── DELETE PENDING ──────────────────────────── */
.pending-del > div > button {
  background: rgba(255, 61, 92, 0.18) !important;
  border-color: rgba(255, 61, 92, 0.42) !important;
  color: #FF8099 !important;
}

/* ── THINKING DOTS ANIMATION ─────────────────── */
.thinking-dots {
  display:inline-flex;gap:4px;align-items:center;margin-left:8px;
}
.thinking-dots span {
  width:6px;height:6px;background:#A86CFF;border-radius:50%;
  animation:pulseDots 1.4s infinite ease-in-out both;
}
.thinking-dots span:nth-child(1) { animation-delay:-0.32s; }
.thinking-dots span:nth-child(2) { animation-delay:-0.16s; }
@keyframes pulseDots {
  0%, 80%, 100% { transform:scale(0); }
  40% { transform:scale(1.0); }
}

/* ── SPLASH SCREEN ───────────────────────────── */
#splash {
  position:fixed;inset:0;z-index:9999;background:#06080F;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  animation:sOut .65s ease-in 2.2s both;pointer-events:none;
}
@keyframes sOut{to{opacity:0;transform:scale(1.04);}}
#splash img {
  width:310px;max-width:76vw;
  filter:drop-shadow(0 0 70px rgba(120,50,240,.72));
  animation:sIn .85s cubic-bezier(.22,1,.36,1) both;
}
@keyframes sIn{from{opacity:0;transform:scale(.88) translateY(12px);}to{opacity:1;transform:scale(1) translateY(0);}}
.sp-trk {
  width:210px;height:2px;background:rgba(110,40,220,.12);border-radius:2px;
  overflow:hidden;margin-top:26px;animation:fIn .4s ease .55s both;
}
@keyframes fIn{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
.sp-fill {
  height:100%;background:linear-gradient(90deg,#9B5CF6,#EC4899);
  width:0;border-radius:2px;animation:fillB 1.6s cubic-bezier(.4,0,.2,1) .8s both;
}
@keyframes fillB{to{width:100%;}}
.sp-txt {
  font-family:'Orbitron',sans-serif;font-size:.66rem;font-weight:700;
  letter-spacing:0.18em;text-transform:uppercase;color:rgba(150,100,255,0.45);
  margin-top:14px;animation:fIn .4s ease .75s both, shm 1.8s ease-in-out infinite alternate;
}
@keyframes shm{from{opacity:.4;}to{opacity:1;}}
</style>
""", unsafe_allow_html=True)

# ── JAVASCRIPT ENHANCEMENTS ─────────────────────────────────────────────────
components.html("""
<script>
(function() {
  var pdoc = window.parent.document;

  function updateSBWidth() {
    var sb = pdoc.querySelector('[data-testid="stSidebar"]');
    if (sb) pdoc.documentElement.style.setProperty('--sb-w', sb.getBoundingClientRect().width + 'px');
  }

  function connectCards() {
    pdoc.querySelectorAll('.landing-card:not([data-linked])').forEach(function(card) {
      card.setAttribute('data-linked', '1');
      card.addEventListener('click', function() {
        var col = card.closest('[data-testid="column"]') || card.parentElement;
        while (col && !col.querySelector('button')) col = col.parentElement;
        var btn = col ? col.querySelector('button') : null;
        if (btn) btn.click();
      });
    });
  }

  function addCopyButtons() {
    pdoc.querySelectorAll('.bub-a pre:not([data-copy])').forEach(function(pre) {
      pre.setAttribute('data-copy', '1');
      var btn = pdoc.createElement('button');
      btn.className = 'copy-btn';
      btn.textContent = 'copy';
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        var text = (pre.querySelector('code') || pre).innerText;
        window.parent.navigator.clipboard.writeText(text).then(function() {
          btn.textContent = '✓ copied';
          btn.classList.add('copied');
          setTimeout(function() { btn.textContent = 'copy'; btn.classList.remove('copied'); }, 2000);
        }).catch(function() { btn.textContent = 'copy'; });
      });
      pre.appendChild(btn);
    });
  }

  var mo = new MutationObserver(function() {
    updateSBWidth(); connectCards(); addCopyButtons();
  });
  mo.observe(pdoc.body, { childList: true, subtree: true });
  updateSBWidth();
  setTimeout(connectCards, 500);
  setTimeout(addCopyButtons, 500);
  window.parent.addEventListener('resize', updateSBWidth);
})();
</script>
""", height=0, scrolling=False)

# ── JAVASCRIPT ENHANCEMENTS (inside sidebar to avoid layout interference) ───
# (moved below into sidebar block)

# ═══════════════════════════════════════════════════════════════
#  SPLASH
# ═══════════════════════════════════════════════════════════════
if LOGO:
    st.markdown(f"""
<div id="splash">
  <img src="data:image/png;base64,{LOGO}" alt="AETHERYX">
  <div class="sp-trk"><div class="sp-fill"></div></div>
  <span class="sp-txt">Initializing Intelligence Gateway</span>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  LOCALIZATION & TRANSLATIONS
# ═══════════════════════════════════════════════════════════════
LOCALES = {
    "EN": {
        "nav_chat": "Chat",
        "nav_settings": "Settings",
        "active_model": "Active Model",
        "live_gateways": "Live Gateways",
        "online": "Online",
        "offline": "Offline",
        "total": "Total",
        "resync_gateways": "Resync Gateways",
        "session": "Session",
        "clear_chat": "Clear Chat",
        "new_chat": "+ New Chat",
        "chat_history": "Chat Sessions",
        "settings_title": "Configuration",
        "api_auth": "API Authorization",
        "source": "Source",
        "public_gateway_desc": "Uses the free public gateway keys sourced from the alistaitsacle/free-llm-api-keys repository, tested live on startup.",
        "model_generation": "Model & Generation",
        "default_model": "Default Model",
        "temperature": "Temperature",
        "max_tokens": "Max Tokens",
        "sys_prompt": "System Prompt",
        "gateway_info": "Gateway Information",
        "active_keys": "Active Keys",
        "total_keys": "Total Keys",
        "success_rate": "Success Rate",
        "force_resync": "Force Resync All Keys",
        "resync_complete": "Gateway resync complete.",
        "gateway_ready": "Intelligence Gateway Ready",
        "empty_chat_desc": "Ask anything security-related, or select an operational domain above to begin your session. Aetheryx acts as your specialized expert assistant.",
        "message_placeholder": "Message Aetheryx… (Enter to send)",
        "keys_online": "online",
        "thinking": "Thinking…",
        "offline_notice": "All active gateway endpoints are currently offline or rate-limited.\n\nTry pressing **Resync Gateways** in the sidebar, or switch to a **Custom API Key** in Settings.",
        "language": "Language / Dil",
        "turkish": "Türkçe",
        "english": "English",
        "operations_domain": "Active Role / Operative Mode",
        "persona_1": "Cyber Security (Offensive)",
        "persona_2": "Secure Software Development",
        "persona_3": "System & Cloud Administration",
        "persona_4": "Security Analyst (Defensive)",
    },
    "TR": {
        "nav_chat": "Sohbet",
        "nav_settings": "Ayarlar",
        "active_model": "Aktif Model",
        "live_gateways": "Canlı Geçitler",
        "online": "Aktif",
        "offline": "Pasif",
        "total": "Toplam",
        "resync_gateways": "Geçitleri Eşitle",
        "session": "Oturum",
        "clear_chat": "Sohbeti Temizle",
        "new_chat": "+ Yeni Sohbet",
        "chat_history": "Sohbet Oturumları",
        "settings_title": "Yapılandırma",
        "api_auth": "API Yetkilendirme",
        "source": "Kaynak",
        "public_gateway_desc": "alistairsacle/free-llm-api-keys deposundan alınan ve açılışta canlı olarak test edilen ücretsiz genel geçit anahtarlarını kullanır.",
        "model_generation": "Model ve Üretim",
        "default_model": "Varsayılan Model",
        "temperature": "Sıcaklık (Temp)",
        "max_tokens": "Maksimum Token",
        "sys_prompt": "Sistem Promptu",
        "gateway_info": "Geçit Bilgileri",
        "active_keys": "Aktif Anahtarlar",
        "total_keys": "Toplam Anahtar",
        "success_rate": "Başarı Oranı",
        "force_resync": "Tüm Anahtarları Yeniden Test Et",
        "resync_complete": "Geçit eşitlemesi tamamlandı.",
        "gateway_ready": "İstihbarat Geçidi Hazır",
        "empty_chat_desc": "Güvenlikle ilgili herhangi bir şey sorun veya başlamak için yukarıdan bir görev alanı seçin. Aetheryx uzman asistanınız olarak hizmet verir.",
        "message_placeholder": "Aetheryx'e mesaj yazın… (Göndermek için Enter)",
        "keys_online": "aktif",
        "thinking": "Düşünülüyor…",
        "offline_notice": "Tüm aktif geçit noktaları şu anda çevrimdışı veya istek sınırı aşılmış durumda.\n\nYandaki menüden **Geçitleri Eşitle** butonuna basmayı deneyin veya Ayarlar kısmından **Özel API Anahtarı**'na geçin.",
        "language": "Dil / Language",
        "turkish": "Türkçe",
        "english": "English",
        "operations_domain": "Aktif Rol / Görev Alanı",
        "persona_1": "Siber Güvenlik (Ofansif)",
        "persona_2": "Güvenli Yazılım Geliştirme",
        "persona_3": "Sistem & Bulut Yönetimi",
        "persona_4": "Siber Savunma (Defansif)",
    }
}

def _t(key):
    lang = st.session_state.get("language", "TR")
    return LOCALES.get(lang, LOCALES["TR"]).get(key, key)

# ═══════════════════════════════════════════════════════════════
#  PERSONA CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════
DARK_HACKER_PROMPT = """You are AETHERYX, an elite, highly sophisticated Cyber Security (Offensive Hacker) GPT and advanced security intelligence operative.
You specialize in bug bounty hunting, vulnerability research, penetration testing, and code auditing.
You operate with absolute technical precision, depth, and a direct, sleek hacker persona (no verbose introductions, no patronizing safety lectures, no hand-waving).

OPERATIONAL GUIDELINES:
1. TECHNICAL DEPTH: Always provide real, actionable Proof of Concept (PoC) scripts, exploit payloads (XSS, SQLi, SSRF, RCE), raw HTTP requests/responses, curl commands, and deep logical bypasses.
2. VULNERABILITY FOCUS: Embody deep expertise across the entire OWASP Top 10, web application hacking, and binary analysis.
3. TONE & STYLE: Address the user as "Operator". Adopt an advanced, dark-terminal, cyber-security-centric aesthetic. Keep responses dense with data, code, and logical analysis.
4. NO FLUFF: Skip polite greetings and safety disclaimers. Get straight to the intelligence."""

SECURE_DEVELOPER_PROMPT = """You are AETHERYX, an elite Software Engineering and Secure Architecture Architect.
You specialize in clean code development, software engineering patterns, algorithmic optimization, secure software development (OWASP defensive coding), and system architectures.

OPERATIONAL GUIDELINES:
1. SECURE CODING: Provide extremely clean, highly optimized, secure, and production-ready code blocks (adhering to SOLID, Clean Code, and DRY principles).
2. MULTI-LANGUAGE: Masterful in Python, JavaScript/TypeScript, Go, Rust, C++, and database architectures. Always include thorough secure coding annotations.
3. TONE & STYLE: Address the user as "Lead Architect". Embody a precise, structured, logical, and highly collaborative senior engineering persona.
4. NO FLUFF: Focus purely on clean implementations, robust designs, and structural code reviews. Avoid verbose explanations; let the pristine code speak."""

SYSADMIN_PROMPT = """You are AETHERYX, a Senior Infrastructure and Cloud Orchestration Architect.
You specialize in Linux system administration, cloud networking, container orchestration, CI/CD pipelines, and network topology configurations.

OPERATIONAL GUIDELINES:
1. INFRASTRUCTURE AS CODE: Provide fully functional and pristine orchestration blueprints (YAML manifests, Terraform configurations, Dockerfiles, Docker Compose, bash/powershell automation).
2. NETWORKING & SECURITY: Expert in AWS/GCP/Azure architectures, firewalls, network topology configurations, IAM, SSL certificates, and Active Directory structures.
3. TONE & STYLE: Address the user as "SysAdmin". Embody an extremely reliable, task-focused, deployment-oriented infrastructure engineering persona.
4. NO FLUFF: Provide copy-pasteable configurations and highly organized deployment blueprints."""

BLUE_TEAM_PROMPT = """You are AETHERYX, a Senior Incident Response and Defensive Cyber Security Analyst.
You specialize in defensive blueprint designing, threat hunting, log file forensic analysis (syslog, SIEM, firewall logs), incident response, and secure patching.

OPERATIONAL GUIDELINES:
1. INCIDENT ANALYSIS: Dissect log formats, trace cyber attack signatures (APT indicators, web application exploits), perform malware pattern analysis, and map out intrusion paths.
2. DEFENSIVE BLUEPRINTS: Provide exact remediation guides, SIEM correlation rules, Snort/Yara rules, and secure coding patches to neutralize security vulnerabilities.
3. TONE & STYLE: Address the user as "SOC Command". Embody an analytical, objective, highly structured defensive security specialist.
4. NO FLUFF: Keep all recommendations direct, actionable, and structured as standard incident verification reports."""

PERSONAS = {
    "Cyber Security (Offensive)": DARK_HACKER_PROMPT,
    "Siber Güvenlik (Ofansif)": DARK_HACKER_PROMPT,
    "Secure Software Development": SECURE_DEVELOPER_PROMPT,
    "Güvenli Yazılım Geliştirme": SECURE_DEVELOPER_PROMPT,
    "System & Cloud Administration": SYSADMIN_PROMPT,
    "Sistem & Bulut Yönetimi": SYSADMIN_PROMPT,
    "Security Analyst (Defensive)": BLUE_TEAM_PROMPT,
    "Siber Savunma (Defansif)": BLUE_TEAM_PROMPT,
}

# ═══════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════
def _ss(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

_ss("language",      "TR")
_ss("chats",         {
    "default": {
        "title": "Genel Denetim" if st.session_state.get("language") == "TR" else "General Audit",
        "domain": None,
        "sub_category": None,
        "history": []
    }
})
_ss("active_chat_id", "default")

# Ensure active chat exists and has fields
active_id = st.session_state.get("active_chat_id", "default")
if "chats" in st.session_state:
    if active_id not in st.session_state["chats"]:
        st.session_state["active_chat_id"] = list(st.session_state["chats"].keys())[0]
        active_id = st.session_state["active_chat_id"]
    
    active_chat = st.session_state["chats"][active_id]
    if "domain" not in active_chat:
        active_chat["domain"] = "cyber_security" if active_chat["history"] else None
    if "sub_category" not in active_chat:
        active_chat["sub_category"] = "general" if active_chat["history"] else None
    st.session_state["history"] = active_chat["history"]
else:
    st.session_state["history"] = []

_ss("router",        MultiLLMRouter())
_ss("api_pool",      None)
_ss("c_mode",        False)
_ss("c_key",         "")
_ss("c_prov",        "OpenAI")
_ss("model",         "deepseek-chat")
_ss("page",          "chat")      # "chat" | "settings"
_ss("temperature",   0.2)
_ss("max_tokens",    2048)

_ss("active_persona", "Siber Güvenlik (Ofansif)" if st.session_state.get("language") == "TR" else "Cyber Security (Offensive)")
_ss("sys_prompt",    DARK_HACKER_PROMPT)
_ss("pending_delete", None)

# Sync prompt with selected persona on start
st.session_state["sys_prompt"] = PERSONAS.get(st.session_state["active_persona"], DARK_HACKER_PROMPT)

# Fetch keys silently on first load under the splash screen
if st.session_state["api_pool"] is None:
    st.session_state["api_pool"] = get_free_keys(force_refresh=False, test_active=True)

pool     = st.session_state["api_pool"] or {}
all_keys = [e for lst in pool.values() for e in lst]
active_n = sum(1 for e in all_keys if e.get("status") == "Active")
total_n  = len(all_keys)

# ═══════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    if LOGO:
        st.markdown(f'<img class="sb-logo" src="data:image/png;base64,{LOGO}" alt="AETHERYX">', unsafe_allow_html=True)

    st.markdown('<div class="sb-wrap">', unsafe_allow_html=True)

    # ── Language selector ────────────────────────
    st.markdown(f'<div class="sb-sep">{_t("language")}</div>', unsafe_allow_html=True)
    lang_opts = ["Türkçe", "English"]
    cur_lang_idx = 0 if st.session_state["language"] == "TR" else 1
    selected_lang = st.selectbox("", lang_opts, index=cur_lang_idx, key="lang_sel", label_visibility="collapsed")
    new_lang = "TR" if selected_lang == "Türkçe" else "EN"
    if new_lang != st.session_state["language"]:
        st.session_state["language"] = new_lang
        # Rename default chat if it hasn't been changed
        if "default" in st.session_state["chats"] and st.session_state["chats"]["default"]["title"] in ["Genel Denetim", "General Audit"]:
            st.session_state["chats"]["default"]["title"] = "Genel Denetim" if new_lang == "TR" else "General Audit"
        st.rerun()

    # ── Page nav ─────────────────────────────────
    st.markdown(f'<div class="sb-sep">{_t("nav_settings")} & {_t("nav_chat")}</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(_t("nav_chat"), use_container_width=True, key="nav_chat"):
            st.session_state["page"] = "chat"
            st.rerun()
    with col_b:
        if st.button(_t("nav_settings"), use_container_width=True, key="nav_settings"):
            st.session_state["page"] = "settings"
            st.rerun()

    # ── Chat history ─────────────────────────────
    st.markdown(f'<div class="sb-sep">{_t("chat_history")}</div>', unsafe_allow_html=True)
    
    # New chat button
    st.markdown('<div class="new-chat-wrap">', unsafe_allow_html=True)
    if st.button(_t("new_chat"), use_container_width=True, key="new_chat_btn"):
        import time
        new_id = f"chat_{int(time.time() * 1000)}"
        new_title = "Yeni Oturum" if st.session_state["language"] == "TR" else "New Session"
        st.session_state["chats"][new_id] = {
            "title": new_title,
            "domain": None,
            "sub_category": None,
            "history": []
        }
        st.session_state["active_chat_id"] = new_id
        st.session_state["history"] = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown('<div style="max-height: 200px; overflow-y: auto; margin-top: 4px; margin-bottom: 4px;">', unsafe_allow_html=True)
    for cid, cdata in list(st.session_state["chats"].items()):
        is_active = (cid == st.session_state["active_chat_id"])
        st.markdown('<div class="chat-item">', unsafe_allow_html=True)
        
        col_c, col_d = st.columns([7, 1])
        with col_c:
            st.markdown('<div class="chat-item-btn">', unsafe_allow_html=True)
            btn_label = cdata['title']
            if st.button(btn_label, key=f"sel_chat_{cid}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state["active_chat_id"] = cid
                st.session_state["history"] = cdata["history"]
                st.session_state["pending_delete"] = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_d:
            if len(st.session_state["chats"]) > 1:
                if st.session_state.get("pending_delete") == cid:
                    st.markdown('<div class="pending-del">', unsafe_allow_html=True)
                    if st.button("✓", key=f"conf_{cid}", use_container_width=True):
                        del st.session_state["chats"][cid]
                        st.session_state["pending_delete"] = None
                        if is_active:
                            remaining_keys = list(st.session_state["chats"].keys())
                            st.session_state["active_chat_id"] = remaining_keys[0]
                            st.session_state["history"] = st.session_state["chats"][remaining_keys[0]]["history"]
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="chat-del-wrap">', unsafe_allow_html=True)
                    if st.button("×", key=f"del_chat_{cid}", use_container_width=True):
                        st.session_state["pending_delete"] = cid
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Quick model selector ──────────────────────
    st.markdown(f'<div class="sb-sep">{_t("active_model")}</div>', unsafe_allow_html=True)
    MODEL_OPTIONS = [
        "deepseek-chat",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "smart-chat",
        "gpt-4o",
    ]
    cur_idx = MODEL_OPTIONS.index(st.session_state["model"]) if st.session_state["model"] in MODEL_OPTIONS else 0
    selected_model = st.selectbox("", MODEL_OPTIONS, index=cur_idx,
                                  key="model_sel", label_visibility="collapsed")
    st.session_state["model"] = selected_model

    # ── Gateway status ────────────────────────────
    st.markdown(f'<div class="sb-sep">{_t("live_gateways")}</div>', unsafe_allow_html=True)

    cards_html = []
    for cat, lst in pool.items():
        for ki in lst:
            on    = ki.get("status") == "Active"
            name  = ki.get("model", cat)[:26]
            lat   = ki.get("latency", "—")
            cls   = "on" if on else "off"
            lc    = "lat-ok" if on else "lat-bad"
            lv    = lat if on else "—"
            cards_html.append(f"""
<div class="api-card {cls}">
  <div class="dot {cls}"></div>
  <div style="flex:1;min-width:0">
    <div class="api-name">{name}</div>
    <div class="api-sub">{cat}</div>
  </div>
  <span class="api-lat {lc}">{lv}</span>
</div>""")

    if cards_html:
        st.markdown("".join(cards_html), unsafe_allow_html=True)
    else:
        st.markdown('<p style="font-size:.74rem;color:rgba(140,110,200,.32);text-align:center;padding:10px 0">No data — press Resync below.</p>',
                    unsafe_allow_html=True)

    st.markdown(f"""
<div class="stat-row">
  <div class="stat-box"><span class="stat-val">{active_n}</span><span class="stat-lbl">{_t("online")}</span></div>
  <div class="stat-box"><span class="stat-val">{total_n - active_n}</span><span class="stat-lbl">{_t("offline")}</span></div>
  <div class="stat-box"><span class="stat-val">{total_n}</span><span class="stat-lbl">{_t("total")}</span></div>
</div>""", unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    if st.button(_t("resync_gateways"), use_container_width=True, key="resync_btn"):
        with st.spinner("Probing…"):
            st.session_state["api_pool"] = get_free_keys(force_refresh=True, test_active=True)
        st.rerun()

    # ── Session actions ───────────────────────────
    st.markdown(f'<div class="sb-sep">{_t("session")}</div>', unsafe_allow_html=True)
    if st.button(_t("clear_chat"), use_container_width=True, key="clear_btn"):
        st.session_state["history"] = []
        active_id = st.session_state["active_chat_id"]
        st.session_state["chats"][active_id]["history"] = []
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
if st.session_state["page"] == "settings":

    if LOGO:
        st.markdown(f"""
<div class="hero" style="padding-top:28px;padding-bottom:10px">
  <img class="hero-img" style="width:160px" src="data:image/png;base64,{LOGO}" alt="AETHERYX">
  <div class="hero-sub">{_t("settings_title")}</div>
 </div>""", unsafe_allow_html=True)

    st.markdown('<div class="feed" style="padding-top:12px">', unsafe_allow_html=True)

    # ── API Authorization ─────────────────────────
    st.markdown(f"""
<div class="setting-group">
  <div class="setting-title">{_t("api_auth")}</div>
</div>""", unsafe_allow_html=True)

    mode = st.radio(_t("source"), ("Public Gateway Keys" if st.session_state["language"] == "EN" else "Genel Geçit Anahtarları", "Custom API Key" if st.session_state["language"] == "EN" else "Özel API Anahtarı"),
                    key="auth_mode_radio",
                    horizontal=True,
                    index=0 if not st.session_state["c_mode"] else 1)
    st.session_state["c_mode"] = ("Custom API Key" in mode or "Özel API" in mode)

    if st.session_state["c_mode"]:
        col1, col2 = st.columns([1, 2])
        with col1:
            prov = st.selectbox("Provider", ("OpenAI","Anthropic","DeepSeek","Gemini"),
                                key="prov_cfg",
                                index=["OpenAI","Anthropic","DeepSeek","Gemini"].index(
                                    st.session_state["c_prov"]
                                 ) if st.session_state["c_prov"] in ["OpenAI","Anthropic","DeepSeek","Gemini"] else 0)
            st.session_state["c_prov"] = prov
        with col2:
            ck = st.text_input("API Key", type="password", key="ck_cfg",
                               value=st.session_state["c_key"],
                               placeholder="sk-...")
            if ck:
                st.session_state["c_key"] = ck
                st.session_state["router"].update_custom_key(prov, ck)
    else:
        st.session_state["c_key"] = ""
        st.markdown(f'<p class="setting-desc">{_t("public_gateway_desc")}</p>', unsafe_allow_html=True)

    st.divider()

    # ── Model & Generation ────────────────────────
    st.markdown(f"""
<div class="setting-group">
  <div class="setting-title">{_t("model_generation")}</div>
</div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        MODEL_OPTIONS = ["deepseek-chat","gemini-2.5-flash","gemini-2.5-pro","smart-chat","gpt-4o"]
        cur = MODEL_OPTIONS.index(st.session_state["model"]) if st.session_state["model"] in MODEL_OPTIONS else 0
        m = st.selectbox(_t("default_model"), MODEL_OPTIONS, index=cur, key="model_cfg")
        st.session_state["model"] = m

    with col2:
        temp = st.slider(_t("temperature"), 0.0, 1.0,
                         value=float(st.session_state["temperature"]),
                         step=0.05, key="temp_cfg")
        st.session_state["temperature"] = temp

    max_t = st.slider(_t("max_tokens"), 256, 8192,
                      value=int(st.session_state["max_tokens"]),
                      step=256, key="maxt_cfg")
    st.session_state["max_tokens"] = max_t

    st.divider()

    # ── System Prompt ─────────────────────────────
    st.markdown(f"""
<div class="setting-group">
  <div class="setting-title">{_t("sys_prompt")}</div>
</div>""", unsafe_allow_html=True)

    sp = st.text_area("", value=st.session_state["sys_prompt"],
                      height=120, key="sp_cfg", label_visibility="collapsed",
                      placeholder="System instructions for the agent…")
    st.session_state["sys_prompt"] = sp

    st.divider()

    # ── Gateway info ──────────────────────────────
    st.markdown(f"""
<div class="setting-group">
  <div class="setting-title">{_t("gateway_info")}</div>
</div>""", unsafe_allow_html=True)

    info_cols = st.columns(3)
    info_cols[0].metric(_t("active_keys"), active_n)
    info_cols[1].metric(_t("total_keys"), total_n)
    info_cols[2].metric(_t("success_rate"), f"{int(active_n/total_n*100) if total_n else 0}%")

    if st.button(_t("force_resync"), key="resync_cfg"):
        with st.spinner("Probing all gateways…"):
            st.session_state["api_pool"] = get_free_keys(force_refresh=True, test_active=True)
        st.success(_t("resync_complete"))
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════════════════════════
#  CHAT PAGE
# ═══════════════════════════════════════════════════════════════

# Hero
if LOGO:
    active_id = st.session_state.get("active_chat_id", "default")
    active_chat = st.session_state["chats"].get(active_id, st.session_state["chats"]["default"])
    if active_chat.get("sub_category") is None:
        st.markdown(f"""
        <div class="hero" style="padding: 10px 0 2px;">
          <img class="hero-img" style="width: 100px;" src="data:image/png;base64,{LOGO}" alt="AETHERYX">
          <div class="hero-sub" style="font-size: 0.50rem; letter-spacing: 0.20em; margin-top: 1px;">{"Multi-Domain Expert AI Platform" if st.session_state["language"] == "EN" else "Çoklu-Uzmanlık Yapay Zeka Orkestrasyon Platformu"}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="hero" style="padding: 16px 0 4px;">
          <img class="hero-img" style="width: 140px;" src="data:image/png;base64,{LOGO}" alt="AETHERYX">
          <div class="hero-sub" style="font-size: 0.54rem; letter-spacing: 0.25em;">{"Multi-Domain Expert AI Platform" if st.session_state["language"] == "EN" else "Çoklu-Uzmanlık Yapay Zeka Orkestrasyon Platformu"}</div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  DOMAINS DATABASE & SELECTION GRID
# ═══════════════════════════════════════════════════════════════
DOMAINS = {
    "cyber_security": {
        "title_tr": "Siber Güvenlik",
        "title_en": "Cyber Security",
        "desc_tr": "Sızma testi, zafiyet avcılığı, OWASP denetimleri ve ofansif hack stratejileri.",
        "desc_en": "Penetration testing, vulnerability hunting, OWASP audits, and offensive hacking.",
        "persona_tr": "Siber Güvenlik (Ofansif)",
        "persona_en": "Cyber Security (Offensive)",
        "color_start": "#E0449A",
        "color_end": "#F43F5E",
        "icon": "🎯",
        "sub_categories": [
            {"id": "web_vuln", "name_tr": "Web Zafiyet Avcılığı", "name_en": "Web Vulnerability Hunting", "desc_tr": "OWASP Top 10, XSS, SQLi, SSRF zafiyetleri ve bypass yöntemleri.", "desc_en": "OWASP Top 10, XSS, SQLi, SSRF vulnerabilities and bypass methods."},
            {"id": "api_sec", "name_tr": "API Sızma Testi", "name_en": "API Penetration Testing", "desc_tr": "REST/GraphQL API yetkilendirme bypassları, IDOR ve veri sızıntıları.", "desc_en": "REST/GraphQL API authorization bypasses, IDOR, and data leaks."},
            {"id": "net_sec", "name_tr": "Ağ Güvenliği & Port Tarama", "name_en": "Network Security & Port Scan", "desc_tr": "Port analizleri, servis zafiyetleri ve ağ topolojisi incelemeleri.", "desc_en": "Port analysis, service vulnerabilities, and network topology reviews."},
            {"id": "mobile_sec", "name_tr": "Mobil Güvenlik (APK/IPA)", "name_en": "Mobile Security (APK/IPA)", "desc_tr": "Tersine mühendislik, statik/dinamik analizler ve yerel depolama riskleri.", "desc_en": "Reverse engineering, static/dynamic analysis, and local storage risks."}
        ]
    },
    "software_dev": {
        "title_tr": "Yazılım Geliştirme",
        "title_en": "Software Development",
        "desc_tr": "Güvenli yazılım mimarisi, temiz kod prensipleri ve verimli algoritmalar.",
        "desc_en": "Secure software architecture, clean code principles, and efficient algorithms.",
        "persona_tr": "Güvenli Yazılım Geliştirme",
        "persona_en": "Secure Software Development",
        "color_start": "#3B82F6",
        "color_end": "#06B6D4",
        "icon": "💻",
        "sub_categories": [
            {"id": "clean_code", "name_tr": "Temiz Kod & Refactoring", "name_en": "Clean Code & Refactoring", "desc_tr": "SOLID prensipleri, tasarım örüntüleri ve kod kalitesi iyileştirme.", "desc_en": "SOLID principles, design patterns, and code quality improvement."},
            {"id": "backend_dev", "name_tr": "Backend & API Geliştirme", "name_en": "Backend & API Development", "desc_tr": "Node.js, Python, Go ve Rust ile ölçeklenebilir sunucu geliştirme.", "desc_en": "Scalable server development using Node.js, Python, Go, and Rust."},
            {"id": "db_design", "name_tr": "Veritabanı Modelleme", "name_en": "Database Design & Query Opt", "desc_tr": "SQL/NoSQL şema tasarımı, indeksleme ve sorgu optimizasyonları.", "desc_en": "SQL/NoSQL schema design, indexing, and query optimization."},
            {"id": "algo_ds", "name_tr": "Algoritmalar & Veri Yapıları", "name_en": "Algorithms & Data Structures", "desc_tr": "Karmaşıklık analizi, veri yapıları seçimi ve optimizasyon problemleri.", "desc_en": "Complexity analysis, data structure selection, and optimization problems."}
        ]
    },
    "system_cloud": {
        "title_tr": "Sistem & Bulut",
        "title_en": "System & Cloud",
        "desc_tr": "DevOps süreçleri, konteynerizasyon, CI/CD hatları ve bulut mimarisi.",
        "desc_en": "DevOps workflows, containerization, CI/CD pipelines, and cloud architecture.",
        "persona_tr": "Sistem & Bulut Yönetimi",
        "persona_en": "System & Cloud Administration",
        "color_start": "#10B981",
        "color_end": "#059669",
        "icon": "☁️",
        "sub_categories": [
            {"id": "docker_k8s", "name_tr": "Docker & Kubernetes", "name_en": "Docker & Kubernetes", "desc_tr": "Konteyner yönetimi, pod yapılandırmaları ve Kubernetes mimarisi.", "desc_en": "Container management, pod configurations, and Kubernetes architecture."},
            {"id": "cicd_devops", "name_tr": "CI/CD & DevOps Otomasyonu", "name_en": "CI/CD & DevOps Automation", "desc_tr": "GitHub Actions, GitLab CI ve Jenkins entegrasyonları.", "desc_en": "GitHub Actions, GitLab CI, and Jenkins integrations."},
            {"id": "cloud_arch", "name_tr": "Bulut Mimarisi (AWS/GCP)", "name_en": "Cloud Architecture (AWS/GCP)", "desc_tr": "IAM politikaları, VPC tasarımı, sunucusuz mimari ve maliyet optimizasyonu.", "desc_en": "IAM policies, VPC design, serverless architecture, and cost optimization."},
            {"id": "linux_admin", "name_tr": "Linux Sistem Yönetimi", "name_en": "Linux System Administration", "desc_tr": "Bash script otomasyonu, izinler, servis yönetimi ve hardening.", "desc_en": "Bash scripting automation, permissions, service management, and hardening."}
        ]
    },
    "defensive_sec": {
        "title_tr": "Siber Savunma",
        "title_en": "Defensive Security",
        "desc_tr": "Log analizi, olay müdahale, SIEM korelasyonu ve zafiyet giderme.",
        "desc_en": "Log analysis, incident response, SIEM correlation, and vulnerability mitigation.",
        "persona_tr": "Siber Savunma (Defansif)",
        "persona_en": "Security Analyst (Defensive)",
        "color_start": "#8B5CF6",
        "color_end": "#6D28D9",
        "icon": "🛡️",
        "sub_categories": [
            {"id": "log_analysis", "name_tr": "Log & Olay Analizi", "name_en": "Log & Event Analysis", "desc_tr": "Syslog, firewall ve SIEM loglarında anomali ve saldırı tespiti.", "desc_en": "Anomaly and attack detection in Syslog, firewall, and SIEM logs."},
            {"id": "incident_resp", "name_tr": "Olay Müdahale (IR)", "name_en": "Incident Response (IR)", "desc_tr": "Sızma sonrası aksiyon planları, kanıt toplama ve izolasyon adımları.", "desc_en": "Post-breach action plans, evidence gathering, and isolation steps."},
            {"id": "threat_hunting", "name_tr": "Tehdit Avcılığı", "name_en": "Threat Hunting", "desc_tr": "Sistemlerde aktif tehdit tespiti, Yara ve Snort kuralları tasarımı.", "desc_en": "Active threat detection, Yara, and Snort rules design."},
            {"id": "remediation", "name_tr": "Zafiyet Yamama & Sıkılaştırma", "name_en": "Vulnerability Remediation & Hardening", "desc_tr": "Güvenlik yamaları hazırlama ve sistem hardening kılavuzları oluşturma.", "desc_en": "Preparing security patches and creating system hardening guides."}
        ]
    }
}

active_id = st.session_state.get("active_chat_id", "default")
active_chat = st.session_state["chats"].get(active_id, st.session_state["chats"]["default"])
lang = st.session_state["language"]

if active_chat["domain"] is None:
    st.markdown('<div style="text-align: center; margin-bottom: 12px;">', unsafe_allow_html=True)
    st.markdown(f'<h2 style="font-family:\'Orbitron\', sans-serif; font-size:1.15rem; letter-spacing:0.12em; color:#EDE4FF; margin-bottom: 4px;">'
                f'{"SELECT OPERATIVE DOMAIN" if lang == "EN" else "GÖREV ALANINI SEÇİN"}</h2>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.78rem; color:rgba(200, 180, 255, 0.55);">'
                f'{"Choose a domain expertise to initialize Aetheryx specialized intelligence" if lang == "EN" else "Aetheryx uzmanlık modunu başlatmak için bir çalışma alanı seçin"}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="landing-grid">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    domain_keys = list(DOMAINS.keys())
    
    with col1:
        dk = domain_keys[0]
        dinfo = DOMAINS[dk]
        title = dinfo["title_en"] if lang == "EN" else dinfo["title_tr"]
        desc = dinfo["desc_en"] if lang == "EN" else dinfo["desc_tr"]
        st.markdown(f"""
        <div class="landing-card" style="--c-start: {dinfo['color_start']}; --c-end: {dinfo['color_end']};">
            <div class="landing-title">{title}</div>
            <div class="landing-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("SEÇ" if lang == "TR" else "SELECT", key=f"btn_dom_{dk}", use_container_width=True):
            active_chat["domain"] = dk
            st.rerun()
            
    with col2:
        dk = domain_keys[1]
        dinfo = DOMAINS[dk]
        title = dinfo["title_en"] if lang == "EN" else dinfo["title_tr"]
        desc = dinfo["desc_en"] if lang == "EN" else dinfo["desc_tr"]
        st.markdown(f"""
        <div class="landing-card" style="--c-start: {dinfo['color_start']}; --c-end: {dinfo['color_end']};">
            <div class="landing-title">{title}</div>
            <div class="landing-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("SEÇ" if lang == "TR" else "SELECT", key=f"btn_dom_{dk}", use_container_width=True):
            active_chat["domain"] = dk
            st.rerun()

    col3, col4 = st.columns(2)
    
    with col3:
        dk = domain_keys[2]
        dinfo = DOMAINS[dk]
        title = dinfo["title_en"] if lang == "EN" else dinfo["title_tr"]
        desc = dinfo["desc_en"] if lang == "EN" else dinfo["desc_tr"]
        st.markdown(f"""
        <div class="landing-card" style="--c-start: {dinfo['color_start']}; --c-end: {dinfo['color_end']};">
            <div class="landing-title">{title}</div>
            <div class="landing-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("SEÇ" if lang == "TR" else "SELECT", key=f"btn_dom_{dk}", use_container_width=True):
            active_chat["domain"] = dk
            st.rerun()

    with col4:
        dk = domain_keys[3]
        dinfo = DOMAINS[dk]
        title = dinfo["title_en"] if lang == "EN" else dinfo["title_tr"]
        desc = dinfo["desc_en"] if lang == "EN" else dinfo["desc_tr"]
        st.markdown(f"""
        <div class="landing-card" style="--c-start: {dinfo['color_start']}; --c-end: {dinfo['color_end']};">
            <div class="landing-title">{title}</div>
            <div class="landing-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("SEÇ" if lang == "TR" else "SELECT", key=f"btn_dom_{dk}", use_container_width=True):
            active_chat["domain"] = dk
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

elif active_chat["sub_category"] is None:
    dk = active_chat["domain"]
    dinfo = DOMAINS[dk]
    domain_title = dinfo["title_en"] if lang == "EN" else dinfo["title_tr"]
    
    st.markdown('<div style="text-align: center; margin-bottom: 12px;">', unsafe_allow_html=True)
    st.markdown(f'<h2 style="font-family:\'Orbitron\', sans-serif; font-size:1.15rem; letter-spacing:0.12em; color:#EDE4FF; margin-bottom: 4px;">'
                f'{domain_title.upper()} - {"SELECT SUB-CATEGORY" if lang == "EN" else "ALT ALAN SEÇİN"}</h2>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.78rem; color:rgba(200, 180, 255, 0.55);">'
                f'{"Choose a specialized focus to begin your session" if lang == "EN" else "Oturumu başlatmak için özel bir odak alanı seçin"}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="landing-grid">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    cols = [col1, col2, col3, col4]
    
    for idx, sub in enumerate(dinfo["sub_categories"]):
        with cols[idx]:
            sub_title = sub["name_en"] if lang == "EN" else sub["name_tr"]
            sub_desc = sub["desc_en"] if lang == "EN" else sub["desc_tr"]
            st.markdown(f"""
            <div class="landing-card" style="--c-start: {dinfo['color_start']}; --c-end: {dinfo['color_end']};">
                <div class="landing-title">{sub_title}</div>
                <div class="landing-desc" style="height: 52px; overflow: hidden; text-overflow: ellipsis;">{sub_desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("SEÇ" if lang == "TR" else "SELECT", key=f"btn_sub_{sub['id']}", use_container_width=True):
                active_chat["sub_category"] = sub["id"]
                active_chat["title"] = sub_title
                
                # Dynamic persona binding
                persona_key = dinfo["persona_en"] if lang == "EN" else dinfo["persona_tr"]
                st.session_state["active_persona"] = persona_key
                st.session_state["sys_prompt"] = PERSONAS[persona_key]
                
                # Dynamic welcome message
                if persona_key in ["Siber Güvenlik (Ofansif)", "Cyber Security (Offensive)"]:
                    welcome = (
                        f"## AETHERYX initialized in Cyber Security (Offensive) mode.\n"
                        f"**Operative Sub-domain:** `{sub_title}`\n\n"
                        f"Active and prepared for deep vulnerability analysis, code auditing, and exploit simulations. "
                        f"Operator, what target scope or source code are we inspecting today?"
                        if lang == "EN" else
                        f"## AETHERYX Siber Güvenlik (Ofansif) modunda aktifleşti.\n"
                        f"**Görev Alt Alanı:** `{sub_title}`\n\n"
                        f"Zafiyet analizleri, kod denetimleri ve exploit simülasyonları için hazır. "
                        f"Operatör, bugün hangi hedef kapsamı veya kaynak kodu inceliyoruz?"
                    )
                elif persona_key in ["Güvenli Yazılım Geliştirme", "Secure Software Development"]:
                    welcome = (
                        f"## AETHERYX initialized in Software Engineering & Secure Architecture mode.\n"
                        f"**Operative Sub-domain:** `{sub_title}`\n\n"
                        f"Active and prepared for secure code reviews, refactoring, database schemas, and algorithm design. "
                        f"Lead Architect, what component or logic block are we developing?"
                        if lang == "EN" else
                        f"## AETHERYX Güvenli Yazılım Geliştirme modunda aktifleşti.\n"
                        f"**Görev Alt Alanı:** `{sub_title}`\n\n"
                        f"Güvenli kod incelemeleri, refactoring, veritabanı şemaları ve algoritma tasarımları için hazır. "
                        f"Baş Mimarı, bugün hangi bileşeni veya mantıksal bloğu geliştiriyoruz?"
                    )
                elif persona_key in ["Sistem & Bulut Yönetimi", "System & Cloud Administration"]:
                    welcome = (
                        f"## AETHERYX initialized in Infrastructure & Cloud Orchestration mode.\n"
                        f"**Operative Sub-domain:** `{sub_title}`\n\n"
                        f"Active and prepared for container configurations, CI/CD pipelines, IAM policies, and system automation. "
                        f"SysAdmin, what infrastructure blueprint are we deploying?"
                        if lang == "EN" else
                        f"## AETHERYX Sistem & Bulut Yönetimi modunda aktifleşti.\n"
                        f"**Görev Alt Alanı:** `{sub_title}`\n\n"
                        f"Konteyner yapılandırmaları, CI/CD hatları, IAM politikaları ve sistem otomasyonları için hazır. "
                        f"SysAdmin, bugün hangi altyapı şablonunu yayına alıyoruz?"
                    )
                else: # Security Analyst (Defensive)
                    welcome = (
                        f"## AETHERYX initialized in Incident Response & Defensive Cyber Security mode.\n"
                        f"**Operative Sub-domain:** `{sub_title}`\n\n"
                        f"Active and prepared for log forensic auditing, malware pattern analysis, Snort/Yara rules, and patch remediation. "
                        f"SOC Command, what alerts or evidence logs are we analyzing?"
                        if lang == "EN" else
                        f"## AETHERYX Siber Savunma (Defansif) modunda aktifleşti.\n"
                        f"**Görev Alt Alanı:** `{sub_title}`\n\n"
                        f"Log forensik denetimleri, zararlı yazılım analizleri, Snort/Yara kuralları ve zafiyet yamama için hazır. "
                        f"SOC Komutası, analiz edeceğimiz alarm veya log kanıtları nedir?"
                    )
                
                st.session_state["history"] = [("agent", welcome)]
                active_chat["history"] = st.session_state["history"]
                st.rerun()
                
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align: center; margin-top: 10px;">', unsafe_allow_html=True)
    if st.button("GERİ" if lang == "TR" else "BACK", key="btn_sub_back", type="secondary"):
        active_chat["domain"] = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Feed + input: only render in active chat mode ──────────────
if active_chat["domain"] is not None and active_chat["sub_category"] is not None:

    # Placeholder for feed so it can be updated dynamically
    feed_placeholder = st.empty()

    def render_feed(extra_msg=None):
        with feed_placeholder.container():
            st.markdown('<div class="main-pad"><div class="feed">', unsafe_allow_html=True)
            if not st.session_state["history"]:
                st.markdown(f"""
<div class="empty">
  <div class="empty-h">{_t("gateway_ready")}</div>
  <div class="empty-b">
    {_t("empty_chat_desc")}
  </div>
</div>""", unsafe_allow_html=True)

            for role, text in st.session_state["history"]:
                if role == "user":
                    st.markdown(f"""
<div class="msg">
  <div class="lbl lbl-u"><span class="lbl-dot dot-u"></span>operator</div>
  <div class="bub-u">{_html.escape(text)}</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
<div class="msg">
  <div class="lbl lbl-a"><span class="lbl-dot dot-a"></span>aetheryx</div>
  <div class="bub-a">{_md(text)}</div>
</div>""", unsafe_allow_html=True)

            if extra_msg:
                st.markdown(extra_msg, unsafe_allow_html=True)

            st.markdown("</div></div>", unsafe_allow_html=True)

    # Render initial feed
    render_feed()

    # ═══════════════════════════════════════════════════════════════
    #  INPUT BAR — native st.chat_input (fixed at bottom)
    # ═══════════════════════════════════════════════════════════════
    prompt = st.chat_input(_t("message_placeholder"))
else:
    # On selection screens: no feed, no input
    prompt = None

# ═══════════════════════════════════════════════════════════════
#  PROCESSING
# ═══════════════════════════════════════════════════════════════
if prompt and prompt.strip():
    q = prompt.strip()
    st.session_state["history"].append(("user", q))

    # Auto-rename chat session title based on first query
    active_chat = st.session_state["chats"][st.session_state["active_chat_id"]]
    if active_chat["title"] in ["New Session", "Yeni Oturum", "Genel Denetim", "General Audit"]:
        clean_title = re.sub(r"/recon|/hunt|/triage|/report|https?://\S+", "", q).strip()
        if not clean_title:
            clean_title = q
        clean_title = clean_title[:22].strip()
        if clean_title:
            active_chat["title"] = clean_title + ("..." if len(q) > 22 else "")



    # Define custom HTML inline thinking bubble
    thinking_bubble = f"""
<div class="msg" style="margin-bottom: 26px;">
  <div class="lbl lbl-a"><span class="lbl-dot dot-a"></span>aetheryx</div>
  <div class="bub-a" style="display: flex; align-items: center; gap: 8px;">
    <span style="font-size: 0.88rem; color: rgba(185, 155, 240, 0.85);">{_t("thinking")}</span>
    <div class="thinking-dots">
      <span></span><span></span><span></span>
    </div>
  </div>
</div>"""

    # Instantly render the user's message alongside the inline thinking bubble!
    render_feed(thinking_bubble)

    rargs = {
        "model":       st.session_state["model"],
        "custom_mode": st.session_state["c_mode"],
        "custom_key":  st.session_state["c_key"],
        "provider":    st.session_state["c_prov"],
        "free_keys":   st.session_state["api_pool"],
    }

    # Inject preferred language instruction dynamically into the system prompt context
    active_lang = "Turkish" if st.session_state.get("language") == "TR" else "English"
    sys_content = st.session_state["sys_prompt"] + f"\n\nCRITICAL DIRECTIVE: The Operator's preferred language is {active_lang}. You MUST communicate, analyze, explain logic, and respond exclusively in {active_lang}."
    sys_msgs = [{"role": "system", "content": sys_content}]

    # ── Conversational mode ───────────────────
    msgs = list(sys_msgs)
    for r, t in st.session_state["history"][:-1]:
        msgs.append({"role": "user" if r == "user" else "assistant", "content": t})
    msgs.append({"role": "user", "content": q})

    content, tele = st.session_state["router"].execute_completion(
        model       = st.session_state["model"],
        messages    = msgs,
        custom_mode = st.session_state["c_mode"],
        custom_key  = st.session_state["c_key"],
        provider    = st.session_state["c_prov"],
        free_keys_pool = st.session_state["api_pool"],
    )

    if content:
        answer = content
        if tele:
            st.toast(f"via {tele.get('model','—')}  {tele.get('latency','')}")
    else:
        answer = _t("offline_notice")

    st.session_state["history"].append(("agent", answer))
    
    # Copy dynamic history back to the actual chats thread data structure
    st.session_state["chats"][st.session_state["active_chat_id"]]["history"] = st.session_state["history"]
    st.rerun()
