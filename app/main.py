from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from .database import SessionLocal, test_connection, engine
from . import models
from decimal import Decimal
from sqlalchemy import select

# データベース接続テストとテーブル作成
try:
    test_connection()
    # テーブルを作成
    models.Base.metadata.create_all(bind=engine)
    print("Database connection successful and tables created!")
except Exception as e:
    print(f"Database initialization error: {str(e)}")

app = FastAPI()

# CORSミドルウェアの設定を更新
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://tech0-gen8-step4-pos-app-57.azurewebsites.net"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductResponse(BaseModel):
    PRD_ID: int
    CODE: str
    NAME: str
    PRICE: int

class ProductItem(BaseModel):
    prd_id: int
    code: str
    name: str
    price: int
    quantity: int

class TransactionRequest(BaseModel):
    emp_cd: Optional[str] = None
    store_cd: Optional[str] = None
    pos_no: Optional[str] = None
    products: List[ProductItem]

class TransactionResponse(BaseModel):
    total_amount: int
    total_amount_ex_tax: int

def get_tax_rate(tax_code: str = '10') -> Decimal:
    """
    税マスタから指定された税コードの税率を取得する
    Args:
        tax_code: 税コード（デフォルト: '10'）
    Returns:
        Decimal: 税率（例: 0.10）
    """
    db = SessionLocal()
    try:
        # 税マスタから税率を取得
        stmt = select(models.Tax).where(models.Tax.CODE == tax_code)
        tax = db.execute(stmt).scalar_one_or_none()
        
        if tax:
            print(f"Found tax rate: {tax.PERCENT} for code: {tax_code}")
            return tax.PERCENT
        
        print(f"Tax code {tax_code} not found, using default rate: 0.10")
        return Decimal('0.10')  # デフォルト税率
    finally:
        db.close()

@app.get("/api/products/{code}", response_model=ProductResponse)
async def get_product(code: str):
    db = SessionLocal()
    try:
        print(f"Searching for product with code: {code}")
        # SQLクエリをログ出力
        query = db.query(models.Product).filter(models.Product.CODE == code)
        print(f"SQL Query: {query}")
        
        product = query.first()
        if product:
            print(f"Found product: {vars(product)}")  # 製品の全属性を出力
            return {
                "PRD_ID": product.PRD_ID,
                "CODE": product.CODE,
                "NAME": product.NAME,
                "PRICE": product.PRICE
            }
        else:
            print(f"No product found with code: {code}")
            raise HTTPException(status_code=404, detail="商品が見つかりません")
            
    except Exception as e:
        import traceback
        print(f"Error occurred: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")  # スタックトレースを出力
        raise HTTPException(status_code=500, detail=f"サーバーエラー: {str(e)}")
    finally:
        db.close()

@app.post("/api/transactions", response_model=TransactionResponse)
async def create_transaction(transaction: TransactionRequest):
    db = SessionLocal()
    try:
        # 税率を取得
        tax_rate = get_tax_rate('10')  # 現在は'10'固定
        
        # 合計金額（税抜）を計算
        total_amount_ex_tax = sum(item.price * item.quantity for item in transaction.products)
        
        # 合計金額（税込）を計算
        total_amount = int(total_amount_ex_tax * (1 + tax_rate))
        
        # トランザクションを作成
        db_transaction = models.Transaction(
            DATETIME=datetime.now(),
            EMP_CD=transaction.emp_cd or "9999999999",
            STORE_CD=transaction.store_cd or "30",
            POS_NO=transaction.pos_no or "90",
            TOTAL_AMT=total_amount,
            TTL_AMT_EX_TAX=total_amount_ex_tax
        )
        db.add(db_transaction)
        db.flush()
        
        # トランザクション明細を作成
        for idx, item in enumerate(transaction.products, 1):
            detail = models.TransactionDetail(
                TRD_ID=db_transaction.TRD_ID,
                DTL_ID=idx,
                PRD_ID=item.prd_id,
                PRD_CODE=item.code,
                PRD_NAME=item.name,
                PRD_PRICE=item.price,
                TAX_CD='10'  # 消費税区分（'10'固定）
            )
            db.add(detail)
        
        db.commit()
        
        # レスポンスを返す
        return {
            "total_amount": total_amount,
            "total_amount_ex_tax": total_amount_ex_tax
        }
    except Exception as e:
        db.rollback()
        print(f"Error in create_transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close() 