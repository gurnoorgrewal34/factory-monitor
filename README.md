## Run with Python

Create and activate virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start API:

```powershell
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

or:

```powershell
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

## Run Directly Without API

Multi-camera test:

```powershell
python test_multi_camera.py
```

Original single-camera application:

```powershell
python app/main.py
```

---

## Camera Configuration

Camera configuration is stored in:

```text
config/cameras.json
```

Example:

```json
{
  "id": "cam_01",
  "name": "Camera 1",
  "enabled": true,
  "source_type": "video",
  "video_path": "datasets/raw_videos/test.mp4",
  "zones_file": "zones/zones.json",
  "modules": ["fire", "smoke"],
  "save_output": true
}
```

Sources supported:

```text
video
webcam
cctv
```

---

## Run All Modules

Use:

```json
{
  "modules": ["all"]
}
```

---

## Run Specific Modules

Fire + Smoke:

```json
{
  "modules": ["fire", "smoke"]
}
```

Running + Pose:

```json
{
  "modules": ["running", "pose"]
}
```

Smoking only:

```json
{
  "modules": ["smoking"]
}
```

---

## Main API Endpoints

```text
GET  /health

GET  /cameras

GET  /cameras/{camera_id}

POST /cameras/{camera_id}/start

POST /cameras/{camera_id}/stop

PUT  /cameras/{camera_id}/modules

GET  /cameras/{camera_id}/stream
```

To change modules:

```text
STOP CAMERA
    ↓
UPDATE MODULES
    ↓
START CAMERA
```

---

## Processed Video

Camera 1:

```text
http://127.0.0.1:8000/cameras/cam_01/stream
```

Camera 2:

```text
http://127.0.0.1:8000/cameras/cam_02/stream
```

---

## WebSocket Alerts

```text
ws://127.0.0.1:8000/ws/alerts
```

One WebSocket receives alerts from all cameras.

Example:

```json
{
  "camera_id": "cam_01",
  "event": "alert",
  "data": {
    "type": "Fire",
    "severity": "CRITICAL"
  }
}
```

---

## Quick Test

1. Open `/docs`
2. Run `GET /health`
3. Run `GET /cameras`
4. Select modules
5. Start camera
6. Check `frames_processed`
7. Open `/stream`
8. Connect WebSocket
9. Verify alerts
10. Stop camera

If:

```text
running = true
frames_processed > 0
last_error = null
```

the camera pipeline is working.

---

## Git Branch

```text
performance-optimization
```

## Version

```text
Factory Monitoring API v1.0.0
Docker: gurnoor13/factory-monitor-api:v1
```