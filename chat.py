import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd

st.title("🔧 樹洞維修診斷")

# 1. 測試連線
try:
    info = st.secrets["connections"]["gsheets"]["service_account_info"]
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)
    
    # 嘗試開啟表格
    sheet = client.open_by_url(url).sheet1
    st.success(f"✅ 連線成功！找到表格：{sheet.title}")
    
    # 2. 測試讀取
    data = sheet.get_all_records()
    if not data:
        st.warning("⚠️ 表格目前是空的 (或是程式讀不到標題列)。")
        st.info("請確認你的 Google Sheet **第一列 A1:G1** 有填入標題：ID, 時間, 暱稱, 內容, IP, 檢舉數, 狀態")
    else:
        st.success(f"✅ 讀取成功！目前有 {len(data)} 筆資料")
        st.write(pd.DataFrame(data))

    # 3. 測試寫入
    if st.button("測試寫入一筆資料"):
        try:
            # 寫入測試資料
            sheet.append_row([999, "測試時間", "維修員", "這是一筆測試", "1.1.1.1", 0, "測試"])
            st.success("🎉 寫入成功！請去 Google Sheet 看看有沒有出現一行資料？")
        except Exception as e:
            st.error(f"❌ 寫入失敗：{e}")

except Exception as e:
    st.error(f"❌ 系統錯誤：{e}")
    st.write("請截圖這個錯誤給我看")
