"""Visual identity and presentation components for the data studio."""
from html import escape
from pathlib import Path
import streamlit as st

ASSET_DIRECTORY = Path(__file__).parent / "assets"


def inject_styles():
    st.markdown('''<style>
:root { --ink:#182938; --muted:#697681; --paper:#f7f7f2; --accent:#df673d; --line:#dedfd8; }
.stApp { background:var(--paper); color:var(--ink); }
[data-testid="stHeader"] { background:transparent; height:2.7rem; }
[data-testid="stToolbar"] { opacity:.35; }
[data-testid="stToolbar"]:hover { opacity:1; }
[data-testid="stMainBlockContainer"] { max-width:1440px; padding:3rem 3.3rem 2rem; }
h1,h2,h3,p,label { color:var(--ink); }
.stApp h1 { font-weight:500; letter-spacing:-.04em; }
.stApp h2 { font-weight:500; letter-spacing:-.025em; }
[data-testid="stSidebar"] { background:#182938; border-right:0; }
[data-testid="stSidebarContent"] { padding-top:.6rem; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding:1.2rem 1.25rem; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] summary,
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] span { color:#e8ecee; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:#a5b2ba; font-size:12px; }
[data-testid="stSidebar"] [data-baseweb="select"]>div,
[data-testid="stSidebar"] [data-baseweb="input"] { background:#253b4b; border-color:#3c505e; color:#f1f3f4; }
[data-testid="stSidebar"] input { color:#f1f3f4; }
[data-testid="stSidebar"] [data-testid="stExpander"] { border-color:#3c505e; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary { padding:12px 10px; }
[data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary { color:#f1c2a5; }
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stCaptionContainer"] p { line-height:1.55; }
.account-panel { margin:0 0 18px; padding:13px 14px; background:#213949; border:1px solid #3e5663; border-radius:7px; }
.account-panel strong { display:block; color:#f0b083; font-size:12px; margin-bottom:5px; }
.account-panel span { display:block; color:#c1ced2; font-size:11px; line-height:1.5; }
.account-panel.signed-in { border-left:3px solid #d86d42; }
.sidebar-spacer { min-height:28px; }
[data-testid="stSidebar"] button[kind="secondary"] { background:transparent; border-color:#50616d; color:#edf1f3; }
[data-testid="stSidebar"] button[kind="secondary"]:hover { background:#2b4354; border-color:#c0c9ce; }
[data-testid="stSidebar"] .stButton { margin-bottom:5px; }
[data-testid="stSidebar"] .stButton button { min-height:38px; text-align:left; padding-left:13px; }
[data-testid="stSidebar"] .stButton button p { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] { background:#253b4b; }
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small { color:#bcc6cb; }
[data-testid="stSidebar"] svg { color:#bac6ce; }
.brand { padding:8px 0 28px; }
.brand img { display:block; width:100%; max-width:205px; height:auto; }
.side-label { color:#99adb9; font-size:10px; letter-spacing:1.7px; font-weight:600; margin:25px 0 12px; }
.side-note { border-top:1px solid #3a4d5b; margin-top:36px; padding-top:20px; font-size:12px; color:#a9bac5; line-height:1.7; }
.side-note strong { color:#e3e9ec; font-weight:500; }
.topline { display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--line); padding-bottom:20px; margin-bottom:38px; gap:15px; }
.breadcrumb { font-size:12px; color:var(--muted); letter-spacing:.02em; }.breadcrumb b { font-weight:500; color:var(--ink); }.breadcrumb span { padding:0 12px; color:#adb4b6; }
.status { color:#586d5d; font-size:11px; display:flex; align-items:center; gap:7px; white-space:nowrap; }.status i { width:6px; height:6px; background:#638268; border-radius:50%; }
.eyebrow { font-size:10px; font-weight:600; letter-spacing:2px; color:#a05c3d; text-transform:uppercase; margin-bottom:19px; }
.hero { display:grid; grid-template-columns:1.2fr 1fr; gap:30px; align-items:center; margin:2px 0 28px; }
.hero h1 { font-family:Georgia,'Times New Roman',serif; font-size:clamp(44px,4.7vw,69px); line-height:1.04; font-weight:400; letter-spacing:-3px; margin:0 0 24px; padding:0; }
.hero h1 em { font-weight:400; color:#bc603d; }
.hero p { font-size:15px; line-height:1.75; color:#697681; max-width:420px; margin:0; }
.signal-art { min-height:265px; border-left:1px solid var(--line); padding:5px 0 5px 30px; }
.signal-art svg { width:100%; max-height:265px; }
.section-kicker { margin:7px 0 8px; color:var(--muted); font-size:10px; letter-spacing:1.5px; text-transform:uppercase; }
.section-title { font-size:20px; font-weight:500; letter-spacing:-.5px; margin-bottom:5px; }
.section-note { font-size:12px; color:var(--muted); margin-bottom:14px; }
[data-testid="stFileUploaderDropzone"] { background:#fff; border:1px dashed #bbc4bb; border-radius:10px; padding:22px; }
[data-testid="stFileUploader"] label { font-size:13px; font-weight:500; }
.stButton button,.stDownloadButton button { border-radius:7px; font-size:13px; min-height:41px; font-weight:500; transition:background .15s,border-color .15s; }
.stButton button[kind="primary"] { background:#df673d; border-color:#df673d; color:white; }
.stButton button[kind="primary"] p { color:white; }
.stButton button[kind="primary"]:hover { background:#bc532e; border-color:#bc532e; }
.stButton button[kind="secondary"],.stDownloadButton button { background:#fff; border:1px solid #d3d8d3; }
.stButton button[kind="secondary"]:hover,.stDownloadButton button:hover { border-color:#b46543; color:#934929; }
.workflow { display:grid; grid-template-columns:repeat(3,1fr); gap:26px; border-top:1px solid var(--line); margin-top:35px; padding-top:24px; }
.workflow .step-no { font-family:Georgia,serif; color:#b57655; font-size:18px; margin-bottom:12px; }
.workflow h3 { font-size:15px; font-weight:600; letter-spacing:-.3px; padding:0; margin:0 0 7px; }
.workflow p { font-size:12px; color:#697681; line-height:1.6; margin:0; }
.studio-footer { color:#88938f; font-size:10px; letter-spacing:.05em; margin-top:40px; padding-top:15px; border-top:1px solid var(--line); display:flex; justify-content:space-between; }
.dataset-heading { display:flex; align-items:flex-end; justify-content:space-between; gap:20px; margin-bottom:23px; }
.dataset-heading h1 { font-family:Georgia,serif; font-size:38px; margin:0; padding:0; line-height:1.2; overflow-wrap:anywhere; }
.dataset-heading .eyebrow { margin-bottom:9px; }.dataset-heading p { margin:8px 0 0; color:var(--muted); font-size:13px; }
.dataset-badge { border:1px solid #cfd7ca; background:#eef2e9; color:#526750; border-radius:5px; padding:7px 10px; font-size:11px; white-space:nowrap; }
[data-testid="stMetric"] { background:#fff; border:1px solid #e0e3da; border-radius:9px; padding:18px 20px; }
[data-testid="stMetricLabel"] p { font-size:11px; color:#6c7b7e; text-transform:uppercase; letter-spacing:1px; }
[data-testid="stMetricValue"] { font-family:Georgia,serif; font-size:34px; color:#203746; }
[data-baseweb="tab-list"] { gap:22px; background:transparent; border-bottom:1px solid #d9dfd5; margin-top:15px; }
button[data-baseweb="tab"] { padding:16px 0; font-size:12px; }
button[data-baseweb="tab"] p { color:#6d7d80; font-size:12px; }
button[data-baseweb="tab"][aria-selected="true"] p { color:#b35430; font-weight:600; }
[data-baseweb="tab-highlight"] { background:#d86b3f; height:2px; }
[data-baseweb="tab-panel"] { padding-top:25px; }
[data-testid="stDataFrame"] { border:1px solid #e0e3da; border-radius:8px; overflow:hidden; }
[data-testid="stExpander"] { background:transparent; border:1px solid #dce1d8; border-radius:8px; }
.insight-banner { background:#213949; color:#f2f4ef; border-radius:10px; display:flex; align-items:center; justify-content:space-between; padding:24px 27px; gap:24px; margin-bottom:22px; }
.insight-banner h3 { color:#f2f4ef; font-family:Georgia,serif; font-size:25px; font-weight:400; letter-spacing:-.4px; margin:0 0 8px; padding:0; }
.insight-banner p { color:#bbcad1; font-size:12px; margin:0; line-height:1.7; }
.insight-banner .eyebrow { color:#e3ab7b; margin-bottom:9px; }
.quality-ring { display:flex; align-items:center; gap:15px; flex-shrink:0; }.quality-ring svg { width:74px; height:74px; }.quality-ring b { font-size:21px; color:#f3f5ee; font-weight:500; }.quality-ring small { display:block; color:#aabfc8; font-size:10px; letter-spacing:.5px; margin-top:3px; }
[data-testid="stChatMessage"] { background:#fff; border:1px solid #e0e3da; border-radius:10px; }
[data-testid="stPills"] label, [data-testid="stPills"] p { color:var(--ink) !important; }
[data-testid="stPills"] button, [data-testid="stPills"] [role="option"] { background:#fff !important; color:#203746 !important; border:1px solid #cfd8cf !important; }
[data-testid="stPills"] button:hover, [data-testid="stPills"] [role="option"]:hover { background:#eef2e9 !important; border-color:#b46543 !important; }
[data-testid="stPills"] button[aria-checked="true"], [data-testid="stPills"] [role="option"][aria-selected="true"] { background:#294b53 !important; color:#fff !important; border-color:#294b53 !important; }
[role="radiogroup"][aria-label="Questions based on this data"] button[data-variant="pills"] { background:#fff !important; color:#203746 !important; border:1px solid #cfd8cf !important; }
[role="radiogroup"][aria-label="Questions based on this data"] button[data-variant="pills"] p { color:#203746 !important; }
[role="radiogroup"][aria-label="Questions based on this data"] button[data-variant="pills"]:hover { background:#eef2e9 !important; border-color:#b46543 !important; }
[role="radiogroup"][aria-label="Questions based on this data"] button[data-variant="pills"][aria-checked="true"] { background:#294b53 !important; color:#fff !important; border-color:#294b53 !important; }
[role="radiogroup"][aria-label="Questions based on this data"] button[data-variant="pills"][aria-checked="true"] p { color:#fff !important; }
[data-testid="stChatInput"] { background:#253b4b; border:1px solid #50616d; border-radius:8px; }
[data-testid="stChatInput"] textarea { color:#f1f3f4 !important; caret-color:#f1f3f4; }
[data-testid="stChatInput"] textarea::placeholder { color:#b9c5ca !important; opacity:1; }
[data-testid="stChatInput"] button { color:#f1f3f4; }
.model-map { display:flex; flex-direction:column; gap:16px; padding:20px; background:#eef2e9; border:1px solid #dce1d8; border-radius:8px; }
.model-link { display:flex; align-items:center; gap:10px; width:100%; overflow:auto; }
.model-node { min-width:210px; max-width:280px; padding:12px 15px 10px; background:#fff; border:1px solid #b9c9bd; border-top:4px solid #294b53; border-radius:6px; box-shadow:0 2px 6px rgba(24,41,56,.06); }
.model-node strong { display:block; color:#203746; font-size:13px; margin-bottom:8px; overflow-wrap:anywhere; }
.model-node small { display:block; color:#697681; line-height:1.5; overflow-wrap:anywhere; }
.model-node .model-key { color:#b35430; font-weight:600; }
.model-unlinked { border-top-color:#aab8ad; }
.model-field { border-top:1px solid #edf0ea; padding-top:3px; margin-top:3px; }
.model-arrow { min-width:180px; text-align:center; color:#b35430; }
.model-arrow b { display:block; font-size:24px; line-height:1; }
.model-arrow small { color:#697681; font-size:10px; line-height:1.4; }
[data-testid="stSidebar"] .stButton button[kind="secondary"] { background:#253b4b; border-color:#4a606f; }
[data-testid="stSidebar"] .stButton button[kind="secondary"] p { color:#e6edef; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] { background:#253b4b; border:1px solid #4a606f; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] input { background:transparent; color:#e6edef; }
[data-testid="stSidebar"] [data-testid="stTextInput"] input { background:#253b4b; color:#e6edef; }
@media(max-width:850px) { [data-testid="stMainBlockContainer"] { padding:3rem 1.4rem 2rem; }.hero { grid-template-columns:1fr; }.signal-art { display:none; }.hero h1 { font-size:49px; }.workflow { gap:16px; }.dataset-heading { align-items:flex-start; }.dataset-heading h1 { font-size:29px; }.insight-banner { align-items:flex-start; }.quality-ring { flex-direction:column; gap:5px; }.quality-ring svg { width:55px; height:55px; } }
@media(max-width:520px) { .workflow { grid-template-columns:1fr; }.topline { margin-bottom:25px; }.status { display:none; }.dataset-badge { display:none; }.insight-banner { flex-direction:column; }.quality-ring { flex-direction:row; }.hero h1 { font-size:42px; } }
</style>''', unsafe_allow_html=True)


