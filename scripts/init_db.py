from app.db.session import engine, Base
# Import models to ensure they are registered with Base
from app.models.audit import AuditLog

def init_db():
    print("Initializing Database Tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ SUCCESS: All tables created successfully.")
    except Exception as e:
        print(f"❌ ERROR: Failed to create tables: {e}")

if __name__ == "__main__":
    init_db()
