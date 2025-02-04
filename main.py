import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# アプリケーションのインスタンスを作成
app = FastAPI()

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],  # 許可するオリジン
    allow_credentials=True,
    allow_methods=["*"],  # 許可するHTTPメソッド
    allow_headers=["*"],  # 許可するHTTPヘッダー
)
@app.get("/")
async def root():
    return {"message": "Hello World"}