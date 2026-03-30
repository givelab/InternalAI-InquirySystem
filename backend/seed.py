"""
seed.py - 初期データ投入スクリプト（冪等性あり）
使い方: docker-compose exec backend python seed.py
"""
import os
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base, User, Task, ChatHistory

DB_URL = (
    f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', '5432')}/{os.environ['DB_NAME']}"
)

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

SEED_USERS = [
    {"email": "alice@example.com", "name": "Alice"},
    {"email": "bob@example.com", "name": "Bob"},
    {"email": "charlie@example.com", "name": "Charlie"},
]

SEED_TASKS = [
    {"title": "プロジェクト計画を立てる", "is_done": False},
    {"title": "デザインレビュー", "is_done": True},
    {"title": "バックエンド実装", "is_done": False},
    {"title": "テストコードを書く", "is_done": False},
    {"title": "デプロイ作業", "is_done": False},
]

SEED_CHATS = [
    {
        "session_id": "session-demo-001",
        "user_message": "こんにちは！このシステムについて教えてください。",
        "ai_response": "こんにちは！このシステムはAIを活用した社内問い合わせシステムです。",
    },
    {
        "session_id": "session-demo-001",
        "user_message": "どんな機能がありますか？",
        "ai_response": "ユーザー管理、タスク管理、チャット機能などがあります。",
    },
    {
        "session_id": "session-demo-002",
        "user_message": "タスクを追加するには？",
        "ai_response": "POST /tasks エンドポイントにリクエストを送ることでタスクを追加できます。",
    },
]


def seed():
    with Session() as db:
        # Users
        existing_emails = {u.email for u in db.query(User).all()}
        users_added = 0
        for data in SEED_USERS:
            if data["email"] not in existing_emails:
                db.add(User(email=data["email"], name=data["name"]))
                users_added += 1
        db.flush()

        # Tasks
        existing_titles = {t.title for t in db.query(Task).all()}
        tasks_added = 0
        for data in SEED_TASKS:
            if data["title"] not in existing_titles:
                db.add(Task(title=data["title"], is_done=data["is_done"]))
                tasks_added += 1

        # ChatHistories
        existing_sessions = {
            (c.session_id, c.user_message)
            for c in db.query(ChatHistory).all()
        }
        chats_added = 0
        for data in SEED_CHATS:
            key = (data["session_id"], data["user_message"])
            if key not in existing_sessions:
                db.add(
                    ChatHistory(
                        id=str(uuid.uuid4()),
                        session_id=data["session_id"],
                        user_message=data["user_message"],
                        ai_response=data["ai_response"],
                    )
                )
                chats_added += 1

        db.commit()
        print(f"Seeding complete: users={users_added}, tasks={tasks_added}, chats={chats_added}")


if __name__ == "__main__":
    seed()
