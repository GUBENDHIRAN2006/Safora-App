import httpx
import psycopg2
import time

DATABASE_URL = "postgresql://postgres.wocwjmikitjzyytuczhw:gubendhiran123@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
BASE_URL = "http://localhost:8000/api"

TEST_EMAIL = "test_user_antigravity@safora.com"
TEST_PASSWORD = "password123"
TEST_NAME = "Antigravity Test User"

def clean_database():
    """Removes the test user from database to ensure fresh registration."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email = %s", (TEST_EMAIL,))
        conn.commit()
        cur.close()
        conn.close()
        print("Cleaned up test user from database successfully.")
    except Exception as e:
        print(f"Database clean error: {e}")

def run_tests():
    # 1. Clean database
    clean_database()
    
    # Wait for server to start if needed
    time.sleep(2)
    
    print("\n--- Starting Auth Tests ---")
    with httpx.Client(timeout=10.0) as client:
        # 2. Test Registration
        register_payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": TEST_NAME
        }
        print(f"1. Sending Registration Request: {register_payload['email']}")
        try:
            r = client.post(f"{BASE_URL}/auth/register", json=register_payload)
            print(f"   Status Code: {r.status_code}")
            print(f"   Response Content: {r.text}")
            assert r.status_code == 201, f"Expected 201, got {r.status_code}"
            print("   Registration successful!")
        except Exception as e:
            print(f"   Registration request failed: {e}")
            return

        # 3. Test Login
        login_payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        print(f"\n2. Sending Login Request: {login_payload['email']}")
        try:
            r = client.post(f"{BASE_URL}/auth/login", json=login_payload)
            print(f"   Status Code: {r.status_code}")
            print(f"   Response Content: {r.text}")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            token_data = r.json()
            token = token_data.get("access_token")
            token_type = token_data.get("token_type")
            assert token is not None, "Access token is missing"
            print("   Login successful!")
        except Exception as e:
            print(f"   Login request failed: {e}")
            return

        # 4. Test User Profile (auth/me)
        print(f"\n3. Fetching User Profile (/auth/me)")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            r = client.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"   Status Code: {r.status_code}")
            print(f"   Response Content: {r.text}")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            profile_data = r.json()
            assert profile_data.get("email") == TEST_EMAIL, f"Expected {TEST_EMAIL}, got {profile_data.get('email')}"
            print("   Profile retrieval successful!")
        except Exception as e:
            print(f"   Profile request failed: {e}")
            return

        print("\n--- All Auth Tests Completed Successfully! ---")

if __name__ == "__main__":
    run_tests()
