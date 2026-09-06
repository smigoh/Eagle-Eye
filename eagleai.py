import os
import cv2
import sqlite3
import pytesseract
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil

# ============================================================
# CONFIG
# ============================================================
UPLOAD_DIR = "uploads"
DB_FILE = "eagle.db"  # Use a SQLite DB file (was 'eagle.sql' which is a SQL script)
RATE_PER_TON = 50
LEGAL_LIMITS = {"LCV": 3, "MEDIUM": 10, "HEAVY": 20, "TANKER": 25}

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================
# DATABASE
# ============================================================
class EagleDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        # Return rows as dictionaries
        self.conn.row_factory = sqlite3.Row
        self._create()

    def _create(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT,
            vehicle_type TEXT,
            gross REAL,
            tare REAL,
            net REAL,
            revenue REAL,
            fine REAL,
            source TEXT,
            timestamp TEXT
        )""")
        self.conn.commit()

    def insert(self, r: dict):
        try:
            self.conn.execute("""
            INSERT INTO records (plate, vehicle_type, gross, tare, net, revenue, fine, source, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (r.get("plate", "UNKNOWN"), r.get("type", "UNKNOWN"), r.get("gross", 0.0), r.get("tare", 0.0), r.get("net", 0.0), r.get("revenue", 0.0), r.get("fine", 0.0), r.get("source", ""), r.get("timestamp", "")))
            self.conn.commit()
        except Exception as e:
            # Keep the app running but report the DB error
            print("DB insert error:", e)

    def fetch_all(self):
        cur = self.conn.execute("SELECT * FROM records ORDER BY id DESC")
        rows = cur.fetchall()
        # Convert sqlite3.Row to dict
        return [dict(row) for row in rows]

# ============================================================
# OPENCV PLATE DETECTOR (No YOLO)
# ============================================================
class CVDetector:
    """Uses Image Processing to find License Plate candidates."""
    def detect_plates(self, frame):
        plates = []
        if frame is None:
            return plates

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
                if h == 0:
                    continue
                aspect_ratio = w / float(h)

                # Filter by typical plate aspect ratios (2.0 to 5.5)
                if 2.0 < aspect_ratio < 5.5:
                    # Ensure ROI is within frame bounds
                    h0, w0 = frame.shape[:2]
                    x1 = max(0, x)
                    y1 = max(0, y)
                    x2 = min(w0, x + w)
                    y2 = min(h0, y + h)
                    if x2 > x1 and y2 > y1:
                        plates.append(frame[y1:y2, x1:x2])
        
        return plates

# ============================================================
# OCR ENGINE
# ============================================================
class OCR:
    def read(self, img):
        if img is None or img.size == 0: return None
        try:
            # Pre-process for Tesseract
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            # PSM 7: Treat image as a single text line
            config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            text = pytesseract.image_to_string(gray, config=config)

            clean_text = "".join(c for c in text if c.isalnum()).strip()
            return clean_text if len(clean_text) >= 4 else None
        except Exception:
            return None

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

        net = float(meta.get("gross", 0.0)) - float(meta.get("tare", 0.0))
        limit = LEGAL_LIMITS.get(meta.get("type", "").upper(), 0)
        excess = max(0, net - limit)

        return {
            "plate": plate_text,
            "type": meta.get("type", "UNKNOWN").upper(),
            "gross": float(meta.get("gross", 0.0)),
            "tare": float(meta.get("tare", 0.0)),
            "net": net,
            "revenue": net * RATE_PER_TON,
            "fine": excess * 10000
        }

app = FastAPI()
# Allow the frontend to call the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(video.file, f)

        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            return JSONResponse({"error": "Could not open video"}, status_code=400)

        result = {"plate": "UNKNOWN"}
        count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or count > 300: break # Scan first 300 frames max

            if count % 10 == 0: # Sample every 10th frame for speed
                meta = {"gross": gross, "tare": tare, "type": vtype}
                res = agent.process(frame, meta)
                if res.get("plate") and res["plate"] != "UNKNOWN":
                    result = res
                    break
            count += 1

        cap.release()
        result["source"] = video.filename
        result["timestamp"] = datetime.now().isoformat()
        db.insert(result)
        return result

    finally:
        # cleanup temporary upload file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

@app.get("/records")
async def get_records():
    records = db.fetch_all()
    return JSONResponse(records)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
