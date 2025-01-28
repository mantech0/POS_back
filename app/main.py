from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from .database import SessionLocal, test_connection, engine
from . import models

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

@app.post("/api/transactions")
async def create_transaction(request: TransactionRequest):
    db = SessionLocal()
    try:
        # 取引データの作成
        total_amount = sum(p.price * p.quantity for p in request.products)
        transaction = models.Transaction(
            DATETIME=datetime.now(),
            EMP_CD=request.emp_cd or "9999999999",
            STORE_CD=request.store_cd or "30",
            POS_NO=request.pos_no or "90",
            TOTAL_AMT=total_amount
        )
        db.add(transaction)
        db.flush()

        # 取引明細の作成
        for idx, product in enumerate(request.products, 1):
            detail = models.TransactionDetail(
                TRD_ID=transaction.TRD_ID,
                DTL_ID=idx,
                PRD_ID=product.prd_id,
                PRD_CODE=product.code,
                PRD_NAME=product.name,
                PRD_PRICE=product.price
            )
            db.add(detail)
        
        db.commit()
        return {"success": True, "total_amount": total_amount}
    
    except Exception as e:
        db.rollback()
        print(f"Error in create_transaction: {str(e)}")  # エラーログ追加
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close() 