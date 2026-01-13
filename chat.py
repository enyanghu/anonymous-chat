import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import gspread
from google.oauth2 import service_account

# --- 1. 頁面設定 ---
st.set_page_config(page_title="秘密樹洞", page_icon="🍃", layout="centered")

# CSS: 雲朵動畫 + 強制懸浮按鈕
st.markdown("""
<style>
    /* 雲朵卡片樣式 */
    .cloud-card {
        background-color: #f0f2f6;
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        border: 2px solid white;
        position: relative;
        animation: float 6s ease-in-out infinite;
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
        100% { transform: translateY(0px); }
    }
    .cloud-card:nth-child(even) { animation-duration: 7s; }
    .cloud-meta { font-size: 0.8em; color: #888; margin-bottom: 5px; }
    .cloud-content { font-size: 1em; line-height: 1.5; color: #31333F; white-space: pre-wrap; }
    
    /* 底部留白 */
    .block-container { padding-bottom: 100px; }

    /* ========== 懸浮按鈕 (右下角藍點點) ========== */
    button[kind="primary"] {
        position: fixed !important;
        bottom: 30px !important;
        right: 30px !important;
        width: 60px !important;
        height: 60px !important;
        border-radius: 50% !important;
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
        z-index: 999999 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        font-size: 24px !important;
    }
    button[kind="primary"]:hover {
        transform: scale(1.1) !important;
        background-color: #FF2B2B !important;
    }
    button[kind="primary"] > div {
        margin: 0 !important;
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🍃 秘密樹洞")
st.caption("抬頭看看天空的心情，或者點擊右下角種下自己的一朵雲。")

# --- 2. 隨機暱稱 ---
adjs = ["神祕的", "優雅的", "憤怒的", "閃耀的", "傲嬌的", "憂鬱的", "佛系的", "吃飽的", "剛睡醒的", "迷路的"]
nouns = ["水豚", "珍珠奶茶", "小籠包", "工程師", "貓頭鷹", "柴犬", "大福", "鹹酥雞", "外星人", "薩克斯風"]

if 'anon_name' not in st.session_state:
    st.session_state.anon_name = f"{random.choice(adjs)}{random.choice(nouns)}"

# --- 3. 連線設定 ---
def get_connection():
    try:
        info = st.secrets["connections"]["gsheets
