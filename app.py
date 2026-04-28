import streamlit as st
import json
import random
import os

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="大滷麵猜歌大賽", page_icon="🎵", layout="wide")

# --- 2. 初始化狀態 ---
if 'player_data' not in st.session_state:
    # 預設為 6 位玩家
    st.session_state.player_data = {f"玩家{i+1}": 0 for i in range(6)}
if 'current_index' not in st.session_state:
    st.session_state.current_index = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'has_scored' not in st.session_state:
    st.session_state.has_scored = False

# 讀取題庫
try:
    with open('quiz_bank.json', 'r', encoding='utf-8') as f:
        quiz_data = json.load(f)
except FileNotFoundError:
    st.error("找不到 quiz_bank.json，請確認檔案已上傳至 GitHub。")
    st.stop()

# 下一題邏輯 (改為隨機抽編號)
def next_question():
    st.session_state.current_index = random.randint(0, len(quiz_data) - 1)
    st.session_state.show_answer = False
    st.session_state.has_scored = False

# 第一次啟動時抽一題
if st.session_state.current_index is None:
    next_question()

# --- 3. 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 遊戲設定")
    num_players = st.slider("調整玩家人數", 1, 12, len(st.session_state.player_data))
    
    new_player_data = {}
    for i in range(num_players):
        old_names = list(st.session_state.player_data.keys())
        default_name = old_names[i] if i < len(old_names) else f"玩家{i+1}"
        name = st.text_input(f"P{i+1} 名稱", value=default_name, key=f"name_{i}")
        
        old_scores = list(st.session_state.player_data.values())
        score = old_scores[i] if i < len(old_scores) else 0
        new_player_data[name] = score
    
    if st.button("套用並更新名單"):
        st.session_state.player_data = new_player_data
        st.rerun()
    
    st.divider()
    if st.button("重置所有分數", use_container_width=True):
        for name in st.session_state.player_data:
            st.session_state.player_data[name] = 0
        st.rerun()

# --- 4. 主畫面介面 ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.title("大滷麵專用 猜歌大賽")
    
    # 根據目前的索引讀取音樂檔案 (檔名格式：song_0.mp3)
    audio_filename = f"song_{st.session_state.current_index}.mp3"
    
    # 檢查檔案是否存在
    if os.path.exists(audio_filename):
        st.audio(audio_filename)
    else:
        st.warning(f"等待音樂檔案加載中：{audio_filename}")
        st.info("提示：請確認 50 個音樂檔案已上傳至 GitHub 根目錄。")

st.divider()

# 動態計分板 (3人一列)
player_names = list(st.session_state.player_data.keys())
rows = [player_names[i:i + 3] for i in range(0, len(player_names), 3)]

for row in rows:
    cols = st.columns(len(row))
    for i, name in enumerate(row):
        with cols[i]:
            st.button(f" {name}: {st.session_state.player_data[name]} 分", 
                      use_container_width=True, disabled=True)

st.write("")

# 揭曉答案按鈕 (灰色系)
main_col1, main_col2, main_col3 = st.columns([1, 2, 1])
with main_col2:
    if not st.session_state.show_answer:
        if st.button("揭 曉 答 案", use_container_width=True, type="secondary"):
            st.session_state.show_answer = True
            st.rerun()

# --- 5. 答案顯示與加分區 ---
if st.session_state.show_answer:
    with main_col2:
        current_song = quiz_data[st.session_state.current_index]
        # 清洗標題，移除括號內的雜訊
        clean_name = current_song['song_name'].split('(')[0].split('[')[0].split('-')[0].strip()
        
        st.success(f"### 答案：{clean_name}")
        st.info(f"歌手：{current_song['artist']}")
    
    st.write(" ➕ 加分區 (每題限加一分) ")
    
    if not st.session_state.has_scored:
        for row in rows:
            bonus_cols = st.columns(len(row))
            for i, name in enumerate(row):
                with bonus_cols[i]:
                    if st.button(f"加分給 {name}", use_container_width=True, key=f"add_{name}", type="secondary"):
                        st.session_state.player_data[name] += 1
                        st.session_state.has_scored = True 
                        st.rerun()
    else:
        st.warning("本題已完成加分，請前往下一題。")

    st.write("")
    if st.button("下 一 題 (Next)", use_container_width=True, type="secondary"):
        next_question()
        st.rerun()
