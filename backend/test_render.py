import httpx

BASE_URL = 'https://safora-app-3.onrender.com/api'
TEST_EMAIL = 'render_test_final@safora.com'
TEST_PASSWORD = 'password123'
TEST_NAME = 'Render Final Test'

print('=== Testing Render Backend Auth ===')
with httpx.Client(timeout=30.0) as client:
    # 1. Register
    print('1. Testing Registration...')
    r = client.post(f'{BASE_URL}/auth/register', json={
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'full_name': TEST_NAME
    })
    print(f'   Status: {r.status_code}')
    if r.status_code == 201:
        data = r.json()
        print(f'   User ID: {data["id"]}')
        print(f'   Email: {data["email"]}')
        print('   PASS: Registration works!')
    elif r.status_code == 400:
        print('   (User already exists - OK, testing login next)')
    else:
        print(f'   FAIL: {r.text}')

    # 2. Login
    print()
    print('2. Testing Login...')
    r = client.post(f'{BASE_URL}/auth/login', json={
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    })
    print(f'   Status: {r.status_code}')
    if r.status_code == 200:
        token = r.json()['access_token']
        print(f'   Token (first 40 chars): {token[:40]}...')
        print('   PASS: Login works!')

        # 3. Profile
        print()
        print('3. Testing /auth/me...')
        r = client.get(f'{BASE_URL}/auth/me', headers={'Authorization': f'Bearer {token}'})
        print(f'   Status: {r.status_code}')
        if r.status_code == 200:
            profile = r.json()
            print(f'   Name: {profile["full_name"]}')
            print(f'   Role: {profile["role"]}')
            print('   PASS: Profile works!')
        else:
            print(f'   FAIL: {r.text}')
    else:
        print(f'   FAIL: {r.text}')

print()
print('=== All Tests Complete ===')
