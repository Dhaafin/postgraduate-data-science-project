import sqlalchemy
from sqlalchemy import text

def test_conn():
    # Let's test session mode on port 5432
    url_5432 = "postgresql://postgres.twpqzogmdzurinnwilvk:datascienceanjaywowkeren@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
    # Let's test transaction mode on port 6543
    url_6543 = "postgresql://postgres.twpqzogmdzurinnwilvk:datascienceanjaywowkeren@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
    
    print("Testing 5432 (Session Mode)...")
    try:
        engine = sqlalchemy.create_engine(url_5432)
        with engine.begin() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging")).scalar()
            print(f"Success on 5432! Artist Count: {res}")
            return
    except Exception as e:
        print(f"Failed on 5432: {e}")
        
    print("\nTesting 6543 (Transaction Mode)...")
    try:
        engine = sqlalchemy.create_engine(url_6543)
        with engine.begin() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging")).scalar()
            print(f"Success on 6543! Artist Count: {res}")
    except Exception as e:
        print(f"Failed on 6543: {e}")

if __name__ == "__main__":
    test_conn()
