import sqlalchemy
from sqlalchemy import create_engine, text
from app.core.config import settings

def test_db_connection():
    print(f"Connecting to Postgres at {settings.POSTGRES_SERVER}...")
    try:
        # Use the SQLALCHEMY_DATABASE_URI which combines everything
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database();"))
            db_name = result.scalar()
            print(f"✅ SUCCESS: Connected to Postgres! Current DB: {db_name}")
            
            # Check if AuditLog table exists
            result = connection.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'audit_logs');"))
            table_exists = result.scalar()
            if table_exists:
                print("✅ SUCCESS: 'audit_logs' table exists.")
            else:
                print("⚠️ WARNING: 'audit_logs' table NOT found. Run migrations/creation script.")
                
    except Exception as e:
        print(f"❌ ERROR: Database connection failed: {e}")

if __name__ == "__main__":
    test_db_connection()
