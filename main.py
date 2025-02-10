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

class AddRequest(BaseModel):
    jan_codes: List[str]
    cashier_code: str = "9999999999"

class PurchaseRequest(BaseModel):
    transaction_id: int

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

@app.post("/add")
async def add_products(request: AddRequest, db: AsyncSession = Depends(get_db)):
    """
    取引情報を作成し、商品を追加する API
    """
    try:
        # 取引を作成
        transaction_id = await create_transaction(db, request.cashier_code)

        details = []
        detail_id = 1

        for jan_code in request.jan_codes:
            product = await search_product(db, jan_code)
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with JAN {jan_code} not found")

            # 取引明細を追加
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

        return {
            "transaction_id": transaction_id,
            "details": details
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/purchase")
async def purchase_products(request: PurchaseRequest, db: AsyncSession = Depends(get_db)):
    """
    取引の合計金額を更新する API
    """
    try:
        # 取引一意キーで合計金額を計算
        total_price = await update_transaction_total(db, request.transaction_id)

        return {"transaction_id": request.transaction_id, "total_price": total_price}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
