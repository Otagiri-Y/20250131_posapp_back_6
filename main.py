import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from db.connection import get_db
from db.crud import search_product
from pydantic import BaseModel

# 環境変数を読み込む
load_dotenv()

# FastAPI のインスタンスを作成
app = FastAPI()

# フロントエンドのオリジンを環境変数から取得（デフォルトはローカル環境）
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

# CORS（クロスオリジンリソースシェアリング）の設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],  # 許可するオリジン
    allow_credentials=True,
    allow_methods=["*"],  # 許可するHTTPメソッド
    allow_headers=["*"],  # 許可するHTTPヘッダー
)

# フロントエンドからのリクエストデータ型を定義（Pydantic 使用）
class JANRequest(BaseModel):
    jan_code: str  # JANコード（13桁の文字列）

# 商品検索 API エンドポイント
@app.post("/search")
async def search_product_api(request: JANRequest, db: AsyncSession = Depends(get_db)):
    """
    指定されたJANコードで商品を検索し、結果を返す API。
    """
    product = await search_product(db, request.jan_code)
    if product:
        return product
    else:
        raise HTTPException(status_code=404, detail="Product not found")

# Gunicorn により起動するため、ここで `uvicorn.run()` は不要
