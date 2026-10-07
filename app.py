from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from review_pipeline import analyze_reviews
from sentiment import ModelLoadError


st.set_page_config(page_title="ReviewPulse | Review Intelligence", page_icon=":material/analytics:", layout="wide", initial_sidebar_state="collapsed")

CURSOR_SPARKLES = st.components.v2.component(
        "reviewpulse_cursor_sparkles",
        html='<div id="cursor-sparkle-layer" aria-hidden="true"></div>',
        css="""
        #cursor-sparkle-layer { position:fixed; left:0; top:0; width:0; height:0; overflow:visible; pointer-events:none; z-index:2147483646; }
        .cursor-sparkle { position:fixed; left:var(--spark-x); top:var(--spark-y); color:var(--spark-color); font:700 15px/1 sans-serif; text-shadow:0 0 8px currentColor,0 0 16px currentColor; pointer-events:none; will-change:transform,opacity; animation:sparkle-drift 780ms cubic-bezier(.18,.65,.3,1) forwards; }
        @keyframes sparkle-drift { 0% { opacity:0; transform:translate(-50%,-50%) scale(.25) rotate(-20deg); } 18% { opacity:.96; transform:translate(-50%,-50%) scale(1) rotate(0); } 100% { opacity:0; transform:translate(calc(-50% + var(--spark-dx)),calc(-50% + var(--spark-dy))) scale(0) rotate(105deg); } }
        @media (prefers-reduced-motion: reduce) { .cursor-sparkle { animation-duration:1ms; } }
        """,
        js="""
        export default function (component) {
            const { parentElement } = component;
            const layer = parentElement.querySelector("#cursor-sparkle-layer");
            if (!layer) return;

            let lastSpawn = 0;
            const onPointerMove = (event) => {
                if (event.pointerType === "touch") return;
                const now = performance.now();
                if (now - lastSpawn < 58) return;
                lastSpawn = now;

                const count = Math.random() < 0.22 ? 2 : 1;
                for (let index = 0; index < count; index += 1) {
                    const spark = document.createElement("span");
                    spark.className = "cursor-sparkle";
                    spark.textContent = Math.random() < 0.55 ? "✦" : "✧";
                    spark.style.setProperty("--spark-x", `${event.clientX + (Math.random() - 0.5) * 12}px`);
                    spark.style.setProperty("--spark-y", `${event.clientY + (Math.random() - 0.5) * 12}px`);
                    spark.style.setProperty("--spark-dx", `${(Math.random() - 0.5) * 34}px`);
                    spark.style.setProperty("--spark-dy", `${-8 - Math.random() * 28}px`);
                    spark.style.setProperty("--spark-color", Math.random() < 0.78 ? "#a8f5d5" : "#ffd4a8");
                    layer.appendChild(spark);
                    spark.addEventListener("animationend", () => spark.remove(), { once: true });
                }

                while (layer.childElementCount > 24) layer.firstElementChild.remove();
            };

            document.addEventListener("pointermove", onPointerMove, { passive: true });
            return () => document.removeEventListener("pointermove", onPointerMove);
        }
        """,
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

:root { --ink:#edf6f2; --muted:#9caaa4; --panel:rgba(24,36,33,.9); --line:rgba(170,198,184,.16); --cyan:#65dfbd; --violet:#f2a77a; }
.stApp { position:relative; min-height:100vh; background-color:#0b1312; background-image:radial-gradient(1px 1px at 29px 49px,rgba(205,246,228,.82) 98%,transparent 100%),radial-gradient(1px 1px at 137px 218px,rgba(101,223,189,.78) 98%,transparent 100%),radial-gradient(1.5px 1.5px at 247px 362px,rgba(237,246,242,.72) 98%,transparent 100%),radial-gradient(1.5px 1.5px at 403px 174px,rgba(242,167,122,.64) 98%,transparent 100%),radial-gradient(1px 1px at 81px 291px,rgba(205,246,228,.68) 98%,transparent 100%),radial-gradient(1.2px 1.2px at 308px 93px,rgba(101,223,189,.68) 98%,transparent 100%),radial-gradient(1px 1px at 183px 414px,rgba(237,246,242,.62) 98%,transparent 100%),radial-gradient(1.5px 1.5px at 552px 311px,rgba(242,167,122,.54) 98%,transparent 100%),radial-gradient(1.2px 1.2px at 45px 120px,rgba(205,246,228,.5) 98%,transparent 100%),radial-gradient(1px 1px at 195px 260px,rgba(101,223,189,.54) 98%,transparent 100%),radial-gradient(1.3px 1.3px at 340px 410px,rgba(237,246,242,.46) 98%,transparent 100%),radial-gradient(1px 1px at 95px 374px,rgba(242,167,122,.48) 98%,transparent 100%),radial-gradient(1.6px 1.6px at 515px 100px,rgba(205,246,228,.46) 98%,transparent 100%),radial-gradient(1px 1px at 270px 145px,rgba(101,223,189,.52) 98%,transparent 100%),radial-gradient(1.2px 1.2px at 110px 210px,rgba(205,246,228,.48) 98%,transparent 100%),radial-gradient(1.4px 1.4px at 460px 510px,rgba(101,223,189,.44) 98%,transparent 100%),radial-gradient(1px 1px at 225px 75px,rgba(237,246,242,.52) 98%,transparent 100%),radial-gradient(1.4px 1.4px at 600px 220px,rgba(242,167,122,.42) 98%,transparent 100%),repeating-linear-gradient(90deg,transparent 0 39px,rgba(101,223,189,.035) 39px 40px),repeating-linear-gradient(0deg,transparent 0 39px,rgba(101,223,189,.028) 39px 40px),linear-gradient(118deg,#0b1312 0%,#101b19 55%,#171a16 100%); background-size:280px 460px,420px 620px,560px 760px,820px 980px,340px 520px,500px 680px,660px 840px,760px 920px,240px 380px,380px 540px,600px 780px,460px 650px,730px 880px,520px 720px,300px 480px,640px 820px,460px 580px,880px 1000px,80px 80px,80px 80px,100% 100%; background-position:0 0,90px 0,180px 0,240px 0,40px 0,150px 0,260px 0,320px 0,20px 0,110px 0,220px 0,50px 0,290px 0,370px 0,30px 0,190px 0,70px 0,360px 0,0 0,0 0,0 0; background-repeat:repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,repeat,no-repeat; animation:soft-starfall 55s linear infinite; color:var(--ink); font-family:'Manrope',sans-serif; }
[data-testid="stHeader"] { background:transparent; }
.block-container { position:relative; z-index:1; max-width:1420px; padding:2.4rem 3rem 4rem; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display:none !important; }
h1,h2,h3 { font-family:'Manrope',sans-serif !important; letter-spacing:0 !important; color:#f8fbff !important; }
h2 { font-size:1.18rem !important; margin-top:2rem !important; }
.dock-brand { display:flex; align-items:center; gap:.65rem; color:#f0f7f2; white-space:nowrap; }
.brand-mark { display:flex; align-items:center; justify-content:center; gap:3px; width:38px; height:38px; border:1px solid rgba(101,223,189,.28); border-radius:11px; background:linear-gradient(145deg,#1c3831,#17221e); box-shadow:0 5px 18px rgba(0,0,0,.22); }
.brand-mark i { display:block; width:3px; border-radius:3px; background:#65dfbd; transform-origin:center; animation:waveform 1.5s ease-in-out infinite; }
.brand-mark i:nth-child(1) { height:8px; animation-delay:-.25s; }
.brand-mark i:nth-child(2) { height:15px; animation-delay:-.1s; }
.brand-mark i:nth-child(3) { height:21px; background:#f2a77a; animation-delay:.08s; }
.brand-mark i:nth-child(4) { height:12px; animation-delay:.2s; }
.brand-name { color:#f3f8f5; font:800 1.08rem 'Manrope',sans-serif; line-height:1.05; }
.brand-name span { color:var(--cyan); }
.brand-subline { margin-top:.22rem; color:#8fa49a; font:500 .52rem 'DM Mono',monospace; }
.st-key-reviewpulse_dock { position:sticky; top:.5rem; z-index:999; padding:.3rem; border:1px solid rgba(170,198,184,.2); border-radius:14px; background:rgba(17,29,25,.9); backdrop-filter:blur(16px); box-shadow:0 10px 32px rgba(0,0,0,.28); animation:rise-in .55s ease both; }
.st-key-reviewpulse_dock [data-testid="stSegmentedControl"] { background:transparent; border:0; }
.st-key-reviewpulse_dock button { border-radius:10px !important; transition:transform .18s ease,background-color .18s ease,box-shadow .18s ease; }
.st-key-reviewpulse_dock button:hover { transform:translateY(-2px); box-shadow:0 7px 18px rgba(101,223,189,.13); }
.st-key-reviewpulse_dock [role="radio"] { min-width:0; padding-inline:.5rem !important; font-size:.84rem !important; white-space:nowrap; }
.home-shell { position:relative; min-height:200px; padding:2.1rem 0 1.2rem; border-bottom:1px solid var(--line); animation:rise-in .8s cubic-bezier(.2,.75,.25,1) both; }
.home-shell::after { content:""; position:absolute; right:2%; top:18%; width:36%; height:68%; opacity:.23; background:repeating-linear-gradient(90deg,transparent 0 30px,rgba(101,223,189,.14) 31px 32px),repeating-linear-gradient(0deg,transparent 0 30px,rgba(101,223,189,.1) 31px 32px); mask-image:linear-gradient(90deg,transparent,#000); pointer-events:none; }
.home-kicker { position:relative; z-index:1; color:var(--cyan); font:500 .7rem 'DM Mono',monospace; }
.home-title { position:relative; z-index:1; margin:.9rem 0 .75rem; color:#f3f8f5; font:800 3.25rem/1.04 'Manrope',sans-serif; }
.home-title em { color:var(--cyan); font-style:normal; }
.home-copy { position:relative; z-index:1; max-width:660px; color:#b4c1ba; font-size:1rem; line-height:1.7; }
.home-tool-rail { position:relative; z-index:1; display:flex; flex-wrap:wrap; gap:1.6rem; margin-top:1.8rem; color:#dce8e1; font:500 .7rem 'DM Mono',monospace; }
.home-tool-rail span { color:#f2a77a; margin-right:.45rem; }
.home-details-label { margin-top:1.6rem; color:#8fa49a; font:500 .62rem 'DM Mono',monospace; }
.home-detail-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1.6rem; max-width:990px; margin-top:.65rem; }
.home-detail { border-top:1px solid rgba(170,198,184,.2); padding-top:.7rem; animation:rise-in .55s ease both; }
.home-detail:nth-child(2) { animation-delay:.08s; }
.home-detail:nth-child(3) { animation-delay:.16s; }
.home-detail strong { display:block; color:#eaf4ee; font-size:.82rem; font-weight:700; }
.home-detail p { margin:.25rem 0 0; color:#98aaa0; font-size:.75rem; line-height:1.5; }
.liquid-progress { display:flex; align-items:center; gap:1rem; padding:.85rem 1rem; border:1px solid rgba(101,223,189,.2); border-radius:14px; background:linear-gradient(110deg,rgba(19,39,33,.82),rgba(20,29,26,.72)); }
.liquid-vessel { position:relative; display:grid; place-items:center; flex:none; width:48px; height:66px; overflow:hidden; border:1px solid rgba(177,241,219,.58); border-radius:9px 9px 13px 13px; background:rgba(9,20,17,.72); box-shadow:inset 0 0 12px rgba(101,223,189,.08),0 4px 14px rgba(0,0,0,.18); }
.liquid-vessel::before { content:""; position:absolute; inset:4px; z-index:2; border:1px solid rgba(220,255,240,.08); border-radius:5px 5px 9px 9px; pointer-events:none; }
.liquid-fill { position:absolute; inset:auto 0 0; height:var(--liquid-level); overflow:hidden; background:linear-gradient(180deg,rgba(101,223,189,.7),rgba(43,155,133,.54)); transition:height .55s cubic-bezier(.2,.7,.2,1); }
.liquid-fill::before,.liquid-fill::after { content:""; position:absolute; left:-65%; width:230%; height:15px; border-radius:43%; background:rgba(177,255,224,.52); }
.liquid-fill::before { top:-8px; animation:liquid-wave 3.4s linear infinite; }
.liquid-fill::after { top:-5px; left:-110%; background:rgba(208,255,236,.24); animation:liquid-wave 5s linear infinite reverse; }
.liquid-bubble { position:absolute; z-index:1; bottom:-7px; width:4px; height:4px; border-radius:50%; background:rgba(218,255,239,.72); animation:liquid-bubble 2.8s ease-in infinite; }
.liquid-bubble:nth-child(2) { left:30%; animation-delay:.7s; }
.liquid-bubble:nth-child(3) { left:68%; width:3px; height:3px; animation-delay:1.5s; }
.liquid-percent { position:relative; z-index:3; color:#f2fff8; font:700 .65rem 'DM Mono',monospace; text-shadow:0 1px 5px rgba(0,0,0,.75); }
.liquid-copy { min-width:0; }
.liquid-phase { color:#e5f5ec; font-size:.88rem; font-weight:700; }
.liquid-caption { margin-top:.2rem; color:#96aaa0; font-size:.73rem; line-height:1.45; }
.page-kicker { color:var(--cyan); font:500 .7rem 'DM Mono',monospace; margin:2rem 0 .4rem; }
.empty-tool { margin:2rem 0; padding:2rem 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); animation:rise-in .55s ease both; }
.intake { position:relative; padding:1.25rem 0 1rem; border-bottom:1px solid var(--line); overflow:hidden; animation:rise-in .75s cubic-bezier(.2,.75,.25,1) both; }
.intake::after { content:""; position:absolute; right:1%; top:1.4rem; width:34%; height:72%; opacity:.32; background:repeating-linear-gradient(90deg,transparent 0 27px,rgba(101,223,189,.14) 28px 29px),repeating-linear-gradient(0deg,transparent 0 27px,rgba(101,223,189,.1) 28px 29px); mask-image:linear-gradient(90deg,transparent,#000); pointer-events:none; }
.intake-kicker { position:relative; z-index:1; color:var(--cyan); font:500 .7rem 'DM Mono',monospace; letter-spacing:0; }
.intake-kicker span { display:inline-block; width:7px; height:7px; margin-right:.55rem; border-radius:50%; background:var(--cyan); box-shadow:0 0 12px rgba(101,223,189,.6); animation:signal-pulse 2s ease-in-out infinite; }
.intake h1 { position:relative; z-index:1; margin:.75rem 0 .55rem !important; font-size:2.8rem !important; line-height:1.04; max-width:780px; }
.intake h1 em { color:var(--cyan); font-style:normal; }
.intake-copy { position:relative; z-index:1; color:#b4c1ba; font-size:.96rem; line-height:1.6; max-width:720px; animation:rise-in .75s .12s both; }
.signal-rail { position:relative; z-index:1; display:flex; gap:2.4rem; margin-top:1.1rem; color:#dce8e1; font:500 .7rem 'DM Mono',monospace; }
.signal-rail b { color:#f2a77a; font-weight:500; margin-right:.55rem; }
.stFileUploader { margin-top:.85rem; animation:rise-in .75s .2s both; }
[data-testid="stFileUploaderDropzone"] { min-height:96px; border:1px dashed rgba(101,223,189,.5) !important; border-radius:14px !important; background:linear-gradient(105deg,rgba(25,52,46,.5),rgba(29,36,29,.48)) !important; transition:background .2s ease,border-color .2s ease,transform .2s ease; }
[data-testid="stFileUploaderDropzone"]:hover { border-color:var(--cyan) !important; background:linear-gradient(105deg,rgba(25,65,55,.72),rgba(39,45,32,.65)) !important; transform:translateY(-2px); }
[data-testid="stMetric"], .stPlotlyChart, [data-testid="stExpander"], .evidence { transition:transform .24s ease,border-color .24s ease,box-shadow .24s ease; }
[data-testid="stMetric"]:hover, .stPlotlyChart:hover { transform:translateY(-4px); border-color:rgba(101,223,189,.48); box-shadow:0 16px 34px rgba(0,0,0,.24); }
[data-testid="stExpander"]:hover { border-color:rgba(101,223,189,.38); }
.evidence:hover { transform:translateX(4px); border-left-color:#f2a77a; }
.stTextArea textarea { border-radius:12px !important; border-color:rgba(170,198,184,.22) !important; background:rgba(18,29,25,.82) !important; transition:border-color .2s ease,box-shadow .2s ease; }
.stTextArea textarea:focus { border-color:var(--cyan) !important; box-shadow:0 0 0 1px rgba(101,223,189,.24) !important; }
.intake-foot { color:#81938a; font:400 .68rem 'DM Mono',monospace; margin-top:.8rem; }
.sidebar-mark { color:var(--cyan); font:500 .68rem 'DM Mono',monospace; letter-spacing:0; }
.sidebar-model { border-left:2px solid var(--cyan); padding:.35rem 0 .35rem .75rem; margin:.45rem 0; color:#c0cec6; font:400 .72rem 'DM Mono',monospace; }
.stFormSubmitButton button { border:0 !important; border-radius:10px !important; background:linear-gradient(105deg,#65dfbd,#a2e4bc) !important; color:#10201b !important; font-weight:800 !important; transition:transform .2s ease,box-shadow .2s ease !important; }
.stFormSubmitButton button:hover { transform:translateY(-2px); box-shadow:0 8px 22px rgba(101,223,189,.2); }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color:#65dfbd !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color:#65dfbd !important; }
.hero { position:relative; overflow:hidden; padding:2.2rem 2.2rem 1.8rem; border:1px solid rgba(101,223,189,.24); border-radius:20px; background:linear-gradient(112deg,#19342e,#20271e 72%,#29251d); box-shadow:0 24px 56px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.05); margin-bottom:1.4rem; }
.hero, [data-testid="stMetric"], .stPlotlyChart, [data-testid="stExpander"], [data-testid="stDataFrame"] { animation: fade-up .65s ease both; }
.hero { animation-delay:.05s; }
.source-pill { animation: live-pulse 2.8s ease-in-out infinite; }
[data-testid="stMetric"]:nth-child(1) { animation-delay:.12s; }
[data-testid="stMetric"]:nth-child(2) { animation-delay:.18s; }
[data-testid="stMetric"]:nth-child(3) { animation-delay:.24s; }
[data-testid="stMetric"]:nth-child(4) { animation-delay:.30s; }
[data-testid="stMetric"]:nth-child(5) { animation-delay:.36s; }
[data-testid="stMetric"]:nth-child(6) { animation-delay:.42s; }
.stPlotlyChart { animation-delay:.48s; }
[data-testid="stExpander"] { animation-delay:.58s; }
@keyframes fade-up { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
@keyframes rise-in { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
@keyframes soft-starfall { to { background-position:0 460px,90px 620px,180px 760px,240px 980px,40px 520px,150px 680px,260px 840px,320px 920px,20px 380px,110px 540px,220px 780px,50px 650px,290px 880px,370px 720px,30px 480px,190px 820px,70px 580px,360px 1000px,40px 40px,-40px 40px,0 0; } }
@keyframes waveform { 0%,100% { transform:scaleY(.62); opacity:.72; } 50% { transform:scaleY(1); opacity:1; } }
@keyframes liquid-wave { from { transform:translateX(-12%) rotate(0); } to { transform:translateX(12%) rotate(360deg); } }
@keyframes liquid-bubble { 0% { opacity:0; transform:translateY(0) scale(.6); } 18% { opacity:.75; } 100% { opacity:0; transform:translateY(-60px) scale(1.15); } }
@keyframes signal-pulse { 0%,100% { opacity:1; box-shadow:0 0 0 0 rgba(101,223,189,.38); } 50% { opacity:.68; box-shadow:0 0 0 6px rgba(101,223,189,0); } }
@keyframes live-pulse { 0%,100% { box-shadow:0 0 0 rgba(66,217,255,0); } 50% { box-shadow:0 0 18px rgba(66,217,255,.16); } }
@keyframes scroll-reveal { from { opacity:0; transform:translateY(26px); } to { opacity:1; transform:translateY(0); } }
@supports (animation-timeline:view()) { .stPlotlyChart, [data-testid="stExpander"], [data-testid="stDataFrame"] { animation:scroll-reveal linear both; animation-timeline:view(); animation-range:entry 0% cover 28%; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; scroll-behavior:auto !important; } }
@media (max-width:700px) { .block-container { padding:1.5rem 1.2rem 3rem; } .intake h1 { font-size:2.4rem !important; } .home-title { font-size:2.55rem; } .home-shell { padding-top:1.3rem; } .signal-rail { gap:1rem; flex-wrap:wrap; } .home-tool-rail { gap:.9rem; } .home-detail-grid { grid-template-columns:1fr; gap:.9rem; } .intake::after,.home-shell::after { width:48%; } .st-key-reviewpulse_dock [role="radio"] { padding-inline:.3rem !important; font-size:.76rem !important; } }
.eyebrow { color:var(--cyan); text-transform:uppercase; letter-spacing:.16em; font:500 .7rem 'DM Mono',monospace; margin-bottom:.55rem; }
.hero h1 { position:relative; z-index:1; font-size:2.7rem !important; margin:0 !important; line-height:1.08; max-width:760px; }
.hero p { position:relative; z-index:1; color:#b7c6df; margin:.7rem 0 0; max-width:680px; font-size:1rem; line-height:1.7; }
.source-pill { position:relative; z-index:1; display:inline-block; margin-top:1.1rem; border:1px solid rgba(101,223,189,.3); background:rgba(101,223,189,.1); color:#baf3df; border-radius:999px; padding:.4rem .8rem; font:500 .69rem 'DM Mono',monospace; }
[data-testid="stMetric"] { background:linear-gradient(180deg,rgba(26,39,35,.96),rgba(17,27,24,.98)); border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; min-height:108px; box-shadow:0 10px 28px rgba(0,0,0,.16), inset 0 1px 0 rgba(255,255,255,.03); }
[data-testid="stMetricLabel"] { color:#9fb0ca !important; font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; }
[data-testid="stMetricValue"] { color:#f6f9ff !important; font-size:1.75rem; font-weight:800; }
[data-testid="stExpander"] { background:var(--panel); border:1px solid var(--line); border-radius:16px; margin-bottom:.7rem; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,.12); }
[data-testid="stExpander"] summary { padding:.8rem .7rem; font-weight:700; }
.stPlotlyChart { border:1px solid rgba(170,198,184,.12); background:linear-gradient(180deg,rgba(23,35,31,.92),rgba(15,23,20,.96)); border-radius:14px; padding:.5rem; box-shadow:0 12px 30px rgba(0,0,0,.15); }
.stDataFrame { border:1px solid var(--line); border-radius:14px; overflow:hidden; box-shadow:0 12px 30px rgba(0,0,0,.12); }
.evidence { border-left:3px solid var(--cyan); background:rgba(45,71,118,.18); padding:.85rem 1rem; border-radius:0 10px 10px 0; margin:.7rem 0; color:#d8e3f5; }
.evidence-meta { color:#8ea3c3; font:500 .71rem 'DM Mono',monospace; margin-bottom:.35rem; }
.section-note { color:#95a9c5; margin-top:-.35rem; font-size:.86rem; }
.developer-footer { margin-top:2.5rem; padding:1rem 0 .25rem; border-top:1px solid var(--line); color:#8ea3c3; text-align:center; font:500 .72rem 'DM Mono',monospace; letter-spacing:.04em; }
.stButton > button { border-radius:10px; border:1px solid rgba(66,217,255,.4); background:rgba(66,217,255,.1); color:#cff7ff; }
div[data-baseweb="select"] > div, [data-testid="stFileUploader"] section { background:#17231f !important; border-color:var(--line) !important; }
</style>
""", unsafe_allow_html=True)

CURSOR_SPARKLES(key="reviewpulse_cursor_sparkles")

NAV_ITEMS = ["Home", "Analyze", "Dashboard", "Trust", "Drift"]
NAV_ICONS = {
    "Home": "home",
    "Analyze": "analytics",
    "Dashboard": "dashboard",
    "Trust": "verified_user",
    "Drift": "trending_up",
}


def _open_analyzer():
    st.session_state["reviewpulse_dock"] = "Analyze"


def _open_dashboard():
    st.session_state["reviewpulse_dock"] = "Dashboard"


st.session_state.setdefault("reviewpulse_dock", "Home")
brand, dock = st.columns([1.15, 5], vertical_alignment="center", gap="large")
with brand:
    st.markdown('<div class="dock-brand"><div class="brand-mark"><i></i><i></i><i></i><i></i></div><div><div class="brand-name">Review<span>Pulse</span></div><div class="brand-subline">REVIEW INTELLIGENCE</div></div></div>', unsafe_allow_html=True)
with dock:
    active_page = st.segmented_control(
        "Workspace navigation",
        NAV_ITEMS,
        format_func=lambda item: f":material/{NAV_ICONS[item]}: {item}",
        required=True,
        key="reviewpulse_dock",
        label_visibility="collapsed",
        width="stretch",
        wrap=False,
    )

if active_page == "Home":
    st.markdown("""
    <section class="home-shell">
      <div class="home-kicker">CUSTOMER FEEDBACK / INTELLIGENCE</div>
      <div class="home-title">Reviews,<br><em>decoded.</em></div>
      <p class="home-copy">ReviewPulse turns customer feedback into clear sentiment, sarcasm, and product signals, with every finding tied back to the review.</p>
      <div class="home-tool-rail"><div><span>01</span> SENTIMENT</div><div><span>02</span> SARCASM</div><div><span>03</span> THEMES</div></div>
    </section>
    """, unsafe_allow_html=True)
    st.button("Analyze reviews", type="primary", icon=":material/arrow_forward:", on_click=_open_analyzer)
    st.markdown('<div class="home-details-label">FROM CUSTOMER WORDS TO PRODUCT SIGNALS</div><div class="home-detail-grid"><div class="home-detail"><strong>Read the tone</strong><p>Hugging Face RoBERTa reads review context, not just keywords.</p></div><div class="home-detail"><strong>Keep the evidence</strong><p>Theme signals link findings back to review text.</p></div><div class="home-detail"><strong>Protect the person</strong><p>Contact details are masked before analysis.</p></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="developer-footer">REVIEWPULSE · PRIVATE BY DESIGN · EVIDENCE FIRST</div>', unsafe_allow_html=True)
    st.stop()

if active_page in {"Dashboard", "Trust", "Drift"}:
    if "analysis_result" not in st.session_state:
        st.markdown(f'<div class="page-kicker">{active_page.upper()}</div><section class="empty-tool"><h1>No review analysis yet</h1><p class="home-copy">Submit reviews first, and this workspace will fill with your results.</p></section>', unsafe_allow_html=True)
        st.button("Go to Analyze", type="primary", icon=":material/arrow_forward:", on_click=_open_analyzer)
        st.stop()

    result = st.session_state["analysis_result"]
    summary = result["sentiment_counts"]
    quality = result["quality"]
    validation = result["validation"]
    drift = result["drift"]
    source_name = st.session_state["analysis_source"]

    if active_page == "Dashboard":
        st.markdown(f'<div class="page-kicker">DASHBOARD / {source_name.upper()}</div><h1>Review overview</h1><p class="home-copy">Sentiment and recurring themes across {result["total_reviews"]:,} submitted reviews.</p>', unsafe_allow_html=True)
        metrics = st.columns(4)
        metrics[0].metric("Reviews analyzed", f"{result['total_reviews']:,}")
        metrics[1].metric("Positive", f"{summary['positive']:,}")
        metrics[2].metric("Negative", f"{summary['negative']:,}")
        metrics[3].metric("Sarcastic", sum(review["sarcasm"] == "sarcastic" for review in result["reviews"]))
        chart_theme = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Manrope", color="#d2ddd6"), margin=dict(l=15, r=15, t=20, b=15), height=330)
        left, right = st.columns(2, gap="large")
        with left:
            st.subheader("Sentiment")
            frame = pd.DataFrame({"Sentiment": list(summary), "Reviews": list(summary.values())})
            figure = px.bar(frame, x="Sentiment", y="Reviews", color="Sentiment", text="Reviews", color_discrete_map={"positive":"#65dfbd", "neutral":"#b8b09a", "negative":"#f07c68"})
            figure.update_layout(**chart_theme, showlegend=False)
            figure.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(figure, width="stretch")
        with right:
            st.subheader("Themes")
            themes = pd.DataFrame([{"Theme": item["name"].title(), "Reviews": item["count"]} for item in result["themes"]])
            if not themes.empty:
                figure = px.bar(themes.sort_values("Reviews"), x="Reviews", y="Theme", orientation="h", text="Reviews", color="Reviews", color_continuous_scale=["#345b4e", "#65dfbd"])
                figure.update_layout(**chart_theme, coloraxis_showscale=False)
                figure.update_traces(textposition="outside", marker_line_width=0)
                st.plotly_chart(figure, width="stretch")
        st.subheader("Review evidence")
        sarcastic_reviews = [review for review in result["reviews"] if review.get("sarcasm") == "sarcastic"]
        # Analyses created before sarcasm_examples was added still have review-level labels.
        sarcasm_examples = result.get("sarcasm_examples") or [{
            "review_id": review["review_id"],
            "text": review["text"],
            "signals": review.get("sarcasm_signals", []),
            "sentiment": review["sentiment"],
            "sarcasm_score": review.get("sarcasm_score", 0),
        } for review in sarcastic_reviews[:3]]
        with st.expander(f"Sarcasm · {len(sarcastic_reviews):,} reviews"):
            if not sarcasm_examples:
                st.caption("No sarcastic reviews were identified in this analysis.")
            for example in sarcasm_examples:
                signals = ", ".join(example["signals"]) or "Sarcasm heuristic"
                confidence = f" · CONFIDENCE: {example['sarcasm_score']:.0%}"
                st.markdown(f'<div class="evidence"><div class="evidence-meta">REVIEW {escape(str(example["review_id"]))} · {escape(example["sentiment"].upper())} · SARCASTIC{confidence} · SIGNALS: {escape(signals)}</div>{escape(example["text"])}</div>', unsafe_allow_html=True)
        for theme in result["themes"]:
            with st.expander(f"{theme['name'].title()} · {theme['count']:,} reviews"):
                for example in theme["examples"]:
                    matched = ", ".join(example["signals"]) or "contextual match"
                    st.markdown(f'<div class="evidence"><div class="evidence-meta">REVIEW {escape(str(example["review_id"]))} · {escape(example["sentiment"].upper())} · {escape(example["sarcasm"].upper())} · SIGNALS: {escape(matched)}</div>{escape(example["text"])}</div>', unsafe_allow_html=True)
        st.stop()

    if active_page == "Trust":
        st.markdown('<div class="page-kicker">TRUST / PRIVACY</div><h1>Evidence you can inspect.</h1><p class="home-copy">Personal details are redacted before model inference. Review-level outputs remain traceable to the submitted text.</p>', unsafe_allow_html=True)
        metrics = st.columns(4)
        metrics[0].metric("PII redactions", f"{quality['pii_redacted_count']:,}")
        metrics[1].metric("Labelled validation", f"{validation['accuracy']:.0%}" if validation["accuracy"] is not None else "Needs labels")
        metrics[2].metric("Validation sample", f"{validation['labelled_sample_size']:,}")
        metrics[3].metric("Human review", f"{quality.get('needs_human_review', 0):,}")
        st.subheader("Model provenance")
        st.caption(f"Sentiment is classified locally with Hugging Face ({result['reviews'][0]['model'] if result['reviews'] else 'RoBERTa model'}). Each result retains all three class probabilities; low-confidence, close-call, and rating-conflict results are flagged for human review. PII is redacted before inference and no API key is needed.")
        st.subheader("Protected audit trail")
        audit = pd.DataFrame(result["reviews"])
        if not audit.empty:
            audit["themes"] = audit["themes"].apply(", ".join)
            audit["sentiment_signals"] = audit["sentiment_signals"].apply(", ".join)
            audit["needs_review"] = audit["needs_review"].map({True: "Yes", False: "No"})
            st.dataframe(audit[["review_id", "rating", "sentiment", "sentiment_score", "sentiment_margin", "needs_review", "sarcasm", "sarcasm_score", "sentiment_signals", "themes", "text"]], width="stretch", hide_index=True, height=420)
        st.stop()

    st.markdown('<div class="page-kicker">DRIFT / SENTIMENT OVER TIME</div><h1>Spot the shift.</h1><p class="home-copy">Compare sentiment distribution across dated reviews to identify changes in customer mood.</p>', unsafe_allow_html=True)
    if result["trend"]:
        trend = pd.DataFrame(result["trend"]).melt(id_vars="month", var_name="Sentiment", value_name="Reviews")
        figure = px.line(trend, x="month", y="Reviews", color="Sentiment", markers=True, color_discrete_map={"positive":"#65dfbd", "neutral":"#b8b09a", "negative":"#f07c68"})
        figure.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Manrope", color="#d2ddd6"), margin=dict(l=15, r=15, t=20, b=15), height=380, legend=dict(orientation="h", y=1.15), xaxis_title=None, yaxis_title="Reviews")
        st.plotly_chart(figure, width="stretch")
        divergence = f"{drift['score']:.3f}" if drift["score"] is not None else "N/A"
        st.info(f"{drift['status']} · Jensen–Shannon divergence: **{divergence}**. Baseline: first half of dated reviews; recent: second half.")
        baseline, recent = st.columns(2)
        baseline_leader = max(drift["baseline"], key=drift["baseline"].get)
        recent_leader = max(drift["recent"], key=drift["recent"].get)
        baseline.metric("Baseline leader", f"{baseline_leader.title()} · {drift['baseline'][baseline_leader]:.0%}")
        recent.metric("Recent leader", f"{recent_leader.title()} · {drift['recent'][recent_leader]:.0%}")
    else:
        st.info("Add dates to the reviews to calculate sentiment drift.")
    st.stop()

st.markdown("""
<section class="intake">
  <div class="intake-kicker"><span></span>REVIEWPULSE / ANALYSIS WORKSPACE</div>
  <h1>Every review has<br><em>a signal.</em></h1>
  <p class="intake-copy">Bring customer feedback into focus. See sentiment, sarcasm, and recurring themes grounded in the reviews you provide.</p>
  <div class="signal-rail"><div><b>01</b> SENTIMENT</div><div><b>02</b> SARCASM</div><div><b>03</b> THEMES</div></div>
</section>
""", unsafe_allow_html=True)
paste_tab, upload_tab = st.tabs(["Paste reviews", "Upload CSV / Excel"])
with paste_tab:
    with st.form("paste_reviews_form", border=False):
        manual_text = st.text_area(
            "Review text",
            placeholder="Paste one review here, or separate multiple reviews with a blank line.",
            height=150,
            key="manual_review_text",
        )
        st.caption("Separate multiple reviews with a blank line. Ratings are optional for pasted reviews.")
        manual_submitted = st.form_submit_button("Analyze pasted reviews", type="primary", icon=":material/analytics:")

with upload_tab:
    with st.form("upload_reviews_form", border=False):
        uploaded = st.file_uploader("Choose a review file", type=["csv", "xlsx", "xls"], key="review_file")
        upload_submitted = st.form_submit_button("Analyze uploaded file", type="primary", icon=":material/upload:")

if manual_submitted or upload_submitted:
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("analysis_source", None)
    records = None
    source_name = ""

    if manual_submitted:
        reviews = [item.strip() for item in manual_text.split("\n\n") if item.strip()]
        if reviews:
            records = [{"review_id": f"pasted-{index}", "review_text": text} for index, text in enumerate(reviews, 1)]
            source_name = f"{len(records)} pasted review(s)"
        else:
            st.error("Paste at least one review before analyzing.")

    if upload_submitted:
        if uploaded is None:
            st.error("Choose a CSV or Excel file before analyzing.")
        else:
            try:
                source = None
                last_error = None
                uploaded.seek(0)
                file_signature = uploaded.read(4)
                uploaded.seek(0)
                is_excel = uploaded.name.lower().endswith((".xlsx", ".xls")) or file_signature == b"PK\x03\x04"
                if is_excel:
                    source = pd.read_excel(uploaded)
                else:
                    for encoding in ("utf-8", "cp1252", "latin1"):
                        try:
                            uploaded.seek(0)
                            source = pd.read_csv(uploaded, encoding=encoding)
                            break
                        except UnicodeDecodeError as error:
                            last_error = error
                        except pd.errors.ParserError as error:
                            last_error = error
                            try:
                                uploaded.seek(0)
                                source = pd.read_csv(uploaded, encoding=encoding, engine="python", on_bad_lines="skip")
                                break
                            except (UnicodeDecodeError, pd.errors.ParserError) as fallback_error:
                                last_error = fallback_error
                if source is None:
                    raise last_error

                source.columns = [str(column).replace("\ufeff", "").strip().lower().replace(" ", "_") for column in source.columns]

                def find_column(options):
                    return next((column for column in options if column in source.columns), None)

                text_col = find_column(["review_text", "review", "text", "content", "comment", "review_body", "review_content", "body", "description"])
                if not text_col:
                    st.error(f"No review text column found. Detected columns: {', '.join(source.columns[:15])}")
                else:
                    id_col, rating_col = find_column(["review_id", "_id", "id"]), find_column(["rating", "score", "stars"])
                    date_col, product_col = find_column(["date", "created_at", "at"]), find_column(["product", "app_name", "product_name"])
                    label_col = find_column(["sentiment_label", "label", "sentiment"])
                    records = [{"review_id": row.get(id_col, index + 1), "review_text": row.get(text_col), "rating": row.get(rating_col) if rating_col else None, "date": row.get(date_col) if date_col else None, "product": row.get(product_col) if product_col else None, "sentiment_label": row.get(label_col) if label_col else None} for index, row in source.iterrows()]
                    source_name = uploaded.name
            except Exception as error:
                st.error(f"Could not read the review file: {error}")

    if records is not None:
        liquid_progress = st.empty()
        progress_note = st.empty()

        def update_analysis_progress(phase, completed, total):
            phase_name = "Hugging Face AI review analysis"
            percent = round(completed / max(total, 1) * 100)
            caption = "Loading Hugging Face AI model…" if completed == 0 else f"{completed:,} of {total:,} reviews classified."
            liquid_progress.markdown(
                f'<div class="liquid-progress" role="progressbar" aria-valuenow="{percent}" aria-valuemin="0" aria-valuemax="100"><div class="liquid-vessel"><div class="liquid-fill" style="--liquid-level:{percent}%"><i class="liquid-bubble"></i><i class="liquid-bubble"></i><i class="liquid-bubble"></i></div><span class="liquid-percent">{percent}%</span></div><div class="liquid-copy"><div class="liquid-phase">{phase_name}</div><div class="liquid-caption">{caption}</div></div></div>',
                unsafe_allow_html=True,
            )
            if completed == 0:
                progress_note.caption(f"Starting {phase_name}…")
            elif completed < total:
                progress_note.caption(f"{phase_name}: {completed:,}/{total:,} reviews analyzed")

        try:
            with st.status("Starting AI review analysis…", expanded=True) as analysis_status:
                st.session_state["analysis_result"] = analyze_reviews(
                    records,
                    progress_callback=update_analysis_progress,
                )
                st.session_state["analysis_source"] = source_name
                analysis_status.update(label="Review analysis complete", state="complete", expanded=False)
            liquid_progress.empty()
            progress_note.empty()
        except Exception as error:
            liquid_progress.empty()
            progress_note.empty()
            st.error("AI analysis could not run. The uploaded reviews were not changed.")
            with st.expander("Technical details"):
                st.code(str(error))

if "analysis_result" not in st.session_state:
    st.markdown('<div class="intake-foot">WAITING FOR YOUR INPUT · NO REVIEWS HAVE BEEN ANALYZED</div>', unsafe_allow_html=True)
    st.markdown('<div class="developer-footer">Developed by Naman · Avni · Abhay · Priyanshu · Alish · Aditya</div>', unsafe_allow_html=True)
    st.stop()

result = st.session_state["analysis_result"]
source_name = st.session_state["analysis_source"]
if active_page == "Analyze":
    st.markdown(f'<div class="page-kicker">ANALYSIS COMPLETE</div><h1>{result["total_reviews"]:,} reviews processed.</h1><p class="home-copy">Sentiment and sarcasm predictions are ready. Open the dashboard to explore themes and review evidence.</p>', unsafe_allow_html=True)
    st.button("Open dashboard", type="primary", icon=":material/dashboard:", on_click=_open_dashboard)
    st.stop()
