# FaceGate

Smart Face Recognition-Based Access Control System — a real-time, computer-vision-powered security system that replaces traditional access mechanisms (keys, cards, PINs) with biometric facial recognition.

Built from [FaceGate_PRD.md](FaceGate_PRD.md) v1.0.

## Stack

| Component       | Technology                      |
| --------------- | ------------------------------- |
| Language        | Python 3.11+                    |
| Computer Vision | OpenCV, face-recognition (dlib) |
| Web Framework   | Flask 3.x                       |
| Database        | SQLite                          |
| Alerting        | Telegram Bot API + SMTP email   |
| Config          | python-dotenv                   |

## Project Structure

```
FaceGate/
├── main.py                       # Entry point — starts live camera recognition loop
├── enroll.py                     # CLI script to enroll authorized users
├── config.py                     # All configurable constants (loaded from .env)
├── requirements.txt              # Pip dependencies with minimum versions
├── .env.example                  # Template showing required environment variables
├── .gitignore                    # Excludes .env, *.pkl, /intruders, /data, logs
├── README.md                     # This file
├── test_modules.py               # Unit tests (UT-01 through UT-06)
├── test_integration.py           # Integration tests (IT-01 through IT-04)
│
├── modules/
│   ├── __init__.py
│   ├── face_engine.py            # Face detection, encoding, matching, annotation
│   ├── access_control.py         # Multi-frame confirmation + per-user cooldowns
│   ├── database.py               # SQLite init, insert, query, summary
│   ├── alert.py                  # Telegram + email alert dispatch with cooldowns
│   └── camera.py                 # OpenCV capture loop + frame classification
│
├── web/
│   ├── app.py                    # Flask application, routes, SSE endpoint
│   ├── auth.py                   # Login/logout, bcrypt validation, rate limiting
│   ├── static/
│   │   └── style.css             # Dashboard stylesheet
│   └── templates/
│       ├── base.html             # Shared layout with navigation
│       ├── login.html            # Admin login form
│       ├── dashboard.html        # Live dashboard with SSE updates
│       ├── logs.html             # Paginated, filterable access log table
│       └── intruders.html        # Captured intruder image gallery
│
├── data/                         # Auto-generated at runtime
│   ├── encodings.pkl             # Serialized face embeddings
│   └── access_logs.db            # SQLite access event database
│
├── intruders/                    # Auto-created — captured intruder JPEG images
└── artifacts/                    # Demo screenshots and assets
```

## Quick Start

### 1. Create and activate the virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

On Windows, the project venv uses `dlib-bin` and `face-recognition --no-deps` so the stack works without compiling dlib from source.

### 3. Configure environment

```powershell
copy .env.example .env
```

Edit `.env` and fill in the required values:

```env
# --- Required for alerts ---
TELEGRAM_BOT_TOKEN=           # From @BotFather on Telegram
TELEGRAM_CHAT_ID=             # Your Telegram chat ID (get via @userinfobot)

# --- Required for dashboard ---
FLASK_SECRET_KEY=             # Generate: python -c "import secrets; print(secrets.token_urlsafe(48))"

# Note: Dashboard credentials are hardcoded in config.py (Username: admin, Password: admin)

# --- Optional: email alert fallback ---
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_RECIPIENT=

# --- Tunable (defaults shown) ---
RECOGNITION_THRESHOLD=0.6
CONFIRMATION_FRAMES=3
ACCESS_COOLDOWN_SEC=30
ALERT_COOLDOWN_SEC=60
CAMERA_INDEX=0
FRAME_SCALE=0.25
DB_PATH=./data/access_logs.db
ENCODINGS_PATH=./data/encodings.pkl
INTRUDERS_DIR=./intruders/
FLASK_PORT=5000
DETECTION_MODEL=hog
```

### 4. Enroll authorized users

```powershell
python enroll.py "Alice" --samples 1
```

- Press **SPACE** to capture when exactly one face is visible
- Press **ESC** to cancel
- Use `--samples N` to capture multiple images per user (improves recognition robustness)
- Encodings are saved to `data/encodings.pkl`

### 5. Run the system

**Live recognition (desktop camera window):**

```powershell
python main.py
```

Press **Q** or **ESC** to stop. Bounding boxes: green = authorized, red = unknown.

**Web dashboard:**

```powershell
python -m web.app
```

Open `http://127.0.0.1:5000/login` in your browser.

**Default web app credentials:**

- **Username:** `admin`
- **Password:** `1` (hardcoded in config.py)

## Dashboard Routes

All routes except `/login` require authentication.

