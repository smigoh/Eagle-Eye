
import os
import cv2
import sqlite3
import pytesseract
import numpy as np
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil

# ============================================================
# CONFIG
# ============================================================
UPLOAD_DIR = "uploads"
DB_FILE = "eagle.sql"
RATE_PER_TON = 50
LEGAL_LIMITS = {"LCV": 3, "MEDIUM": 10, "HEAVY": 20, "TANKER": 25}

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================
# DATABASE
# ============================================================
class EagleDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self._create()

    def _create(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT, vehicle_type TEXT, gross REAL, tare REAL,
            net REAL, revenue REAL, fine REAL, source TEXT, timestamp TEXT
        )""")
        self.conn.commit()

    def insert(self, r: dict):
        self.conn.execute("""
        INSERT INTO records (plate, vehicle_type, gross, tare, net, revenue, fine, source, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
        (r["plate"], r["type"], r["gross"], r["tare"], r["net"], r["revenue"], r["fine"], r["source"], r["timestamp"]))
        self.conn.commit()

    def fetch_all(self):
        return self.conn.execute("SELECT * FROM records ORDER BY id DESC").fetchall()

# ============================================================
# OPENCV PLATE DETECTOR (No YOLO)
# ============================================================
class CVDetector:
    """Uses Image Processing to find License Plate candidates."""
    def detect_plates(self, frame):
        plates = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Filter noise & Find Edges
        gray = cv2.bilateralFilter(gray, 11, 17, 17) 
        edged = cv2.Canny(gray, 30, 200)

        # 2. Find Contours
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)
            
            # If contour has 4 corners, it's potentially a plate
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / float(h)
                
                # Filter by typical plate aspect ratios (2.0 to 5.5)
                if 2.0 < aspect_ratio < 5.5:
                    plates.append(frame[y:y+h, x:x+w])
        
        return plates

# ============================================================
# OCR ENGINE
# ============================================================
class OCR:
    def read(self, img):
        if img is None or img.size == 0: return None
        
        # Pre-process for Tesseract
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        # PSM 7: Treat image as a single text line
        config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        text = pytesseract.image_to_string(gray, config=config)
        
        clean_text = "".join(c for c in text if c.isalnum()).strip()
        return clean_text if len(clean_text) >= 4 else None

# ============================================================
# AGENT & API
# ============================================================
class EagleAgent:
    def __init__(self):
        self.detector = CVDetector()
        self.ocr = OCR()

    def process(self, frame, meta):
        plate_text = "UNKNOWN"
        
        # Try all potential plate regions found by OpenCV
        candidates = self.detector.detect_plates(frame)
        for roi in candidates:
            p = self.ocr.read(roi)
            if p:
                plate_text = p
                break

        net = meta["gross"] - meta["tare"]
        limit = LEGAL_LIMITS.get(meta["type"].upper(), 0)
        excess = max(0, net - limit)

        return {
            "plate": plate_text,
            "type": meta["type"].upper(),
            "gross": meta["gross"],
            "tare": meta["tare"],
            "net": net,
            "revenue": net * RATE_PER_TON,
            "fine": excess * 10000
        }

app = FastAPI()
db = EagleDB()
agent = EagleAgent()

@app.post("/process")
async def process_video(
    video: UploadFile = File(...),
    gross: float = Form(30.0),
    tare: float = Form(10.0),
    vtype: str = Form("HEAVY")
):
    temp_path = os.path.join(UPLOAD_DIR, video.filename)
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    cap = cv2.VideoCapture(temp_path)
    result = {"plate": "UNKNOWN"}
    count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or count > 300: break # Scan first 300 frames max
        
        if count % 10 == 0: # Sample every 10th frame for speed
            meta = {"gross": gross, "tare": tare, "type": vtype}
            res = agent.process(frame, meta)
            if res["plate"] != "UNKNOWN":
                result = res
                break
        count += 1

    cap.release()
    result["source"] = video.filename
    result["timestamp"] = datetime.now().isoformat()
    db.insert(result)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
