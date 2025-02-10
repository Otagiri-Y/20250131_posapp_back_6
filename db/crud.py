from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from sqlalchemy import text
from datetime import datetime

async def search_product(db: AsyncSession, jan_code: str):
    """
    JANコードをもとに商品情報を検索する
    """
    try:
        query = text("SELECT PRD_ID, CODE, NAME, PRICE FROM m_product_joe_prd WHERE CODE = :code")
        result = await db.execute(query, {"code": jan_code})
        product = result.mappings().first()  # 商品情報を取得
        return product if product else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def create_transaction(db: AsyncSession):
    """
    新しい取引情報を m_product_joe_trd に追加する
    - `cashier_code` を固定 (`9999999999`)
    """
    try:
        query = text("SELECT COALESCE(MAX(TRD_ID), 0) + 1 AS new_id FROM m_product_joe_trd")
        result = await db.execute(query)
        transaction_id = result.scalar()

        insert_query = text("""
            INSERT INTO m_product_joe_trd (TRD_ID, DATETIME, EMP_CD, STORE_CD, POS_NO, TOTAL_AMT)
            VALUES (:trd_id, :datetime, :cashier_code, :store_code, :pos_id, :total_amount)
        """)

        await db.execute(insert_query, {
            "trd_id": transaction_id,
            "datetime": datetime.now(),
            "cashier_code": "9999999999",  # 固定値に変更
            "store_code": 30,
            "pos_id": 90,
            "total_amount": 0
        })
        await db.commit()
        return transaction_id
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def add_transaction_detail(db: AsyncSession, transaction_id: int, detail_id: int, product: dict):
    """
    取引明細 (m_product_joe_dtl) に商品を追加する
    """
    try:
        insert_query = text("""
            INSERT INTO m_product_joe_dtl (TRD_ID, DTL_ID, PRD_ID, PRD_CODE, PRD_NAME, PRD_PRICE)
            VALUES (:trd_id, :trd_dtl_id, :prd_id, :prd_code, :prd_name, :prd_price)
        """)

        await db.execute(insert_query, {
            "trd_id": transaction_id,
            "trd_dtl_id": detail_id,
            "prd_id": product["PRD_ID"],
            "prd_code": product["CODE"],
            "prd_name": product["NAME"],
            "prd_price": product["PRICE"]
        })
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def update_transaction_total(db: AsyncSession, transaction_id: int):
    """
    取引の合計金額を更新する
    """
    try:
        # 取引明細から合計金額を計算
        query = text("""
            SELECT COALESCE(SUM(PRD_PRICE), 0) FROM m_product_joe_dtl WHERE TRD_ID = :trd_id
        """)
        result = await db.execute(query, {"trd_id": transaction_id})
        total_price = result.scalar()

        # 合計金額を更新
        update_query = text("""
            UPDATE m_product_joe_trd SET TOTAL_AMT = :total_price WHERE TRD_ID = :trd_id
        """)

        await db.execute(update_query, {
            "total_price": total_price,
            "trd_id": transaction_id
        })
        await db.commit()

        return total_price
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")