def brand():
    st.markdown('<div class="brand">', unsafe_allow_html=True)
    st.image(str(ASSET_DIRECTORY / "analytoka-logo.svg"), width=205)
    st.markdown('</div>', unsafe_allow_html=True)


def topline(loaded):
    st.markdown(f'<div class="topline"><div class="breadcrumb">Workspace<span>/</span><b>{"Your data" if loaded else "Overview"}</b></div><div class="status"><i></i>Your work is saved locally</div></div>', unsafe_allow_html=True)


def welcome():
    st.markdown('''<div class="hero"><div><div class="eyebrow">A little curiosity. A lot of clarity.</div><h1>Your data.<br><em>A clearer story.</em></h1><p>Turn spreadsheets into understanding.<br>Explore patterns, ask better questions, and find<br>the insights that move your business forward.</p></div><div class="signal-art"><svg viewBox="0 0 330 270" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Illustration of raw data becoming a clear trend"><text x="12" y="24" font-family="monospace" font-size="9" letter-spacing="2" fill="#7b8886">FROM SIGNAL TO STORY</text><path d="M12 72H320M12 115H320M12 158H320M12 201H320" stroke="#dde1d8" stroke-dasharray="3 5"/><rect x="21" y="163" width="24" height="38" rx="2" fill="#dde3d9"/><rect x="61" y="133" width="24" height="68" rx="2" fill="#c8d4c8"/><rect x="101" y="144" width="24" height="57" rx="2" fill="#c8d4c8"/><rect x="141" y="109" width="24" height="92" rx="2" fill="#a7bfae"/><rect x="181" y="119" width="24" height="82" rx="2" fill="#a7bfae"/><rect x="221" y="86" width="24" height="115" rx="2" fill="#73988a"/><rect x="261" y="57" width="24" height="144" rx="2" fill="#294b53"/><path d="M33 148L73 118L113 130L153 94L193 104L233 70L273 42" stroke="#d86d42" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="273" cy="42" r="5" fill="#f7f7f2" stroke="#d86d42" stroke-width="2"/><text x="12" y="238" font-family="monospace" font-size="9" fill="#8b9892">EXPLORE</text><path d="M85 235H227" stroke="#c9d2c8"/><path d="m223 232 4 3-4 3" stroke="#c9d2c8"/><text x="245" y="238" font-family="monospace" font-size="9" fill="#8b9892">UNDERSTAND</text></svg></div></div>''', unsafe_allow_html=True)


