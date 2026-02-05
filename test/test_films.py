def test_films_list_q_filter(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            status_code = 200
            def json(self):
                return {"results": [{"title": "A New Hope"}, {"title": "The Empire Strikes Back"}]}
        return Resp()

    import routers.films_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/films/?q=hope")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 1
    assert body["results"][0]["title"] == "A New Hope"


def test_films_sort_order(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            status_code = 200
            def json(self):
                return {"results": [
                    {"title": "B", "release_date": "2001-01-01", "episode_id": 2, "director": "X"},
                    {"title": "A", "release_date": "1999-01-01", "episode_id": 1, "director": "Y"},
                ]}
        return Resp()

    import routers.films_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/films/?sort=title&order=asc")
    assert res.status_code == 200
    titles = [x["title"] for x in res.json()["results"]]
    assert titles == ["A", "B"]


def test_films_expand_characters_summary(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            def __init__(self, data):
                self.status_code = 200
                self._data = data
            def json(self):
                return self._data

        if url.endswith("/films/"):
            return Resp({"results": [{
                "title": "A New Hope",
                "characters": ["https://swapi.dev/api/people/1/"]
            }]})

        if url.endswith("/people/1/"):
            return Resp({
                "name": "Luke Skywalker",
                "gender": "male",
                "homeworld": "https://swapi.dev/api/planets/1/"
            })

        if url.endswith("/planets/1/"):
            return Resp({"name": "Tatooine"})

        return Resp({})

    import routers.films_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/films/?expand=characters")
    assert res.status_code == 200
    luke = res.json()["results"][0]["characters"][0]
    assert luke["name"] == "Luke Skywalker"
    assert luke["homeworld"] == "Tatooine"


def test_films_detail_by_id(client, auth_off, monkeypatch):
    def fake_get(url, timeout=10):
        class Resp:
            status_code = 200
            def json(self):
                return {"title": "A New Hope"}
        return Resp()

    import routers.films_router as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/films/1")
    assert res.status_code == 200
    assert res.json()["result"]["title"] == "A New Hope"


def test_films_upstream_timeout_502(client, auth_off, monkeypatch):
    import routers.films_router as mod

    class FakeReqExc(mod.requests.RequestException):
        pass

    def fake_get(url, timeout=10):
        raise FakeReqExc("timeout")

    monkeypatch.setattr(mod.requests, "get", fake_get)

    res = client.get("/films/")
    assert res.status_code == 502
