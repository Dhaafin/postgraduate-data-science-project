import sqlalchemy
from sqlalchemy import text

def test_conn():
    url_5432 = "postgresql://postgres.twpqzogmdzurinnwilvk:datascienceanjaywowkeren@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
    print("Testing 5432 (Session Mode) with aws-1...")
    try:
        engine = sqlalchemy.create_engine(url_5432)
        with engine.begin() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging")).scalar()
            print(f"SUCCESS! Artist Count: {res}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_conn()
