import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd

st.set_page_config(page_title="診斷模式")
st.title("🚑 樹洞緊急診斷")

# 1. 檢查 Secrets
st.write("---")
st.write("### 步驟 1：檢查鑰匙")
if "connections" in st.secrets:
    st.success("✅ Secrets 格式正確 (讀取到 connections)")
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    st.write(f"目標表格網址: `{url}`")
else:
    st.error("❌ Secrets 讀取失敗！請檢查是否貼在正確位置")
    st.stop()

# 2. 測試連線
st.write("### 步驟 2：測試 Google 連線")
try:
    info = st.secrets["connections"]["gsheets"]["service_account_info"]
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)
    st.success("✅ Google 帳號認證成功！")
except Exception as e:
    st.error(f"❌ 認證失敗：{e}")
    st.stop()

# 3. 測試開啟表格
st.write("### 步驟 3：開啟試算表")
try:
    sheet = client.open_by_url(url).sheet1
    st.success(f"✅ 成功找到表格！分頁名稱：{sheet.title}")
except Exception as e:
    st.error(f"❌ 找不到表格！請確認：\n1. 機器人信箱是否有編輯權限？\n2. 網址是否正確？\n錯誤訊息：{e}")
    st.stop()

# 4. 測試讀取標題
st.write("### 步驟 4：讀取資料")
try:
    data = sheet.get_all_records()
    if not data:
        st.warning("⚠️ 表格內容是空的！(這就是為什麼你沒看到東西)")
        st.info("👇 請去 Google Sheet 確認第一列 (Row 1) 是否有填入這些標題：")
        st.code("ID, 時間, 暱稱, 內容, IP, 檢舉數, 狀態")
    else:
        st.success(f"✅ 讀取成功！目前有 {len(data)} 筆資料")
        st.dataframe(data)
except Exception as e:
    st.error(f"❌ 讀取失敗：{e}")
