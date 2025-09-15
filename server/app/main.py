from fastapi import FastAPI, UploadFile, File, Form
from typing import Literal, Optional
from io import BytesIO
import os, time
from PIL import Image
import numpy as np
import cv2
import httpx

app = FastAPI(title="PetCare API")

@app.get("/health")
def health():
    return {"ok": True}

def _img_to_arrays(file: UploadFile):
    raw = file.file.read()
    pil = Image.open(BytesIO(raw)).convert("RGB")
    arr = np.array(pil)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    return arr, gray

def _quality_gates(gray: np.ndarray):
    mean = float(gray.mean())
    low_light = mean < 55
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    blur = lap_var < 110.0
    return {"low_light": low_light, "blur": blur, "light_mean": mean, "lap_var": lap_var}

def _classify_skin(rgb: np.ndarray):
    r, g, b = [rgb[:,:,i].mean() for i in range(3)]
    brightness = (r+g+b)/3.0
    red_margin = r - max(g, b)
    if brightness > 230: return "dandruff_like", 0.72
    if red_margin > 18:  return "mild_redness", min(0.9, 0.5 + red_margin/60)
    return "normal", 0.6

def _classify_poop(rgb: np.ndarray):
    r, g, b = [rgb[:,:,i].mean() for i in range(3)]
    brightness = (r+g+b)/3.0
    red_margin = r - max(g, b)
    if red_margin > 35:       return "suspected_blood", 0.9
    if brightness > 170:      return "diarrhea", 0.75
    if 120 < brightness <= 170: return "soft_stool", 0.65
    return "normal_stool", 0.6

@app.post("/scan")
def scan(image: UploadFile = File(...), kind: Literal["skin","poop"] = Form(...)):
    rgb, gray = _img_to_arrays(image)
    gates = _quality_gates(gray)
    label, conf = (_classify_skin(rgb) if kind=="skin" else _classify_poop(rgb))
    if gates["low_light"] or gates["blur"]:
        conf = max(0.3, conf - 0.25)
    return {"label": label, "confidence": round(conf,2), "gates": gates}

TEMPLATE_MAP = {
    "mild_redness": {"home":"• 温和清洁；48h 观察","visit":"若加重/破溃/发热 → 就医"},
    "dandruff_like":{"home":"• 轻梳理去屑；注意过敏源","visit":"若大片脱毛/结痂 → 就医"},
    "normal":{"home":"• 未见明显异常；记录观察","visit":"若红肿渗液/抓挠不止 → 就医"},
    "normal_stool":{"home":"• 清洁饮水与规律饮食","visit":"若黏液/黑便/精神差 → 就医"},
    "soft_stool":{"home":"• 少量多餐；观察 24–48h","visit":"若>3次/天或呕吐 → 就医"},
    "diarrhea":{"home":"• 6–12h 轻度禁食后少量多餐","visit":"若含血/幼宠/发热 → 立即就医"},
    "suspected_blood":{"home":"• 暂停零食；记录颜色频次","visit":"红色/黑褐色便 → 立即就医"},
}

async def _ask_dify(label: str, species: Optional[str], lang: str, timeout_s=6):
    base = os.getenv("DIFY_API_BASE"); key = os.getenv("DIFY_APP_KEY")
    if not base or not key: return None
    payload = {"inputs":{"label":label,"species":species or "cat","lang":lang}, "response_mode":"blocking"}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        try:
            resp = await client.post(f"{base.rstrip('/')}/v1/workflows/run", json=payload, headers=headers)
            if resp.status_code == 200: return resp.json()
        except Exception: return None
    return None

@app.post("/advice")
async def advice(label: str, species: Optional[str] = None, lang: str = "zh"):
    start = time.time()
    data = await _ask_dify(label, species, lang, timeout_s=6)
    used = time.time() - start
    if data: return {"source":"dify","elapsed":round(used,2),"data":data}
    tpl = TEMPLATE_MAP.get(label) or TEMPLATE_MAP["normal"]
    return {"source":"template","elapsed":round(used,2),"home_care_md":tpl["home"],"visit_threshold_md":tpl["visit"]}
