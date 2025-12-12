# tests/test_api.py
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"

def test_auth_ping(client):
    r = client.get("/auth/ping")
    assert r.status_code == 200
    assert r.get_json()["auth"] == "ok"

def test_games_ping(client):
    r = client.get("/games/ping")
    assert r.status_code == 200
    assert r.get_json()["games"] == "ok"
