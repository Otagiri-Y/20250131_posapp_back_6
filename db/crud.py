from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from sqlalchemy import text

# 商品検索関数
async def search_product(db: AsyncSession, jan_code: str):
    """
    データベースから JAN コードに対応する商品情報を取得する関数。
    """
    try:
        # SQLクエリを定義（プレースホルダーを使用）
        query = text("SELECT PRD_ID, CODE, NAME, PRICE FROM m_product_joe_prd WHERE CODE = :code")
        result = await db.execute(query, {"code": jan_code})
        product = result.mappings().first()
        return product if product else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
