from fastapi.testclient import TestClient
from app.main import app
from io import BytesIO
from PIL import Image

client = TestClient(app)

def _mk_img(color, size=(64,64)):
    img = Image.new("RGB", size, color=color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["ok"] is True

def test_scan_skin():
    buf = _mk_img((240, 80, 80))
    files = {"image": ("red.png", buf, "image/png")}
    r = client.post("/scan", files=files, data={"kind":"skin"})
    assert r.status_code == 200
    assert "label" in r.json()

def test_advice_template():
    r = client.post("/advice", params={"label":"soft_stool"})
    assert r.status_code == 200
    assert r.json()["source"] in {"template","dify"}
