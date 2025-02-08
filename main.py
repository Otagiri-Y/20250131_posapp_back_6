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

class JANRequest(BaseModel):
    jan_code: str

class PurchaseRequest(BaseModel):
    jan_codes: List[str]  
    cashier_code: str = "9999999999"

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

@app.post("/purchase")
async def purchase_products(request: PurchaseRequest, db: AsyncSession = Depends(get_db)):
    """
    商品を購入し、取引を登録する API
    """
    try:
        transaction_id = await create_transaction(db, request.cashier_code)

        total_price = 0  
        detail_id = 1  

        for jan_code in request.jan_codes:
            product = await search_product(db, jan_code)
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with JAN {jan_code} not found")

            await add_transaction_detail(db, transaction_id, detail_id, product)
            total_price += product["PRICE"]  
            detail_id += 1  

        await update_transaction_total(db, transaction_id, total_price)

        return {"transaction_id": transaction_id, "total_price": total_price}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
