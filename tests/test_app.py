def test_generate_recipe(client):
    # Assuming recipe with ID 1 exists. Adjust ID as needed.
    r = client.post('/recipes/1/generate')
    assert r.status_code in (200, 404)  # Depending on presence of recipe
    if r.status_code == 200:
        assert "instructions" in r.json

def test_chat_authorized(client, monkeypatch):
    # Simulate logged-in session
    with client.session_transaction() as sess:
        sess['user'] = 'admin'

    class DummyResp:
        def __getitem__(self, key):
            return [{"message": {"content": "Simulated response"}}] if key == "choices" else None

    monkeypatch.setattr("openai.ChatCompletion.create", lambda **kwargs: DummyResp())

    r = client.post('/chat', json={"prompt": "Hello"})
    assert r.status_code == 200
    assert r.json == {"response": "Simulated response"}
