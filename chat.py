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

# --- 3. 連線設定 (優化版) ---
def get_connection():
    try:
        # 👇 我把這邊拆短了，避免手機複製時斷行
        conn = st.secrets["connections"]["gsheets"]
        info = conn["service_account_info"]
        url = conn["spreadsheet"]
        
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        return client.open_by_url(url).sheet1
    except Exception as e:
        st.error(f"連線失敗: {e}")
        st.stop()

def get_ip():
    try:
        from streamlit.web.server.websocket_headers import _get_websocket_headers
        return _get_websocket_headers().get("X-Forwarded-For", "Unknown IP")
    except:
        return "Hidden IP"

sheet = get_connection()
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data if data else [], columns=["ID", "時間", "暱稱", "內容", "IP", "檢舉數", "狀態"])
except:
    df = pd.DataFrame()

# ==========================================
# PART 1: 定義彈出視窗
# ==========================================
@st.dialog("🌱 種下一顆種子")
def entry_dialog():
    st.write(f"你的身分：**{st.session_state.anon_name}**")
    
    with st.form("popup_form", clear_on_submit=True):
        user_msg = st.text_area("寫下你想說的話...", height=150, max_chars=300)
        submitted = st.form_submit_button("🚀 發送雲朵", use_container_width=True)
    
    if submitted and user_msg.strip():
        try:
            tw_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            new_id = len(df) + 1
            new_row = [new_id, tw_time, st.session_state.anon_name, user_msg, get_ip(), 0, "正常"]
            sheet.append_row(new_row)
            st.toast("雲朵飄上去了！", icon="☁️")
            st.rerun()
        except Exception as e:
            st.error(f"發送失敗：{e}")

# ==========================================
# PART 2: 天空區 (顯示留言)
# ==========================================
st.subheader("☁️ 心情天空")

if not df.empty and "狀態" in df.columns:
    try:
        df["檢舉數"] = pd.to_numeric(df["檢舉數"], errors='coerce').fillna(0)
        valid_df = df[(df['狀態'] == '正常') & (df['檢舉數'] < 5)]
        sorted_df = valid_df.sort_values(by="時間", ascending=False)
        
        if sorted_df.empty:
            st.info("天空中還沒有雲朵...")
        else:
            col1, col2 = st.columns(2)
