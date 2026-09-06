# otp_generator.py
import random
import string
import psycopg2
from datetime import datetime, timedelta

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def store_otp(user_id, conn):
    otp = generate_otp()
    expires = datetime.utcnow() + timedelta(minutes=5)
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO user_otps (user_id, otp_code, expires_at, used, created_at)
            VALUES (%s, %s, %s, FALSE, %s)
        """, (user_id, otp, expires, datetime.utcnow()))
    conn.commit()
    return otp

# Example usage
if __name__ == "__main__":
    conn = psycopg2.connect("postgresql://eagle_app:change_me_app@localhost:5432/eagle_eye")
    user_id = "00000000-0000-0000-0000-000000000000"  # Replace with actual user UUID
    otp = store_otp(user_id, conn)
    print("Generated OTP:", otp)
