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
        # 抓取第一個工作表 (不管它叫 Sheet1 還是 工作表1)
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
    # 如果只有標題沒有內容，data 會是空的，這時我們要手動建立 DataFrame
    if not data:
        df = pd.DataFrame(columns=["ID", "時間", "暱稱", "內容", "IP", "檢舉數", "狀態"])
    else:
        df = pd.DataFrame(data)
except Exception as e:
    df = pd.DataFrame()

# --- 5. 輸入區域 ---
with st.container():
    st.info(f"🎭 你現在的偽裝身分是：**{st.session_state.anon_name}**")
    
    with st.form("msg_form", clear_on_submit=True):
        user_msg = st.text_area("寫下你想說的話...", height=100, max_chars=300)
        # 👇 這裡就是之前報錯的地方，我已經修好了！
        submitted = st.form_submit_button("🚀 發布留言", use_container_width=True)
    
    if submitted and user_msg.strip():
        try:
            # 取得台灣時間 (UTC+8)
            tw_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            
            # 計算新 ID (如果 df 是空的，len 就是 0，ID 從 1 開始)
            new_id = len(df) + 1
            
            new_row = [
                new_id,
                tw_time,
                st.session_state.anon_name,
                user_msg,
                get_ip(),
                0,      # 檢舉數
                "正常"   # 狀態
            ]
            
            sheet.append_row(new_row)
            st.success("留言已送出！正在更新牆面...")
            st.rerun()
        except Exception as e:
            st.error(f"發送失敗：{e}")

st.divider()

# --- 6. 留言牆 (雲朵瀑布流版) ---
st.subheader("☁️ 心情天空")

# 自訂 CSS：讓卡片變成圓角雲朵狀，並加上輕微浮動動畫
st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        gap: 1rem;
    }
    .cloud-card {
        background-color: #f0f2f6;
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        transition: transform 0.2s;
        border: 2px solid white;
    }
    .cloud-card:hover {
        transform: translateY(-3px);
        box-shadow: 4px 4px 10px rgba(0,0,0,0.1);
    }
    .cloud-meta {
        font-size: 0.8em;
        color: #888;
        margin-bottom: 5px;
    }
    .cloud-content {
        font-size: 1em;
        line-height: 1.5;
        color: #31333F;
        white-space: pre-wrap; /* 保留換行 */
    }
</style>
""", unsafe_allow_html=True)

if not df.empty and "狀態" in df.columns:
    try:
        # 1. 資料處理
        df["檢舉數"] = pd.to_numeric(df["檢舉數"], errors='coerce').fillna(0)
        valid_df = df[(df['狀態'] == '正常') & (df['檢舉數'] < 5)]
        sorted_df = valid_df.sort_values(by="時間", ascending=False)
        
        if sorted_df.empty:
            st.info("天空中還沒有雲朵，快來發送第一朵吧！")
        else:
            # 2. 建立雙欄位 (這就是瀑布流的關鍵！)
            col1, col2 = st.columns(2)
            cols = [col1, col2] # 把兩個欄位放進清單方便輪流使用
            
            # 3. 迴圈顯示
            for i, (index, row) in enumerate(sorted_df.iterrows()):
                # i % 2 會決定是 0 (左欄) 還是 1 (右欄)
                with cols[i % 2]:
                    # 使用 HTML 畫出雲朵氣泡
                    st.markdown(f"""
                    <div class="cloud-card">
                        <div class="cloud-meta">
                            {row['暱稱']}<br>
                            <span style="font-size:0.8em">{row['時間'][5:-3]}</span>
                        </div>
                        <div class="cloud-content">{row['內容']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 檢舉按鈕 (保持 Streamlit 原生按鈕功能)
                    # 為了美觀，我們把按鈕設為小一點，並靠右
                    if st.button(f"🚩", key=f"report_{row['ID']}", help="檢舉這則留言"):
                        # 邏輯：ID 對應 Row+1
                        target_row = int(row['ID']) + 1
                        current_reports = int(row['檢舉數']) + 1
                        sheet.update_cell(target_row, 6, current_reports)
                        
                        if current_reports >= 5:
                            sheet.update_cell(target_row, 7, "屏蔽")
                        
                        st.toast("已收到檢舉，雲朵即將消散...", icon="🌫️")
                        st.rerun()

    except Exception as e:
        st.error(f"讀取錯誤：{e}")
else:
    st.info("這裡還是一片荒蕪，快來搶頭香！")
