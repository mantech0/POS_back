from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint, DECIMAL
from sqlalchemy.orm import relationship
from .database import Base

class Tax(Base):
    __tablename__ = 'm_tax_manzaki'
    
    ID = Column(Integer, primary_key=True)
    CODE = Column(String(2), unique=True)
    NAME = Column(String(20))
    PERCENT = Column(DECIMAL(5,2))

class Product(Base):
    __tablename__ = 'm_product_manzaki'
    
    PRD_ID = Column(Integer, primary_key=True, index=True)
    CODE = Column(String(13), unique=True, index=True)
    NAME = Column(String(50))
    PRICE = Column(Integer)

class Transaction(Base):
    __tablename__ = 't_transaction_manzaki'
    
    TRD_ID = Column(Integer, primary_key=True, index=True)
    DATETIME = Column(DateTime)
    EMP_CD = Column(String(10))
    STORE_CD = Column(String(5))
    POS_NO = Column(String(3))
    TOTAL_AMT = Column(Integer)
    TTL_AMT_EX_TAX = Column(Integer)
    
    details = relationship("TransactionDetail", back_populates="transaction")

class TransactionDetail(Base):
    __tablename__ = 't_transaction_detail_manzaki'
    
    TRD_ID = Column(Integer, ForeignKey("t_transaction_manzaki.TRD_ID"), primary_key=True)
    DTL_ID = Column(Integer, primary_key=True)
    PRD_ID = Column(Integer, ForeignKey("m_product_manzaki.PRD_ID"))
    PRD_CODE = Column(String(13))
    PRD_NAME = Column(String(50))
    PRD_PRICE = Column(Integer)
    TAX_CD = Column(String(2))
    
    transaction = relationship("Transaction", back_populates="details") 