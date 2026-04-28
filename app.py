import streamlit as st
import json
import random
import yt_dlp
from pydub import AudioSegment
import os

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="大滷麵猜歌大賽", page_icon="🎵", layout="wide")


# --- 2. 下載與剪輯函數 ---
def prepare_audio(song_name, artist):
    query = f"{song_name} {artist}"
    ydl_opts = {
    'format': 'bestaudio/best',
    'default_search': 'ytsearch1:',
    'outtmpl': 'temp_audio.%(ext)s',
    'cookiefile': 'cookies.txt',
    'nocheckcertificate': True,  # 跳過 SSL 檢查
    'ignoreerrors': True,
    'no_warnings': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }],
    'quiet': True,
}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([query])

    if os.path.exists("temp_audio.mp3"):
        audio = AudioSegment.from_mp3("temp_audio.mp3")
        quiz_clip = audio[30000:50000]
        quiz_clip.export("quiz_clip.mp3", format="mp3")
        os.remove("temp_audio.mp3")


# --- 3. 初始化狀態 ---
if 'player_data' not in st.session_state:
    st.session_state.player_data = {f"玩家{i + 1}": 0 for i in range(6)}
if 'current_song' not in st.session_state:
    st.session_state.current_song = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'has_scored' not in st.session_state:
    st.session_state.has_scored = False

try:
    with open('quiz_bank.json', 'r', encoding='utf-8') as f:
        quiz_data = json.load(f)
except FileNotFoundError:
    st.error("找不到 quiz_bank.json")
    st.stop()


def next_question():
    st.session_state.current_song = random.choice(quiz_data)
    st.session_state.show_answer = False
    st.session_state.has_scored = False
    with st.spinner(f"正在抓取音樂..."):
        prepare_audio(st.session_state.current_song['song_name'],
                      st.session_state.current_song['artist'])


if st.session_state.current_song is None:
    next_question()

# --- 4. 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 遊戲設定")
    num_players = st.slider("調整玩家人數", 1, 12, len(st.session_state.player_data))
    new_player_data = {}
    for i in range(num_players):
        old_names = list(st.session_state.player_data.keys())
        default_name = old_names[i] if i < len(old_names) else f"玩家{i + 1}"
        name = st.text_input(f"P{i + 1} 名稱", value=default_name, key=f"name_{i}")
        old_scores = list(st.session_state.player_data.values())
        score = old_scores[i] if i < len(old_scores) else 0
        new_player_data[name] = score
    if st.button("套用並更新名單"):
        st.session_state.player_data = new_player_data
        st.rerun()

    st.divider()
    if st.button("重置所有分數", use_container_width=True):
        # 針對目前的 player_data 將分數歸零
        for name in st.session_state.player_data:
            st.session_state.player_data[name] = 0
        st.rerun()

# --- 5. 主畫面介面 ---
# 這裡使用了三欄佈局，將標題與播放器都放在 c2，實現垂直切齊
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.title("大滷麵專用 猜歌大賽")
    if os.path.exists("quiz_clip.mp3"):
        st.audio("quiz_clip.mp3")

st.divider()

# 動態計分板
player_names = list(st.session_state.player_data.keys())
rows = [player_names[i:i + 3] for i in range(0, len(player_names), 3)]

for row in rows:
    cols = st.columns(len(row))
    for i, name in enumerate(row):
        with cols[i]:
            st.button(f" {name}: {st.session_state.player_data[name]} 分",
                      use_container_width=True, disabled=True)

st.write("")

# 揭曉答案按鈕
main_col1, main_col2, main_col3 = st.columns([1, 2, 1])
with main_col2:
    if not st.session_state.show_answer:
        if st.button("揭 曉 答 案", use_container_width=True, type="secondary"):
            st.session_state.show_answer = True
            st.rerun()

# --- 答案顯示與加分區 ---
if st.session_state.show_answer:
    with main_col2:
        # 使用 .split('(')[0] 自動刪除括號後的文字
        clean_name = st.session_state.current_song['song_name'].split('(')[0].split('[')[0].strip()
        st.success(f"### 答案：{clean_name}")
        st.info(f"歌手：{st.session_state.current_song['artist']}")

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
    # 將下一題按鈕也改為灰色系 (secondary)
    if st.button("下 一 題 (Next)", use_container_width=True, type="secondary"):
        next_question()
        st.rerun()
