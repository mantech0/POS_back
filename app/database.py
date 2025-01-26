from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Azure Database for MySQL接続情報
AZURE_MYSQL_HOST = "tech0-gen-8-step4-db-3.mysql.database.azure.com"
AZURE_MYSQL_USER = "Tech0Gen8TA3"
AZURE_MYSQL_PASSWORD = "New_password"  # 実際のパスワードを設定
AZURE_MYSQL_DATABASE = "pos"
AZURE_MYSQL_PORT = "3306"

# SQLAlchemy接続URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{AZURE_MYSQL_USER}:{AZURE_MYSQL_PASSWORD}@{AZURE_MYSQL_HOST}:{AZURE_MYSQL_PORT}/{AZURE_MYSQL_DATABASE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "ssl": {
            "ssl_ca": None  # Azure MySQL は SSL 証明書を自動的に処理します
        }
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# データベース接続テスト用
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        raise e 