| Route                         | Method    | Description                                                                      |
| ----------------------------- | --------- | -------------------------------------------------------------------------------- |
| `/login`                      | GET, POST | Admin login form                                                                 |
| `/logout`                     | GET       | End session                                                                      |
| `/dashboard`                  | GET       | Live dashboard — summary cards, camera controls, latest events (SSE auto-update) |
| `/dashboard/stream`           | GET       | Server-Sent Events endpoint (dashboard consumes this automatically)              |
| `/logs`                       | GET       | Paginated access log table with name/status/date filters                         |
| `/logs/filter?format=json`    | GET       | Filtered logs as JSON array                                                      |
| `/intruders`                  | GET       | Intruder image gallery                                                           |
| `/intruders/image/<filename>` | GET       | Serve a captured intruder image (protected)                                      |
| `/start`                      | GET, POST | Start background camera recognition                                              |
| `/stop`                       | GET, POST | Stop background camera recognition                                               |
| `/status`                     | GET       | Camera state as JSON: `{"running": true, "fps": 12.5, ...}`                      |

## Alert Channels

### Telegram (primary)

1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
2. Copy the bot token → `TELEGRAM_BOT_TOKEN` in `.env`
3. Get your chat ID via [@userinfobot](https://t.me/userinfobot) → `TELEGRAM_CHAT_ID` in `.env`

On each unauthorized access, the system sends a photo + timestamp caption to your Telegram.

### Email (secondary fallback)

Configure SMTP in `.env` to receive email alerts alongside Telegram:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_RECIPIENT=admin@example.com
```

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833).

## Configuration Reference

All tunable parameters live in `config.py` and can be overridden via `.env`:

| Constant                | Default                 | Description                                                             |
| ----------------------- | ----------------------- | ----------------------------------------------------------------------- |
| `RECOGNITION_THRESHOLD` | `0.6`                   | Euclidean distance threshold — lower = stricter matching                |
| `CONFIRMATION_FRAMES`   | `3`                     | Consecutive frames before a GRANT event fires                           |
| `ACCESS_COOLDOWN_SEC`   | `30`                    | Seconds before same user triggers another GRANT log                     |
| `ALERT_COOLDOWN_SEC`    | `60`                    | Seconds between intruder alert dispatches                               |
| `CAMERA_INDEX`          | `0`                     | OpenCV VideoCapture device index                                        |
| `FRAME_SCALE`           | `0.25`                  | Downsample factor per frame before recognition                          |
| `DB_PATH`               | `./data/access_logs.db` | SQLite database file path                                               |
| `ENCODINGS_PATH`        | `./data/encodings.pkl`  | Serialized face encodings file                                          |
| `INTRUDERS_DIR`         | `./intruders/`          | Directory for captured intruder images                                  |
| `FLASK_PORT`            | `5000`                  | Flask web server port                                                   |
| `DETECTION_MODEL`       | `hog`                   | Face detection model: `hog` (fast) or `cnn` (accurate, GPU recommended) |

## Security

- **Secrets in `.env`**: Telegram tokens, Flask secret key, admin password hash, and SMTP credentials are never hardcoded — all read from environment via `python-dotenv`
- **`.gitignore`**: Excludes `.env`, `*.pkl`, `/intruders/`, `/data/`, `__pycache__/`, `*.log`
- **Password hashing**: Admin password stored as bcrypt/werkzeug hash — plaintext never touches disk
- **Login rate limiting**: After 5 failed login attempts from the same IP, further attempts are blocked for 5 minutes
- **Protected routes**: All dashboard routes and intruder image serving require authentication
- **Camera disconnect recovery**: After 10 consecutive frame read failures, the system releases and re-opens the camera device automatically

## Testing

### Unit Tests

```powershell
python -m unittest test_modules.py -v
```

Covers UT-01 through UT-06 from the PRD:

| Test  | Description                                  |
| ----- | -------------------------------------------- |
| UT-01 | Identical encodings match with zero distance |
| UT-02 | Unknown encodings return "Unknown"           |
| UT-03 | `init_db()` creates correct table schema     |
| UT-04 | `log_event()` inserts a retrievable row      |
| UT-05 | Access cooldown suppresses duplicate logs    |
| UT-06 | Alert cooldown suppresses duplicate alerts   |

### Integration Tests

```powershell
python -m unittest test_integration.py -v
```

Covers IT-01 through IT-04 from the PRD:

| Test  | Description                                                                           |
| ----- | ------------------------------------------------------------------------------------- |
| IT-01 | Enrolled user encoding → GRANTED event in database                                    |
| IT-02 | Unknown encoding → DENIED event + intruder image saved                                |
| IT-03 | Flask `/logs` returns HTTP 200 with log rows; `/logs/filter?format=json` returns JSON |
| IT-04 | POST `/start` spawns camera thread; GET `/status` confirms running                    |

### Syntax Check

```powershell
python -m py_compile config.py enroll.py main.py modules\face_engine.py modules\access_control.py modules\database.py modules\alert.py modules\camera.py web\app.py web\auth.py test_modules.py test_integration.py
```

## Architecture

```
┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────┐
│  Camera  │───▶│ Face Engine  │───▶│ Access Control│───▶│ Database │
│ (OpenCV) │    │ (dlib/HOG)   │    │ (multi-frame) │    │ (SQLite) │
└──────────┘    └──────────────┘    └───────────────┘    └──────────┘
                                             │
                                      ┌──────┴──────┐
                                      ▼              ▼
                                ┌──────────┐  ┌───────────┐
                                │ Intruder │  │  Alerts   │
                                │  Images  │  │(Telegram+ │
                                │  (JPEG)  │  │   Email)  │
                                └──────────┘  └───────────┘
                                             │
                                      ┌──────┴──────┐
                                      ▼              ▼
                                ┌──────────┐  ┌───────────┐
                                │  Flask   │  │  Browser  │
                                │  Server  │──▶│ Dashboard │
                                │  (SSE)   │  │  (Live)   │
                                └──────────┘  └───────────┘
```

1. Webcam captures frames at ~15-30 FPS
2. Each frame is downsampled and passed through face detection (HOG or CNN)
3. Detected faces are encoded into 128-dimensional embeddings
4. Embeddings are compared against enrolled users using Euclidean distance
5. Multi-frame confirmation prevents false positives
6. Access decisions are logged to SQLite in real time
7. Unknown faces trigger intruder image capture + Telegram/email alerts (with cooldown)
8. Flask dashboard serves live metrics via Server-Sent Events

## PRD Deliverables Status

| Deliverable                         | Status                                    |
| ----------------------------------- | ----------------------------------------- |
| Modular face engine                 | Done — `modules/face_engine.py`           |
| Enrollment CLI                      | Done — `enroll.py`                        |
| Camera loop with live recognition   | Done — `modules/camera.py`, `main.py`     |
| Multi-frame confirmation + cooldown | Done — `modules/access_control.py`        |
| SQLite logging                      | Done — `modules/database.py`              |
| Intruder image capture              | Done — saved to `intruders/`              |
| Telegram alerts                     | Done — `modules/alert.py`                 |
| Email alert fallback                | Done — `modules/alert.py` via SMTP        |
| Flask web dashboard                 | Done — `web/app.py`, `web/auth.py`        |
| Dashboard SSE live updates          | Done — `/dashboard/stream` endpoint       |
| Login rate limiting                 | Done — IP-based, 5 attempts / 5 min       |
| Camera disconnect recovery          | Done — auto-reconnect after 10 failures   |
| Unit tests (UT-01 to UT-06)         | Done — `test_modules.py`                  |
| Integration tests (IT-01 to IT-04)  | Done — `test_integration.py`              |
| Configuration via .env              | Done — `config.py`, `.env.example`        |
| Demo screenshot                     | Done — `artifacts/facegate-dashboard.png` |

## Troubleshooting

**`face_recognition_models` import warning about `pkg_resources`:**
This is a known cosmetic warning from the `face-recognition` package. Pin `setuptools<81` in your venv to suppress it. Does not affect functionality.

**Camera opens but shows black frames:**
Check that no other application is using the camera. Try changing `CAMERA_INDEX` in `.env` (0 = built-in, 1 = external USB).

**`dlib` fails to install on Windows:**
Use `dlib-bin` instead: `pip install dlib-bin face-recognition --no-deps`. The project venv is pre-configured this way.

**Dashboard says "Too many failed attempts":**
The rate limiter fired. Wait 5 minutes or restart the Flask server to clear the in-memory counter.

**No Telegram alerts received:**
Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`. Check `alerts.log` for error details. Ensure you've sent at least one message to the bot on Telegram first.

## Notes

- `face-recognition` depends on dlib internally for embeddings and matching
- Telegram and email alerts are dispatched asynchronously in daemon threads — they never block the recognition loop
- The dashboard uses Server-Sent Events (SSE) for live updates — no page refresh needed
- Alert cooldowns prevent spam: 60s between Telegram alerts, per-user cooldown for access logs
- Adding a new authorized user requires only running `enroll.py` — no code changes needed
