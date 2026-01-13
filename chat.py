import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import gspread
from google.oauth2 import service_account

# --- 1. 頁面設定 ---
st.set_page_config(page_title="秘密樹洞", page_icon="🍃", layout="centered")
st.title("🍃 秘密樹洞 | 匿名留言板")
st.caption("這裡沒有身分，只有真實的心聲。")

# --- 2. 隨機暱稱庫 ---
adjs = ["神祕的", "優雅的", "憤怒的", "閃耀的", "傲嬌的", "憂鬱的", "佛系的", "吃飽的", "剛睡醒的", "迷路的"]
nouns = ["水豚", "珍珠奶茶", "小籠包", "工程師", "貓頭鷹", "柴犬", "大福", "鹹酥雞", "外星人", "薩克斯風"]

if 'anon_name' not in st.session_state:
    st.session_state.anon_name = f"{random.choice(adjs)}{random.choice(nouns)}"

# --- 3. 連線 Google Sheets ---
def get_connection():
    try:
        info = st.secrets["connections"]["gsheets"]["service_account_info"]
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_url(url).sheet1
        return sheet
    except Exception as e:
        st.error(f"連線失敗，請檢查 Secrets 設定。\n錯誤: {e}")
        st.stop()

# --- 4. 抓取 IP (隱私版) ---
def get_ip():
    try:
        from streamlit.web.server.websocket_headers import _get_websocket_headers
        headers = _get_websocket_headers()
        return headers.get("X-Forwarded-For", "Unknown IP")
    except:
        return "Hidden IP"

# 初始化連線
sheet = get_connection()

# 讀取資料
try:
    data = sheet.get_all_records()
    if not data:
        # 如果是空的，手動建立欄位名稱以防報錯
        df = pd.DataFrame(columns=["ID", "時間", "暱稱", "內容", "IP", "檢舉數", "狀態"])
    else:
        df = pd.DataFrame(data)
except:
    df = pd.DataFrame()

# --- 5. 輸入區域 ---
with st.container():
    st.info(f"🎭 你現在的偽裝身分是：**{st.session_state.anon_name}**")
    
    with st.form("msg_form", clear_on_submit=True):
        user_msg = st.text_area("寫下你想說的話...", height=100, max_chars=300)
        submitted = st.form_submit_button("🚀 發布留言
