# FaceGate

FaceGate is a smart face-recognition access control system built from `FaceGate_PRD.md`.
It supports enrollment, live webcam recognition, SQLite logging, intruder image capture, Telegram alerts, and a Flask dashboard.

## Stack

- Python 3.x
- OpenCV
- face-recognition / dlib
- Flask
- SQLite
- python-dotenv
- requests

## Project Layout

The repository follows the PRD structure:

```text
main.py
enroll.py
config.py
requirements.txt
.env.example
.gitignore
modules/
web/
data/
intruders/
artifacts/
test_modules.py
```

Runtime files such as `.env`, `data/*.db`, `data/*.pkl`, `intruders/*.jpg`, `alerts.log`, and local build outputs are ignored by git.

## Environment

Create and activate the project venv:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

The requirements file is intentionally unpinned. On Windows, the repo venv uses `dlib-bin` and `face-recognition --no-deps` so the stack works without compiling dlib from source.

## Configuration

Copy `.env.example` to `.env` and fill the values.

Required keys:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
FLASK_SECRET_KEY=
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=
```

The current local admin login is:

```text
Username: admin
Password: hrfPM!liSorANzyJ5j
```

Generate a Flask secret key:

```powershell
py -3.11 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Generate an admin password hash:

```powershell
py -3.11 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

Store only the hash in `.env`, never the plain password.

## Core Commands

Enroll a user from the webcam:

```powershell
python enroll.py "User Name" --samples 1
```

Run live recognition from the webcam:

```powershell
python main.py
```

Run the Flask dashboard:

```powershell
python -m web.app
```

Open:

```text
http://127.0.0.1:5000/login
```

Dashboard routes:

- `/dashboard` - summary cards and camera controls
- `/logs` - paginated access logs
- `/logs/filter?format=json` - JSON filtered logs
- `/intruders` - protected intruder gallery
- `/start` - start background recognition
- `/stop` - stop background recognition
- `/status` - camera state JSON

## PRD Deliverables

Completed deliverables:

- Modular face engine in `modules/face_engine.py`
- Enrollment CLI in `enroll.py`
- Camera loop in `modules/camera.py` and `main.py`
- Access confirmation and cooldown in `modules/access_control.py`
- SQLite persistence in `modules/database.py`
- Intruder image capture in `intruders/`
- Telegram alert manager in `modules/alert.py`
- Flask dashboard in `web/app.py` and `web/auth.py`
- Test suite in `test_modules.py`
- Seeded SQLite database with 10 sample log entries
- Dashboard screenshot artifact at `artifacts/facegate-dashboard.png`

## Verification

Run the module tests:

```powershell
python -m unittest test_modules.py
```

Run a syntax check:

```powershell
python -m py_compile config.py enroll.py main.py modules\face_engine.py modules\access_control.py modules\database.py modules\alert.py modules\camera.py web\app.py web\auth.py test_modules.py
```

Check the seeded database:

```powershell
python -c "from modules.database import get_logs; print(len(get_logs(limit=20, offset=0, filters={})))"
```

## Demo Artifact

Dashboard screenshot:

- [artifacts/facegate-dashboard.png](artifacts/facegate-dashboard.png)

## Notes

- `face-recognition` still depends on dlib internally for embeddings and matching.
- `setuptools<81` is pinned in the repo venv because `face_recognition_models` still imports `pkg_resources`.
- Telegram alerts require `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`.

