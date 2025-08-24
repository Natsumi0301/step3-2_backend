import hashlib
from database import SessionLocal
from models import User

# app.pyから転記したダミーユーザーデータ
DUMMY_USERS = [
    {
        "id": 1,
        "name": "山田太郎",
        "email": "test@example.com",
        "password": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "password"
    },
    {
        "id": 2,
        "name": "佐藤花子",
        "email": "user@example.com",
        "password": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # "secret123"
    }
]

def seed_users():
    db = SessionLocal()
    try:
        for user_data in DUMMY_USERS:
            # 既に同じメールアドレスのユーザーがいないか確認
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                # ER図のuser_id(PK)に、ダミーデータのidをマッピング
                new_user = User(
                    user_id=user_data["id"],
                    name=user_data["name"],
                    email=user_data["email"],
                    password=user_data["password"]
                    # birthdayなどの他の必須でないカラムはNULLのまま登録されます
                )
                db.add(new_user)
                print(f"ユーザー '{user_data['name']}' を追加しました。")
            else:
                print(f"ユーザー '{user_data['name']}' は既に存在するため、スキップしました。")
        
        db.commit()
        print("✅ ユーザーデータの投入が完了しました。")

    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding user data...")
    seed_users()
