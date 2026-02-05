def test_requires_api_key_when_env_set(client, auth_on):
    res = client.get("/films/")
    assert res.status_code == 401

def test_accepts_api_key_when_env_set(client, auth_on):
    res = client.get("/films/", headers={"x-api-key": "test-key"})
    assert res.status_code != 401
