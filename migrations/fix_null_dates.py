# migrations/fix_null_dates.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

def fix_null_dates():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Fix projects with NULL created_at or updated_at
        session.execute(text("""
            UPDATE projects 
            SET created_at = CURRENT_TIMESTAMP 
            WHERE created_at IS NULL
        """))
        
        session.execute(text("""
            UPDATE projects 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE updated_at IS NULL
        """))
        
        # Fix commits with NULL timestamp
        session.execute(text("""
            UPDATE commits 
            SET timestamp = CURRENT_TIMESTAMP 
            WHERE timestamp IS NULL
        """))
        
        # Fix feedback with NULL created_at
        session.execute(text("""
            UPDATE feedback 
            SET created_at = CURRENT_TIMESTAMP 
            WHERE created_at IS NULL
        """))
        
        session.commit()
        print("Successfully fixed NULL date values")
        
    except Exception as e:
        session.rollback()
        print(f"Error fixing NULL dates: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    fix_null_dates()