import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# AzureのSSL接続要件を満たすため、サーバーの正当性を検証するための
# SSL証明書ファイルを指定します。
connect_args = {
    "ssl_ca": "./DigiCertGlobalRootCA.crt.pem"
}

# create_engineに関数を渡して、SSL設定を適用する
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
