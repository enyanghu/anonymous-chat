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
# 每次重新整理頁面，身分都會變，保持神祕感
adjs = ["神祕的", "優雅的", "憤怒的", "閃耀的", "傲嬌的", "憂鬱的", "佛系的", "吃飽的", "剛睡醒的", "迷路的"]
nouns = ["水豚", "珍珠奶茶", "小籠包", "工程師", "貓頭鷹", "柴犬", "大福", "鹹酥雞", "外星人", "薩克斯風"]

if 'anon_name' not in st.session_state:
    st.session_state.anon_name = f"{random.choice(adjs)}{random.choice(nouns)}"

# --- 3. 連線 Google Sheets (核心功能) ---
def get_connection():
    try:
        # 讀取 Secrets
        info = st.secrets["connections"]["gsheets"]["service_account_info"]
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # 建立連線
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_url(url).sheet1
        return sheet
    except Exception as e:
        st.error(f"連線失敗，請檢查 Secrets 設定。\n錯誤: {e}")
        st.stop()

# --- 4. 抓取 IP (隱私保護版) ---
def get_ip():
    try:
        from streamlit.web.server.websocket_headers import _get_websocket_headers
        headers = _get_websocket_headers()
        # 嘗試抓取真實 IP，若無則回傳 Unknown
        return headers.get("X-Forwarded-For", "Unknown IP")
    except:
        return "Hidden IP"

# 初始化連線
sheet = get_connection()

# 讀取資料並轉為 DataFrame
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
except:
    df = pd.DataFrame() # 如果是空的，就建立空表

# --- 5. 輸入區域 ---
with st.container():
    st.info(f"🎭 你現在的偽裝身分是：**{st.session_state.anon_name}**")
    
    with st.form("msg_form", clear_on_submit=True):
        user_msg = st.text_area("寫下你想說的話...", height=100, max_chars=300)
        submitted = st.form_submit_button("🚀 發布留言", use_container_width=True)
    
    if submitted and user_msg.strip():
        # 取得台灣時間 (UTC+8)
        tw_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        
        # 準備寫入資料
        new_id = len(df) + 1
        new_row = [
            new_id,             # ID
            tw_time,            # 時間
            st.session_state.anon_name, # 暱稱
            user_msg,           # 內容
            get_ip(),           # IP
            0,                  # 檢舉數 (預設0)
            "正常"              # 狀態 (預設正常)
        ]
        
        sheet.append_row(new_row)
        st.success("留言已送出！正在更新牆面...")
        st.rerun()

st.divider()

# --- 6. 留言牆 (瀑布流) ---
st.subheader("📢 最新留言")

if not df.empty and "狀態" in df.columns:
    # 篩選：只顯示狀態正常，且檢舉數小於 5 的留言
    # 注意：這裡要將檢舉數轉為數字以防出錯
    df["檢舉數"] = pd.to_numeric(df["檢舉數"], errors='coerce').fillna(0)
    valid_df = df[(df['狀態'] == '正常') & (df['檢舉數'] < 5)]
    
    # 排序：新的在上面
    # 我們利用 Pandas 的索引來確保檢舉時能找到正確的行數
    sorted_df = valid_df.sort_values(by="時間", ascending=False)
    
    for index, row in sorted_df.iterrows():
        # 顯示卡片
        with st.container():
            st.markdown(f"""
            <div style="padding:15px; border-radius:10px; background-color:#f0f2f6; margin-bottom:10px;">
                <small style="color:grey;">{row['時間']} · {row['暱稱']}</small><br>
                <div style="font-size:16px; margin-top:5px;">{row['內容']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 檢舉按鈕
            # 邏輯：index 是 DataFrame 的原始索引 (0, 1, 2...)
            # Google Sheet 的 Row = 原始索引 + 2 (因為 Row 1 是標題)
            if st.button(f"🚩 檢舉此樓", key=f"report_{row['ID']}"):
                sheet_row_number = index + 2 
                current_reports = int(row['檢舉數']) + 1
                
                # 更新檢舉數 (第 6 欄)
                sheet.update_cell(sheet_row_number, 6, current_reports)
                
                # 如果檢舉超過 5 次，直接隱藏 (更新第 7 欄為 '屏蔽')
                if current_reports >= 5:
                    sheet.update_cell(sheet_row_number, 7, "屏蔽")
                
                st.toast("收到檢舉，系統審核中...", icon="👮‍♂️")
                st.rerun()
else:
    st.info("這裡還是一片荒蕪，快來搶頭香！")
  
