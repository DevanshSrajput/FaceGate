# Product Requirements Document
## Smart Face Recognition-Based Access Control System
**Project Code:** CWV-FR-001 | **Version:** 1.0 | **Status:** Draft | **Date:** May 2026  
**Author:** Garvita Agarwal (Roll No. 2103493) | **Guide:** Mrs. Gunjan Mehra, Graphic Era University

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Goals & Objectives](#2-goals--objectives)
3. [Scope](#3-scope)
4. [System Architecture](#4-system-architecture)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [File & Folder Structure](#7-file--folder-structure)
8. [Module Specifications](#8-module-specifications)
9. [Configuration Reference](#9-configuration-reference)
10. [Data Models](#10-data-models)
11. [Algorithm Specifications](#11-algorithm-specifications)
12. [Dependencies & Requirements](#12-dependencies--requirements)
13. [External API Integrations](#13-external-api-integrations)
14. [User Stories](#14-user-stories)
15. [Testing Requirements](#15-testing-requirements)
16. [Implementation Phases](#16-implementation-phases)
17. [Deliverables Checklist](#17-deliverables-checklist)
18. [Glossary](#18-glossary)
19. [Revision History](#19-revision-history)

---

## 1. Project Overview

This document defines the full product requirements for building the **Smart Face Recognition-Based Access Control System** — a real-time, computer-vision-powered security system that replaces traditional access mechanisms (keys, cards, PINs) with biometric facial recognition. It is intended to serve as a complete, unambiguous specification for an autonomous AI agent or development team to implement the project end-to-end.

| Field | Value |
|---|---|
| Project Name | Smart Face Recognition-Based Access Control System |
| Short Name | FaceGate / CWV-Scanner |
| Author / Student | Garvita Agarwal (Roll No. 2103493) |
| Guide | Mrs. Gunjan Mehra, Dept. of Computer Applications, Graphic Era University |
| Degree | Bachelor of Computer Applications (BCA) |
| Tech Stack | Python 3.x, OpenCV, face_recognition (dlib), Flask, SQLite, Telegram Bot API |

---

## 2. Goals & Objectives

### 2.1 Business / Academic Goals
- Demonstrate a working prototype of a smart, contactless security system.
- Replace traditional access methods (cards, PINs, keys) with biometric facial recognition.
- Provide a real-time, automated, and auditable access control workflow.
- Show integration of computer vision, web development, database management, and alerting in a single cohesive system.

### 2.2 Specific Technical Objectives
1. Implement accurate, real-time face detection using HOG + CNN (via dlib/face_recognition library).
2. Generate 128-dimensional face embeddings for each enrolled user and persist them.
3. Match live face encodings against stored embeddings using Euclidean distance with a configurable threshold.
4. Automate access control decisions: GRANT for authorized users, DENY for unknown individuals.
5. Capture and store timestamped intruder images on unauthorized access attempts.
6. Log all access events (name, status, timestamp) in a structured SQLite database.
7. Send real-time Telegram (and optionally email) alerts to administrators on unauthorized access detection.
8. Build a Flask web dashboard with login, access log view, and live camera control.
9. Ensure the system is modular and allows easy addition of new authorized users.

---

## 3. Scope

### 3.1 In Scope
- Real-time webcam feed capture and face detection.
- Face enrollment: capturing and storing face encodings for authorized users.
- Face recognition pipeline: detect → encode → match → decide.
- Access control module: grant/deny logic with confidence threshold.
- SQLite-based event logging system.
- Intruder image capture and local storage.
- Telegram Bot integration for instant unauthorized access alerts.
- Flask web application with login, dashboard, and log viewer.
- Basic anti-spam cooldown mechanism for alert generation.
- Modular codebase for future extension.

### 3.2 Out of Scope (Version 1.0)
- Anti-spoofing / liveness detection (protection against photo/video attacks).
- Multi-camera or CCTV network integration.
- Mobile application or native desktop app.
- Cloud-based storage or cloud deployment.
- RFID/smart card hybrid integration.
- Role-based access control (RBAC) for different permission levels.
- Raspberry Pi or embedded hardware deployment.
- Real electronic door lock actuation.

---

## 4. System Architecture

### 4.1 High-Level Architecture

The system is composed of six tightly coupled modules that communicate through shared state and a central database:

| Module | Responsibility | Primary Files |
|---|---|---|
| M1 — Camera Module | Captures live frames from webcam using OpenCV VideoCapture. | face_detection.py, main.py |
| M2 — Face Recognition Engine | Detects faces, generates 128-d embeddings, and matches against enrolled users. | face_recognition, dlib |
| M3 — Access Control Logic | Applies Euclidean distance threshold to make grant/deny decisions. | access_control.py |
| M4 — Logging System | Writes access events to SQLite DB with name, status, and timestamp. | database.py |
| M5 — Alert System | Captures intruder images and sends Telegram alerts with cooldown logic. | alert.py |
| M6 — Web Dashboard | Flask app with login, log viewer, and camera control routes. | app.py, templates/ |

### 4.2 Data Flow

1. Webcam captures a frame every N milliseconds.
2. Frame is passed to Face Detection → one or more face locations returned.
3. For each detected face, a 128-d embedding is computed.
4. Embedding is compared to all stored encodings using Euclidean distance.
5. If distance < THRESHOLD → user is identified → Access **GRANTED** → log event.
6. If distance >= THRESHOLD → user is unknown → Access **DENIED** → log event → capture image → trigger alert (if cooldown allows).
7. All events are immediately written to SQLite.
8. Web dashboard reads from SQLite to display live logs.

---

## 5. Functional Requirements

### 5.1 Face Enrollment Module
*Purpose: Register new authorized users into the system before deployment.*

| Req. ID | Requirement |
|---|---|
| FR-ENR-01 | System shall provide a script/CLI command to enroll a new user by name. |
| FR-ENR-02 | Enrollment shall capture at least 1 clear facial image per user from the webcam. |
| FR-ENR-03 | System shall compute a 128-d face embedding for each enrolled image. |
| FR-ENR-04 | Embeddings shall be serialized and saved to a persistent file (encodings.pkl or similar). |
| FR-ENR-05 | Enrollment script shall validate that a face is detected before saving — reject blank/no-face captures. |
| FR-ENR-06 | Multiple images per user should be supportable (for robustness) — store all embeddings mapped to the same name. |
| FR-ENR-07 | System shall print a confirmation message upon successful enrollment. |

### 5.2 Real-Time Face Detection & Recognition
*Purpose: Detect and identify faces in each live frame from the camera.*

| Req. ID | Requirement |
|---|---|
| FR-DET-01 | System shall capture frames from the default webcam (index 0) using OpenCV. |
| FR-DET-02 | System shall resize/downsample frames before processing to maintain real-time performance (e.g., 25% scale). |
| FR-DET-03 | System shall use face_recognition.face_locations() with model='hog' (default) or 'cnn' (configurable) to detect face bounding boxes. |
| FR-DET-04 | System shall use face_recognition.face_encodings() to generate 128-d embeddings for all detected faces in a frame. |
| FR-DET-05 | System shall compare each live encoding against all stored encodings using face_recognition.compare_faces() and face_recognition.face_distance(). |
| FR-DET-06 | System shall pick the stored encoding with the minimum distance as the best match candidate. |
| FR-DET-07 | If minimum distance < RECOGNITION_THRESHOLD (default: 0.6), the face is classified as the matching known user. |
| FR-DET-08 | If minimum distance >= RECOGNITION_THRESHOLD, the face is classified as 'Unknown'. |
| FR-DET-09 | System shall draw bounding boxes around detected faces on the live feed — GREEN for authorized, RED for unknown. |
| FR-DET-10 | System shall overlay the user name (or 'Unknown') and distance score on the bounding box label. |
| FR-DET-11 | RECOGNITION_THRESHOLD shall be a configurable constant in a config file or environment variable. |

### 5.3 Access Control Module
*Purpose: Make and enforce the access grant or deny decision.*

| Req. ID | Requirement |
|---|---|
| FR-ACC-01 | System shall output ACCESS GRANTED when a face matches a known user below the threshold. |
| FR-ACC-02 | System shall output ACCESS DENIED when a face is classified as Unknown. |
| FR-ACC-03 | System shall implement multi-frame confirmation: require a face to be recognized consistently for N consecutive frames (default: N=3) before triggering a GRANT event, to reduce false positives. |
| FR-ACC-04 | System shall implement a per-user access cooldown: once a user is granted access, suppress duplicate GRANT logs for the same user for a configurable duration (default: 30 seconds). |
| FR-ACC-05 | Access decisions shall be accompanied by a visual indicator (colored bounding box) on the local display. |
| FR-ACC-06 | A session log of grant/deny events shall be maintained in memory and flushed to SQLite in real time. |

### 5.4 Database & Logging Module
*Purpose: Maintain a persistent, structured audit trail of all access events.*

| Req. ID | Requirement |
|---|---|
| FR-LOG-01 | System shall use SQLite as the database engine with no external database server dependency. |
| FR-LOG-02 | System shall auto-create the database and table on first run if they do not exist. |
| FR-LOG-03 | The access_logs table shall have columns: id (INTEGER PRIMARY KEY), name (TEXT), status (TEXT: 'Granted'/'Denied'), timestamp (DATETIME DEFAULT CURRENT_TIMESTAMP), image_path (TEXT, nullable). |
| FR-LOG-04 | Every access event (grant or deny) shall result in a new row insertion within 500ms of the event. |
| FR-LOG-05 | System shall support querying all logs, filtering by date range, and filtering by user name. |
| FR-LOG-06 | Database file location shall be configurable (default: ./data/access_logs.db). |

### 5.5 Intruder Detection & Image Capture
*Purpose: Collect evidence when unauthorized access is attempted.*

| Req. ID | Requirement |
|---|---|
| FR-INT-01 | On every ACCESS DENIED event, system shall capture the current frame from the webcam. |
| FR-INT-02 | The captured image shall be saved as a JPEG file with filename format: intruder_YYYYMMDD_HHMMSS.jpg. |
| FR-INT-03 | Images shall be saved to a configurable directory (default: ./intruders/). |
| FR-INT-04 | The image file path shall be recorded in the image_path column of the corresponding access_logs row. |
| FR-INT-05 | System shall ensure the intruders directory is created automatically if it does not exist. |
| FR-INT-06 | Intruder images shall include the annotated bounding box and 'Unknown' label overlay before saving. |

### 5.6 Alert System (Telegram Bot)
*Purpose: Notify administrators in real time when unauthorized access is detected.*

| Req. ID | Requirement |
|---|---|
| FR-ALT-01 | System shall integrate with Telegram Bot API to send alert messages. |
| FR-ALT-02 | Alert message shall contain: 'ALERT: Unauthorized access detected at \<timestamp\>. Image attached.' |
| FR-ALT-03 | Alert shall include the captured intruder image as a photo attachment in the Telegram message. |
| FR-ALT-04 | Telegram Bot Token and Chat ID shall be stored in environment variables or a .env file — never hardcoded. |
| FR-ALT-05 | System shall implement an alert cooldown: after sending one alert, suppress additional alerts for the same 'Unknown' trigger for a configurable duration (default: 60 seconds). |
| FR-ALT-06 | Alerts shall be sent asynchronously (separate thread) to avoid blocking the main recognition loop. |
| FR-ALT-07 | System shall log alert dispatch success/failure to a local log file (alerts.log). |
| FR-ALT-08 | (Optional) System shall support email alerts via smtplib as a secondary channel. |

### 5.7 Web Dashboard (Flask)
*Purpose: Provide a centralized, browser-accessible interface for monitoring and control.*

| Req. ID | Requirement |
|---|---|
| FR-WEB-01 | System shall expose a Flask web application on localhost:5000 (configurable port). |
| FR-WEB-02 | The app shall require username/password login before accessing any protected route. |
| FR-WEB-03 | Admin credentials shall be stored securely (hashed with werkzeug.security or bcrypt) — not in plain text. |
| FR-WEB-04 | Route /dashboard shall display: total events today, total authorized accesses, total denied, last 10 events. |
| FR-WEB-05 | Route /logs shall display the full access log in a paginated HTML table with columns: ID, Name, Status, Timestamp, Image. |
| FR-WEB-06 | Route /logs/filter shall support GET parameters ?name=&status=&date= for filtered queries. |
| FR-WEB-07 | Route /intruders shall display a gallery of captured intruder images with timestamps. |
| FR-WEB-08 | Route /start shall trigger the face recognition camera loop to begin (if not already running). |
| FR-WEB-09 | Route /stop shall gracefully terminate the camera loop. |
| FR-WEB-10 | Dashboard shall auto-refresh or support live updates (SSE or polling every 5 seconds) for the log table. |
| FR-WEB-11 | All pages shall be served with a consistent, minimal HTML/CSS template (Bootstrap or custom CSS). |
| FR-WEB-12 | Route /logout shall terminate the user session. |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Req. ID | Requirement |
|---|---|
| NFR-PERF-01 | Face detection and recognition loop shall run at minimum 10 FPS on recommended hardware (Intel i5, 8GB RAM). |
| NFR-PERF-02 | Access decision (grant/deny) shall be made within 500ms of a face appearing in frame. |
| NFR-PERF-03 | Telegram alert (including image upload) shall be dispatched within 5 seconds of unauthorized detection. |
| NFR-PERF-04 | Web dashboard page load time shall be under 2 seconds for up to 10,000 log rows. |

### 6.2 Reliability & Accuracy

| Req. ID | Requirement |
|---|---|
| NFR-REL-01 | System shall achieve face recognition accuracy > 90% under normal indoor lighting for enrolled users. |
| NFR-REL-02 | System shall gracefully handle camera disconnection — display error and attempt reconnect. |
| NFR-REL-03 | SQLite writes shall be wrapped in try/except to prevent recognition loop crashes on DB errors. |
| NFR-REL-04 | Alert failures (network down, Telegram API error) shall be caught and logged without crashing the system. |

### 6.3 Security

| Req. ID | Requirement |
|---|---|
| NFR-SEC-01 | Telegram Bot Token and Chat ID shall never appear in source code — use .env and python-dotenv. |
| NFR-SEC-02 | Flask admin password shall be stored as a bcrypt/werkzeug hash. |
| NFR-SEC-03 | Flask sessions shall use a randomly generated SECRET_KEY stored in .env. |
| NFR-SEC-04 | The .env file shall be listed in .gitignore — never committed to version control. |
| NFR-SEC-05 | Intruder images directory shall not be publicly accessible via Flask static routes. |

### 6.4 Usability

| Req. ID | Requirement |
|---|---|
| NFR-USE-01 | Enrollment script shall provide clear CLI prompts with instructions. |
| NFR-USE-02 | Live camera window shall display bounding boxes, names, and access status in real time. |
| NFR-USE-03 | Web dashboard shall be usable on modern browsers (Chrome, Firefox, Edge) without plugins. |
| NFR-USE-04 | README.md shall include step-by-step setup, enrollment, and run instructions. |

### 6.5 Maintainability & Scalability

| Req. ID | Requirement |
|---|---|
| NFR-MAI-01 | Codebase shall be organized into modules (see Section 8) — no monolithic single-file script. |
| NFR-MAI-02 | Adding a new user shall require only running the enrollment script — no code changes. |
| NFR-MAI-03 | All configurable values (threshold, cooldown, DB path, ports) shall be in config.py or .env. |
| NFR-MAI-04 | System shall support at least 100 enrolled users without degradation in recognition speed. |

---

## 7. File & Folder Structure

Every file listed below is a required deliverable:

```
face-recognition-system/
│
├── main.py                    # Entry point — starts camera loop
├── enroll.py                  # CLI script to enroll new users
├── config.py                  # All configurable constants
├── requirements.txt           # All pip dependencies
├── .env                       # Secrets (not committed to git)
├── .env.example               # Template showing required env vars
├── .gitignore                 # Must include .env, *.pkl, /intruders
├── README.md                  # Setup + usage documentation
│
├── modules/
│   ├── __init__.py
│   ├── face_engine.py         # Face detection + encoding + matching
│   ├── access_control.py      # Grant/deny logic + multi-frame confirm
│   ├── database.py            # SQLite init, insert, query functions
│   ├── alert.py               # Telegram + optional email alert sender
│   └── camera.py              # OpenCV capture + frame utilities
│
├── web/
│   ├── app.py                 # Flask application + all routes
│   ├── auth.py                # Login/logout + session management
│   ├── static/
│   │   ├── style.css          # Custom dashboard CSS
│   │   └── logo.png           # (optional) branding
│   └── templates/
│       ├── base.html          # Base layout with nav
│       ├── login.html         # Admin login page
│       ├── dashboard.html     # Summary dashboard
│       ├── logs.html          # Full log table with filters
│       └── intruders.html     # Intruder image gallery
│
├── data/
│   ├── encodings.pkl          # Serialized face embeddings (auto-generated)
│   └── access_logs.db         # SQLite database (auto-generated)
│
└── intruders/                 # Captured intruder images (auto-created)
```

---

## 8. Module Specifications

### 8.1 modules/face_engine.py

| Function Signature | Description |
|---|---|
| `load_encodings(path)` | Loads serialized (name, encoding) pairs from .pkl file. Returns: `List[Tuple[str, np.ndarray]]` |
| `save_encodings(data, path)` | Serializes enrollment data to .pkl. Called by enroll.py. |
| `detect_faces(frame)` | Takes a BGR OpenCV frame. Returns: list of `(top, right, bottom, left)` bounding boxes. |
| `encode_faces(frame, locations)` | Given frame + face locations, returns list of 128-d `np.ndarray` embeddings. |
| `match_face(encoding, known_encodings, threshold)` | Computes Euclidean distances, returns `(best_match_name, distance)` or `('Unknown', distance)`. |
| `annotate_frame(frame, locations, names, statuses)` | Draws colored bounding boxes + labels on frame in-place. |

### 8.2 modules/access_control.py

| Component | Description |
|---|---|
| `AccessController` class | Stateful class that maintains per-user cooldowns and frame confirmation buffers. |
| `decide(name, distance)` | Returns `('GRANTED', name)` or `('DENIED', 'Unknown')` after applying multi-frame confirmation logic. |
| `can_log(name)` | Returns True if cooldown period has passed for this user. Updates last_seen timestamp. |
| `reset()` | Clears all state — call on camera stop. |

### 8.3 modules/database.py

| Function | Description |
|---|---|
| `init_db(db_path)` | Creates DB + table if not exists. Safe to call on every startup. |
| `log_event(name, status, image_path=None)` | Inserts one row into access_logs. Handles exceptions silently. |
| `get_logs(limit, offset, filters)` | Returns list of log dicts with pagination + optional filter by name/status/date. |
| `get_summary()` | Returns dict: `{total_today, granted_today, denied_today, last_events: [...]}` |

### 8.4 modules/alert.py

| Component | Description |
|---|---|
| `AlertManager` class | Wraps Telegram API calls with cooldown logic and async dispatch. |
| `send_telegram_alert(image_path, timestamp)` | Sends photo + caption to configured Telegram chat. Runs in a daemon thread. |
| `can_alert()` | Returns True if cooldown has elapsed since last alert. |
| `send_email_alert(image_path, timestamp)` | (Optional) SMTP-based email fallback. |

### 8.5 web/app.py — Flask Routes

| Route | Specification |
|---|---|
| `GET /` | Redirect to /dashboard if logged in, else /login. |
| `GET /login` + `POST /login` | Render login form; validate credentials; set session. |
| `GET /logout` | Clear session, redirect to /login. |
| `GET /dashboard` | Render dashboard.html with summary stats from get_summary(). |
| `GET /logs` | Render logs.html with paginated results from get_logs(). |
| `GET /logs/filter` | Return filtered log rows (supports AJAX/JSON response with ?format=json). |
| `GET /intruders` | Render intruders.html — list files from ./intruders/ directory. |
| `POST /start` | Spawn recognition loop in background thread if not running. Return JSON status. |
| `POST /stop` | Signal recognition loop to stop. Return JSON status. |
| `GET /status` | Return JSON: `{running: bool, fps: float, last_event: dict}` |

---

## 9. Configuration Reference

All tunable parameters shall reside in `config.py`:

| Constant | Default Value | Description |
|---|---|---|
| `RECOGNITION_THRESHOLD` | `0.6` | Euclidean distance threshold for face match. Lower = stricter. |
| `CONFIRMATION_FRAMES` | `3` | Consecutive matching frames before a GRANT event fires. |
| `ACCESS_COOLDOWN_SEC` | `30` | Seconds before same authorized user triggers another GRANT log. |
| `ALERT_COOLDOWN_SEC` | `60` | Seconds before another intruder alert is sent (prevents spam). |
| `CAMERA_INDEX` | `0` | OpenCV VideoCapture index (0 = default webcam). |
| `FRAME_SCALE` | `0.25` | Downsample factor applied to each frame before recognition. |
| `DB_PATH` | `./data/access_logs.db` | File path for SQLite database. |
| `ENCODINGS_PATH` | `./data/encodings.pkl` | File path for serialized face encodings. |
| `INTRUDERS_DIR` | `./intruders/` | Directory where intruder images are saved. |
| `FLASK_PORT` | `5000` | Port on which Flask web app listens. |
| `DETECTION_MODEL` | `hog` | Face detection model: 'hog' (fast) or 'cnn' (accurate, GPU recommended). |

The following secrets **MUST** be in `.env` (not config.py):

| Variable | Example Value | Purpose |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | (from BotFather) | Telegram Bot API token. |
| `TELEGRAM_CHAT_ID` | (your chat ID) | Telegram chat/user ID to receive alerts. |
| `FLASK_SECRET_KEY` | (random string) | Secret key for Flask session signing. |
| `ADMIN_USERNAME` | `admin` | Dashboard login username. |
| `ADMIN_PASSWORD_HASH` | (bcrypt hash) | Bcrypt-hashed dashboard password. |

---

## 10. Data Models

### 10.1 SQLite: access_logs Table

| Column | Type & Constraints |
|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT |
| `name` | TEXT NOT NULL — 'Unknown' for intruders, else enrolled username |
| `status` | TEXT NOT NULL — Values: 'Granted' or 'Denied' |
| `timestamp` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP |
| `image_path` | TEXT NULLABLE — Relative path to intruder JPEG, NULL for authorized access |

```sql
CREATE TABLE IF NOT EXISTS access_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    status     TEXT    NOT NULL CHECK(status IN ('Granted', 'Denied')),
    timestamp  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT
);
```

### 10.2 Face Encodings File (encodings.pkl)

A Python pickle file containing:
```python
List[Tuple[str, numpy.ndarray]]
# e.g. [("Alice", array([0.12, -0.34, ...])), ("Bob", array([...]))]
```
Each tuple = `(user_name_string, 128_dimensional_float_array)`. Multiple tuples with the same name are allowed (multiple images per user).

### 10.3 Intruder Image Files

JPEG files saved in `/intruders/` with naming convention:
```
intruder_YYYYMMDD_HHMMSS.jpg
# e.g. intruder_20260508_143022.jpg
```
Each image is the annotated webcam frame at the moment of detection.

---

## 11. Algorithm Specifications

### 11.1 Face Detection

- **Library:** face_recognition (wraps dlib)
- **Method:** HOG-based (default) or CNN-based (config flag)
- **Input:** RGB frame — convert from BGR using `frame[:, :, ::-1]`
- **Output:** List of bounding boxes as `(top, right, bottom, left)` pixel tuples

### 11.2 Face Encoding

- **Library:** face_recognition
- **Method:** Deep metric learning → 128-dimensional feature vector per face
- **Model:** ResNet variant trained on ~3 million face images
- **Process:** Detect 68-point face landmarks → align face → project into embedding space
- **Property:** Similar faces → low Euclidean distance; dissimilar faces → high distance

### 11.3 Matching Algorithm

For each live encoding `E_live` and each stored encoding `E_stored[i]`:

```
d_i     = ||E_live - E_stored[i]||₂       # Euclidean distance
best_i  = argmin(d_i)                      # closest stored encoding

if d_best < RECOGNITION_THRESHOLD:
    → identified as known_names[best_i]    # AUTHORIZED
else:
    → classified as "Unknown"              # UNAUTHORIZED
```

### 11.4 Multi-Frame Confirmation

To reduce false positives:
1. Maintain rolling buffer of last N detections per face region.
2. GRANT event fires only when same name appears in all N consecutive frames.
3. Buffer resets on scene change (face disappears from frame).

```python
# Pseudocode
if confirmation_buffer[face_id].count(name) == CONFIRMATION_FRAMES:
    trigger_grant_event(name)
```

### 11.5 Cooldown Logic

Both access cooldown and alert cooldown use same pattern:

```python
last_triggered = {}

def can_trigger(key, cooldown_sec):
    now = datetime.now()
    if key not in last_triggered:
        last_triggered[key] = now
        return True
    if (now - last_triggered[key]).seconds > cooldown_sec:
        last_triggered[key] = now
        return True
    return False
```

---

## 12. Dependencies & Requirements

### 12.1 requirements.txt

```
opencv-python>=4.8.0
face-recognition>=1.3.0
dlib>=19.24.0
numpy>=1.24.0
Flask>=3.0.0
Werkzeug>=3.0.0
python-dotenv>=1.0.0
requests>=2.31.0
Pillow>=10.0.0
```

| Package | Min Version | Purpose |
|---|---|---|
| opencv-python | 4.8.0 | Webcam capture, frame processing, image I/O |
| face-recognition | 1.3.0 | Face detection, landmark detection, encoding, comparison |
| dlib | 19.24.0 | Backend for face_recognition (auto-installed as dependency) |
| numpy | 1.24.0 | Array operations for embedding math |
| Flask | 3.0.0 | Web dashboard framework |
| Werkzeug | 3.0.0 | Password hashing (pbkdf2_sha256 or bcrypt) |
| python-dotenv | 1.0.0 | Load .env secrets into os.environ |
| requests | 2.31.0 | Telegram Bot API HTTP calls |
| Pillow | 10.0.0 | Image manipulation before sending alerts |

### 12.2 Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| CPU | Intel Core i3 (8th gen) / AMD Ryzen 3 | Intel Core i5/i7 (10th gen+) / AMD Ryzen 5/7 |
| RAM | 4 GB | 8 GB+ |
| Storage | 20 GB free (HDD) | SSD (faster DB I/O) |
| Camera | Built-in webcam (480p) | USB HD webcam (720p/1080p) |
| OS | Windows 10/11 or Ubuntu 20.04 | Ubuntu 22.04 LTS |
| Internet | Required for Telegram alert dispatch | — |

---

## 13. External API Integrations

### 13.1 Telegram Bot API

| Parameter | Value |
|---|---|
| Endpoint | `https://api.telegram.org/bot{TOKEN}/sendPhoto` |
| Method | POST |
| Auth | Bot token in URL path (from env var `TELEGRAM_BOT_TOKEN`) |
| Payload | `chat_id`, `photo` (file bytes), `caption` (string with timestamp) |
| Error Handling | Catch `requests.exceptions.RequestException`; log to alerts.log; do not raise |

**Setup Steps:**
1. Create bot via `@BotFather` on Telegram.
2. Copy the bot token → save as `TELEGRAM_BOT_TOKEN` in .env.
3. Get your chat ID via `@userinfobot` → save as `TELEGRAM_CHAT_ID` in .env.
4. Test with a manual POST request before wiring into the system.

```python
# Example alert dispatch
def send_telegram_alert(image_path, timestamp):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    caption = f"ALERT: Unauthorized access detected at {timestamp}"
    with open(image_path, 'rb') as photo:
        response = requests.post(url, data={
            'chat_id': CHAT_ID,
            'caption': caption
        }, files={'photo': photo})
    return response.status_code == 200
```

---

## 14. User Stories

### 14.1 Administrator

| ID | Story |
|---|---|
| US-ADM-01 | As an admin, I want to enroll new authorized users so that the system recognizes them. |
| US-ADM-02 | As an admin, I want to log in to the web dashboard so that I can monitor access events securely. |
| US-ADM-03 | As an admin, I want to see a summary of today's access activity on the dashboard so I can assess security status at a glance. |
| US-ADM-04 | As an admin, I want to filter access logs by date, name, or status so I can investigate specific incidents. |
| US-ADM-05 | As an admin, I want to view captured intruder images so I can identify unauthorized visitors. |
| US-ADM-06 | As an admin, I want to receive a Telegram alert instantly when an intruder is detected so I can respond quickly. |
| US-ADM-07 | As an admin, I want to start and stop the camera feed from the dashboard so I can control the system remotely. |

### 14.2 Authorized User

| ID | Story |
|---|---|
| US-USR-01 | As an authorized user, I want the system to recognize my face quickly so I can gain access without delay. |
| US-USR-02 | As an authorized user, I want visual feedback (green box + name) confirming I am recognized. |

---

## 15. Testing Requirements

### 15.1 Unit Tests

| Test ID | Description |
|---|---|
| UT-01 | Test `match_face()` with known identical encoding → expect distance 0.0, correct name returned. |
| UT-02 | Test `match_face()` with unknown encoding → expect 'Unknown' when distance > threshold. |
| UT-03 | Test `init_db()` creates table with correct schema. |
| UT-04 | Test `log_event()` inserts a row retrievable via `get_logs()`. |
| UT-05 | Test `AccessController.can_log()` respects cooldown window. |
| UT-06 | Test `AlertManager.can_alert()` returns False within cooldown, True after cooldown. |

### 15.2 Integration Tests

| Test ID | Description |
|---|---|
| IT-01 | Enroll test user → run recognition on photo of that user → expect GRANTED event in DB. |
| IT-02 | Run recognition on unknown face photo → expect DENIED event + intruder image saved. |
| IT-03 | Flask route /logs returns HTTP 200 and contains log rows after events are logged. |
| IT-04 | Flask POST /start spawns camera thread; GET /status returns `{running: true}`. |

### 15.3 Manual Acceptance Tests

| Test ID | Description |
|---|---|
| MAT-01 | System correctly grants access to all enrolled users under normal indoor lighting. |
| MAT-02 | System correctly denies access to faces not in the enrollment database. |
| MAT-03 | Telegram alert received within 10 seconds of unauthorized detection. |
| MAT-04 | Intruder image saved to /intruders/ and linked in the DB row. |
| MAT-05 | Web dashboard login rejects wrong credentials; allows correct credentials. |
| MAT-06 | Log filter by date range returns only events within the specified range. |

---

## 16. Implementation Phases

Recommended build order for an AI agent or developer:

| Phase | Name | Description | Deliverable |
|---|---|---|---|
| 1 | Core Engine | Set up project structure. Implement face_engine.py and enroll.py. Verify enrollment + recognition work via CLI with test image. | Working recognition from static image. |
| 2 | Live Camera Loop | Implement camera.py and main.py. Integrate face_engine into real-time webcam loop. Add bounding box overlay. | Live recognition with visual feedback. |
| 3 | Access Control | Implement access_control.py with multi-frame confirmation + cooldown. | Stable grant/deny decisions on live feed. |
| 4 | Logging | Implement database.py. Wire access decisions to DB inserts. Verify rows in SQLite. | Persistent access log. |
| 5 | Intruder Capture | Add intruder image capture to DENIED path. Save to /intruders/ and update DB row. | Images saved + linked in DB. |
| 6 | Alerts | Implement alert.py. Set up Telegram bot. Test alert dispatch on DENIED event. | Telegram alert with image received on phone. |
| 7 | Web Dashboard | Implement Flask app with all routes. Build HTML templates. Add login/auth. | Functional dashboard with live log refresh. |
| 8 | Config & Cleanup | Centralize all constants into config.py and .env. Write README.md. Add .gitignore. Final integration test. | Production-ready codebase. |

---

## 17. Deliverables Checklist

| Deliverable | Description |
|---|---|
| Source Code | Complete Python codebase in folder structure defined in Section 7. |
| requirements.txt | All pip dependencies with pinned minimum versions. |
| .env.example | Template showing all required environment variable names (no actual secrets). |
| .gitignore | Must include `.env`, `*.pkl`, `/intruders`, `__pycache__`, `*.pyc`, `/data`. |
| README.md | Installation steps, environment setup, enrollment instructions, run commands. |
| Demo Video / Screenshot | Evidence of working system: live recognition + dashboard + Telegram alert. |
| SQLite Database | Pre-populated with at least 10 sample log entries for demonstration. |
| Test Files | Unit test file (test_modules.py) covering all items in Section 15.1. |

---

## 18. Glossary

| Term | Definition |
|---|---|
| Face Embedding | A 128-dimensional numerical vector that encodes the unique facial features of a person. |
| Euclidean Distance | Straight-line distance between two vectors in n-dimensional space. Used to compare face embeddings. |
| RECOGNITION_THRESHOLD | Maximum Euclidean distance for a face to be considered a match. Lower = stricter. |
| HOG | Histogram of Oriented Gradients — a feature descriptor used for fast face detection. |
| CNN | Convolutional Neural Network — a deep learning model used for more accurate (but slower) face detection. |
| dlib | An open-source C++ machine learning library with Python bindings; backend for face_recognition. |
| Flask | A lightweight Python WSGI web framework used to build the dashboard. |
| SQLite | A serverless, file-based relational database engine built into Python. |
| Telegram Bot API | A REST API provided by Telegram for programmatically sending messages and media. |
| Cooldown | A time-based suppression mechanism preventing repeated events within a defined window. |
| Multi-frame Confirmation | Requiring a face to be consistently recognized across N consecutive frames before triggering an event. |
| GRANT / DENY | Access outcomes: GRANT = authorized user recognized; DENY = unknown face detected. |

---

## 19. Revision History

| Version | Date | Summary |
|---|---|---|
| 1.0 | May 2026 | Initial draft — Full PRD created from CWV_scanner_synopsis.docx. All sections defined. |

---

*END OF DOCUMENT — FaceGate PRD v1.0*
