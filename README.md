# Eagle OCR — Eagle-Eye

![Eagle OCR — Web Background](frontend/eaglebk.png)

[![Status](https://img.shields.io/badge/status-development-orange)](https://github.com/smigoh/Eagle-Eye)
[![Language](https://img.shields.io/badge/language-Python%20%7C%20Java%20%7C%20C%2B%2B-blue)](https://github.com/smigoh/Eagle-Eye)

Eagle OCR is an integrated computer-vision and weighbridge revenue management system designed for government use. It automates vehicle identification and weighbridge revenue capture by combining camera-based license-plate capture, OCR, weight recording, and centralized record-keeping and analytics. Eagle OCR helps county governments and national transport/regulatory agencies reduce revenue leakage, speed enforcement, and improve operational efficiency at weighbridges, parking areas and checkpoints.

> NOTE: This project is under active development. Expect breaking changes and incomplete features.

## Quick links
- Live frontend (GitHub Pages): https://smigoh.github.io/Eagle-Eye/  (deployment via GitHub Actions)
- API: FastAPI service in `eagleai.py` (POST `/process`, GET `/records`)
- Frontend: `frontend/eagle.html`, `frontend/eagle.js`, `frontend/eagle.css`
- CLI tools: `eagle.java` (Java) and `eagle.c++` (C++)

---

## Why Eagle OCR
Eagle OCR is built to support Kenyan county governments and national agencies by:

- Automating plate capture at weighbridges and parking points.
- Linking weighbridge measurements to vehicles (gross/tare/net) to compute revenue and fines.
- Providing auditable digital records for enforcement and reporting.
- Integrating with national registries and payment systems (future integration).

### Advantages
- Reduced revenue leakage through automated recording.
- Faster vehicle processing and reduced queueing at weighbridges.
- Consistent enforcement with auditable records.
- Data-driven planning for road maintenance and policy.

---

## Visual assets & icons
Use the images in `frontend/` for branding and presentation. Example assets:

- `frontend/logo.png` — primary logo
- `frontend/eaglebk.png` — startup background (used in README)
- `frontend/login.png` / `frontend/logologin.png` — login and banner images

You can include these in documents or slides with simple Markdown image links:

```markdown
![Eagle Logo](frontend/logo.png)
```

For icons and UI templates, the frontend uses Font Awesome (CDN) and simple glass-panel templates in `frontend/eagle.html` + `frontend/eagle.css`.

---

## Frontend (stylish, interactive)
The static frontend is in `frontend/`. It now includes an upload UI to POST video files to the API and a results area to show OCR + weight results.

Run locally:

```bash
cd frontend
python -m http.server 8000
# open http://localhost:8000/eagle.html
```

Production: the repository includes a GitHub Actions workflow that publishes the `frontend/` directory to GitHub Pages. See `.github/workflows/gh-pages.yml`.

---

## How to run the API (development)
Prerequisites: Python 3.8+, system Tesseract OCR installed, and Python deps.

1. Install system Tesseract (Ubuntu):
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev
```

2. Create virtualenv and install Python deps:
```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn opencv-python pytesseract numpy
```

3. Run the API:
```bash
python eagleai.py
# or
uvicorn eagleai:app --host 0.0.0.0 --port 5000
```

4. From the frontend UI (or curl), POST a video and form fields (gross, tare, vtype). The frontend provides a simple upload form.

---

## Debugging & deployment notes
- The FastAPI app exposes `POST /process` to upload a video, and `GET /records` to fetch stored records (SQLite `eagle.db`).
- The repo contains a reference Postgres schema `eagle.sql` (35 tables) for production planning. The runtime SQLite database is `eagle.db` (used by the Python/Java/C++ tools).
- Deployment: a GitHub Actions workflow publishes the `frontend/` directory to GitHub Pages on push to `main`. After first deployment, enable Pages in the repository settings if needed.

---

## Contributing
Contributions are welcome. Suggested starting points:

- Improve plate detection (replace contour-based detector with a trained detector).
- Harden backend (move to Postgres, add auth, logging, and migrations).
- Improve frontend UX and add authentication.

Please file issues or open a pull request with a focused change.

---

## License
Specify license here. If you want an MIT license, add a LICENSE file and replace this section accordingly.
