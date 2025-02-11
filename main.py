from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from db.connection import get_db
from db.crud import search_product, create_transaction, add_transaction_detail, update_transaction_total
from pydantic import BaseModel
from datetime import datetime
from typing import List

# 環境変数を読み込む
load_dotenv()

# FastAPI のインスタンスを作成
app = FastAPI()

# フロントエンドのオリジンを環境変数から取得
frontend_origin = "http://localhost:3000"

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test")
async def root():
    return {"message": "Hello World"}

class JANRequest(BaseModel):
    jan_code: str

class BuyRequest(BaseModel):
    jan_codes: List[str]  # 購入する商品のJANコードリスト

@app.post("/search")
async def search_product_api(request: JANRequest, db: AsyncSession = Depends(get_db)):
    """
    指定されたJANコードの商品を検索し、結果を返す API
    """
    product = await search_product(db, request.jan_code)
    if product:
        return product
    else:
        raise HTTPException(status_code=404, detail="Product not found")

@app.post("/buy")
async def buy_products(request: BuyRequest, db: AsyncSession = Depends(get_db)):
    """
    取引を作成し、商品を追加して、合計金額を返す API
    """
    try:
        # 取引情報を作成
        transaction_id = await create_transaction(db)

        details = []
        detail_id = 1

        for jan_code in request.jan_codes:
            product = await search_product(db, jan_code)
            if not product:
                raise HTTPException(status_code=404, detail=f"商品 {jan_code} が見つかりません")

            # 取引明細に追加
            await add_transaction_detail(db, transaction_id, detail_id, product)

            details.append({
                "transaction_id": transaction_id,
                "detail_id": detail_id,
                "product_id": product["PRD_ID"],
                "product_code": product["CODE"],
                "product_name": product["NAME"],
                "product_price": product["PRICE"]
            })
            detail_id += 1

        # 合計金額を計算し、取引情報を更新
        total_price = await update_transaction_total(db, transaction_id)

        return {
            "transaction_id": transaction_id,
            "total_price": total_price,
            "details": details
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
