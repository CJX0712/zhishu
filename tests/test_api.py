from fastapi.testclient import TestClient

from zhishu.api import app


def test_health(requires_qdrant):
    c = TestClient(app)
    r = c.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_and_search(requires_qdrant):
    c = TestClient(app)
    r = c.post("/api/ingest", json={"text": "年假按入职年限计算：满1年5天。"})
    assert r.status_code == 200
    assert r.json()["ingested"] >= 1
    r2 = c.post("/api/search", json={"query": "年假怎么算", "top_k": 3})
    assert r2.status_code == 200
    assert len(r2.json()["results"]) >= 1
