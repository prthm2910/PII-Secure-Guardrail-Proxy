from app.db.session import engine, Base
from app.models.audit import AuditLog

def reset_db():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ SUCCESS: Database schema reset and updated.")

if __name__ == "__main__":
    reset_db()
