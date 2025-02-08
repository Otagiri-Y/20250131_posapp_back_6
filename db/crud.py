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

async def create_transaction(db: AsyncSession, cashier_code: str):
    """
    新しい取引情報を m_product_joe_trd に追加する
    - 取引一意キー (TRD_ID) を生成
    - 取引日付（DATETIME）、レジ担当者コード（EMP_CD）、店舗コード（STORE_CD）、POS機能ID（POS_NO）、合計金額（TOTAL_AMT）を登録
    - 取引一意キーを返す
    """
    try:
        # 取引一意キーの最大値を取得し、インクリメント
        query = text("SELECT COALESCE(MAX(TRD_ID), 0) + 1 AS new_id FROM m_product_joe_trd")
        result = await db.execute(query)
        transaction_id = result.scalar()

        # 取引情報を挿入
        insert_query = text("""
            INSERT INTO m_product_joe_trd (TRD_ID, DATETIME, EMP_CD, STORE_CD, POS_NO, TOTAL_AMT)
            VALUES (:trd_id, :datetime, :cashier_code, :store_code, :pos_id, :total_amount)
        """)

        await db.execute(insert_query, {
            "trd_id": transaction_id,
            "datetime": datetime.now(),
            "cashier_code": cashier_code,
            "store_code": 30,
            "pos_id": 90,
            "total_amount": 0  # 初期値 0
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

async def update_transaction_total(db: AsyncSession, transaction_id: int, total_price: int):
    """
    取引の合計金額を更新する
    """
    try:
        update_query = text("""
            UPDATE m_product_joe_trd SET TOTAL_AMT = :total_price WHERE TRD_ID = :trd_id
        """)

        await db.execute(update_query, {
            "total_price": total_price,
            "trd_id": transaction_id
        })
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
