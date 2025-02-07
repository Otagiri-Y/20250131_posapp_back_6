import os
import urllib.parse
import logging
import tempfile
import atexit
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text  # ✅ `text()` を明示的にインポート
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager

# .envの読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数からデータベース接続情報を取得
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = urllib.parse.quote_plus(os.getenv("DB_PASSWORD"))  # パスワードのエンコード
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_SSL_CA_CONTENT = os.getenv("DB_SSL_CA")  # SSL証明書の内容

# SSL証明書を一時ファイルに保存
temp_pem_path = None
if DB_SSL_CA_CONTENT:
    try:
        pem_content = DB_SSL_CA_CONTENT.replace("\\n", "\n")  # 改行コードを適切に変換

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".pem") as temp_pem:
            temp_pem.write(pem_content)
            temp_pem_path = temp_pem.name

        atexit.register(lambda: os.unlink(temp_pem_path))
        logger.info("SSL証明書を一時ファイルに保存しました。")

    except Exception as e:
        logger.error(f"SSL証明書の処理中にエラーが発生しました: {e}")
        raise

# **修正: SSLContext を作成**
ssl_context = None
if temp_pem_path:
    ssl_context = ssl.create_default_context(cafile=temp_pem_path)

# Azure MySQL用の接続URL（非同期）
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# **修正: SSLContext を connect_args に渡す**
connect_args = {"ssl": ssl_context} if ssl_context else {}

# SQLAlchemy の非同期エンジンを作成
engine = create_async_engine(DATABASE_URL, echo=True, connect_args=connect_args)

# セッションを作成
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# セッションを取得するための関数（FastAPI の依存関係として使用）
async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database session error: {e}")
        raise
    finally:
        await db.close()

# データベース接続テスト用の関数
async def test_connection():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))  # ✅ `text("SELECT 1")` に修正
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

# **修正: `lifespan` を使い FastAPI 起動時に `test_connection()` を実行**
@asynccontextmanager
async def lifespan(app: FastAPI):
    await test_connection()
    yield

app = FastAPI(lifespan=lifespan)  # ✅ FastAPI 起動時に DB 接続確認を実行
