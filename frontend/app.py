import streamlit as st
import requests
from dotenv import load_dotenv
import os
import uuid
import pandas as pd

# .env ファイルの読み込み
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("社内AIアシスタント")

st.sidebar.header("メニュー")
menu = [
    "AIチャット",
    "ユーザー一覧",
    "ユーザー追加",
    "タスク一覧",
    "タスク追加・更新",
    "タスク削除",
]
choice = st.sidebar.selectbox("選択してください", menu)

# ----------------------------------------
# ユーザー関連のAPI呼び出し
# ----------------------------------------
def get_users():
    try:
        response = requests.get(f"{API_BASE_URL}/users")
        response.raise_for_status()
        return response.json().get("users", [])
    except requests.exceptions.RequestException as e:
        st.error(f"ユーザー取得エラー: {e}")
        return []

def post_user(name: str):
    try:
        response = requests.post(f"{API_BASE_URL}/users", json={"name": name})
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"ユーザー追加エラー: {e}")
        return False

# ----------------------------------------
# タスク関連のAPI呼び出し
# ----------------------------------------
def get_tasks():
    try:
        response = requests.get(f"{API_BASE_URL}/tasks")
        response.raise_for_status()
        # もしバックエンドが `[task, task, ...]` のリスト形式返す場合はそのまま返す
        # あるいは { "tasks": [ ... ] } のような構造なら取り出す処理が必要
        return response.json()  
    except requests.exceptions.RequestException as e:
        st.error(f"タスク取得エラー: {e}")
        return []

def post_task(title: str):
    try:
        response = requests.post(f"{API_BASE_URL}/tasks", json={"title": title})
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"タスク追加エラー: {e}")
        return False

def patch_task(task_id: int, title: str, is_done: bool):
    try:
        response = requests.patch(
            f"{API_BASE_URL}/tasks/{task_id}",
            json={"title": title, "is_done": is_done}
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"タスク更新エラー: {e}")
        return False

def delete_task(task_id: int):
    try:
        response = requests.delete(f"{API_BASE_URL}/tasks/{task_id}")
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"タスク削除エラー: {e}")
        return False

# ----------------------------------------
# チャット関連のAPI呼び出し
# ----------------------------------------
def post_chat(session_id: str, message: str):
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"session_id": session_id, "message": message},
        )
        response.raise_for_status()
        return response.json().get("answer", "")
    except requests.exceptions.RequestException as e:
        st.error(f"チャットエラー: {e}")
        return None

# ----------------------------------------
# 画面構成
# ----------------------------------------
if choice == "AIチャット":
    st.subheader("社内ドキュメント連携チャット")

    # セッションIDをセッション状態で管理（会話ごとに固定）
    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = str(uuid.uuid4())
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # 会話履歴を表示
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # チャット入力
    if prompt := st.chat_input("メッセージを入力してください"):
        # ユーザーメッセージを表示・保存
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # バックエンドに送信してAI応答を取得
        with st.chat_message("assistant"):
            with st.spinner("回答を生成中..."):
                answer = post_chat(st.session_state.chat_session_id, prompt)
            if answer:
                st.write(answer)
                st.session_state.chat_messages.append({"role": "assistant", "content": answer})

    if st.button("会話をリセット"):
        st.session_state.chat_session_id = str(uuid.uuid4())
        st.session_state.chat_messages = []
        st.rerun()

elif choice == "ユーザー一覧":
    st.subheader("ユーザー一覧")
    users = get_users()
    if users:
        df = pd.DataFrame(users)
        st.dataframe(df)
    else:
        st.info("ユーザーが存在しません。")

elif choice == "ユーザー追加":
    st.subheader("新規ユーザーの追加")
    with st.form(key='add_user_form'):
        name = st.text_input("ユーザー名")
        submit_button = st.form_submit_button(label='追加')
    
    if submit_button:
        if name:
            success = post_user(name)
            if success:
                st.success("ユーザーを追加しました。")
        else:
            st.warning("ユーザー名を入力してください。")

elif choice == "タスク一覧":
    st.subheader("タスク一覧")
    tasks = get_tasks()
    if tasks:
        df = pd.DataFrame(tasks)
        st.dataframe(df)
    else:
        st.info("タスクが存在しません。")

elif choice == "タスク追加・更新":
    st.subheader("タスク追加 or 更新")

    # タスク追加フォーム
    with st.form(key='add_task_form'):
        new_title = st.text_input("新規タスク名")
        submit_new_task = st.form_submit_button(label='タスク追加')
    if submit_new_task and new_title:
        success = post_task(new_title)
        if success:
            st.success("タスクを追加しました。")

    st.write("---")

    # タスク更新フォーム
    tasks = get_tasks()
    if tasks:
        st.write("タスク更新")
        task_ids = [t['id'] for t in tasks]
        selected_id = st.selectbox("更新するタスクIDを選択", task_ids)
        # 該当のタスクを取得
        selected_task = next((t for t in tasks if t['id'] == selected_id), None)
        if selected_task:
            default_title = selected_task.get('title', "")
            default_is_done = selected_task.get('is_done', False)

            with st.form(key='update_task_form'):
                title_input = st.text_input("タイトル", default_title)
                done_input = st.checkbox("完了フラグ", value=default_is_done)
                submit_update = st.form_submit_button(label='更新')

            if submit_update:
                success = patch_task(selected_id, title_input, done_input)
                if success:
                    st.success("タスクを更新しました。")
    else:
        st.info("タスク一覧を取得できないため更新操作ができません。")

elif choice == "タスク削除":
    st.subheader("タスク削除")
    tasks = get_tasks()
    if tasks:
        task_ids = [t['id'] for t in tasks]
        selected_id = st.selectbox("削除するタスクIDを選択", task_ids)
        if st.button("削除実行"):
            success = delete_task(selected_id)
            if success:
                st.success("タスクを削除しました。")
    else:
        st.info("タスクが存在しません。")