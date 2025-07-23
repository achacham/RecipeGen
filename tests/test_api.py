def test_categories(client):
    r = client.get('/categories')
    assert r.status_code == 200
    assert isinstance(r.json, list)

def test_recipes(client):
    r = client.get('/recipes')
    assert r.status_code == 200
    assert isinstance(r.json, list)

def test_single_recipe(client):
    r = client.get('/recipes/1')
    assert r.status_code in (200, 404)  # depending on recipe existence

def test_generate_recipe(client):
    r = client.post('/recipes/1/generate')
    assert r.status_code in (200, 404)  # depending on recipe existence

def test_history(client):
    r = client.get('/history')
    assert r.status_code == 200
    assert isinstance(r.json, list)

def test_login_success(client):
    r = client.post('/login', json={"username": "admin", "password": "password123"})
    assert r.status_code == 200
    assert r.json['status'] == 'success'

def test_login_failure(client):
    r = client.post('/login', json={"username": "wrong", "password": "wrong"})
    assert r.status_code == 401
    assert r.json['status'] == 'failure'

def test_chat_authorized(client, monkeypatch):
    # Simulate logged-in session
    with client.session_transaction() as sess:
        sess['user'] = 'admin'

    class DummyResp:
        def __getitem__(self, key):
            return [{"message": {"content": "Test response"}}] if key == "choices" else None

    monkeypatch.setattr("openai.ChatCompletion.create", lambda **kwargs: DummyResp())

    r = client.post('/chat', json={"prompt": "Hello"})
    assert r.status_code == 200
    assert r.json == {"response": "Test response"}

def test_chat_unauthorized(client):
    r = client.post('/chat', json={"prompt": "Should fail"})
    assert r.status_code == 403
    assert r.json['error'] == 'Unauthorized'