def workflow():
    st.markdown('''<div class="workflow"><div><div class="step-no">01 /</div><h3>Bring your data</h3><p>Start with a CSV or Excel workbook.<br>Every worksheet has a place.</p></div><div><div class="step-no">02 /</div><h3>Follow your curiosity</h3><p>Ask in plain language. Explore trends,<br>clean up details, connect the dots.</p></div><div><div class="step-no">03 /</div><h3>Make it meaningful</h3><p>Build a visual story and export<br>findings worth sharing.</p></div></div>''', unsafe_allow_html=True)


def dataset_heading(name, count):
    label = name.rsplit(' [', 1)[0]
    st.markdown(f'<div class="dataset-heading"><div><div class="eyebrow">Your workspace</div><h1>{escape(label)}</h1><p>A closer look at the data behind your next decision.</p></div><div class="dataset-badge">{count} {"source" if count == 1 else "sources"} available</div></div>', unsafe_allow_html=True)


def overview_banner(df):
    missing = int(df.isna().sum().sum())
    total = df.size
    percent = (total-missing)/total*100 if total else 0
    circumference = 188.5
    title = 'A good story starts with a clear picture.'
    text = f'{len(df):,} records, {len(df.columns)} fields, and a workspace ready for your questions.'
    st.markdown(f'''<div class="insight-banner"><div><div class="eyebrow">At a glance</div><h3>{title}</h3><p>{text}</p></div><div class="quality-ring"><svg viewBox="0 0 74 74" aria-hidden="true"><circle cx="37" cy="37" r="30" stroke="#3e5663" stroke-width="5" fill="none"/><circle cx="37" cy="37" r="30" stroke="#dbaa79" stroke-width="5" stroke-linecap="round" fill="none" stroke-dasharray="{circumference*percent/100} {circumference}" transform="rotate(-90 37 37)"/></svg><div><b>{percent:.1f}%</b><small>NON-MISSING CELLS</small></div></div></div>''', unsafe_allow_html=True)


def footer():
    st.markdown('<div class="studio-footer"><span>ANALYTOKA AI / THE DATA STUDIO</span><span>Designed by John Muthoka</span></div>', unsafe_allow_html=True)
