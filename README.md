# RescueNet Backend

RescueNet is a full-stack AI-assisted Stray Animal Welfare Management Platform connecting citizens, municipal officers, NGOs, and volunteers.

This is the FastAPI backend repository. It powers the REST API, integrates the AI models, handles geospatial PostGIS queries, and manages all business logic.

## Architecture & Tech Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with PostGIS extension (for geospatial indexing and nearest-neighbor routing)
- **ORM**: SQLAlchemy + GeoAlchemy2
- **Auth**: JWT-based Role-Based Access Control (RBAC)
- **AI Integration**: RF-DETR (animal detection), Multimodal VLMs (video verification), FFT/CLIP/EXIF checks (photo authenticity).

## Setup & Running Locally

1. **Install Dependencies**
   Make sure you have Python 3.9+ installed.
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup**
   You need a PostgreSQL database with the PostGIS extension installed.
   Set up your environment variables or modify `app/core/config.py`:
   - `POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
   
   Execute the `rescuenet_schema.md` SQL snippet in your database to create the required tables and enums.

3. **Seed Initial Data**
   Run the seed script to load dummy users, zones, and an initial complaint for the frontend to test against.
   ```bash
   python seed.py
   ```

4. **Run the Server**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Contract (Swagger / OpenAPI)

Once the server is running, the **Interactive API Contract** is available at:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

The frontend team should rely on this automatically generated Swagger UI. It defines every endpoint, request/response schema, authentication requirement, and returns mock/real responses.

## "SIMPLIFIED" Implementations (For Future Extension)

To ensure the backend runs seamlessly on local dev environments without requiring heavy GPUs or paid API keys, the following components are currently marked as `SIMPLIFIED`:

1. **RF-DETR & Zero-Shot Detectors (`app/services/ai_detector.py`)**
   - *Currently*: Uses lightweight keyword/mock logic to simulate bounding boxes and confidences.
   - *Full Version*: Drop in the `ultralytics` or `transformers` model inference code directly in `detect_animal()`.

2. **Photo Authenticity (FFT, CLIP, EXIF) (`app/services/ai_detector.py`)**
   - *Currently*: Returns high mock scores that pass the consensus threshold.
   - *Full Version*: Needs real EXIF parsing (`Pillow`/`exifread`), Fourier Transform artifacts check, and CLIP embedding comparisons.

3. **Live Video Verification (`app/api/routes/video.py`)**
   - *Currently*: Uses a single-shot photo comparison fallback (comparing embeddings) instead of handling continuous video streaming due to quota/latency constraints. 
   - *Full Version*: Open a WebSocket, stream frames, and ping Gemini Live API or a similar vision-language model.

4. **PostGIS Nearest Neighbor Routing (`app/api/routes/complaints.py`)**
   - *Currently*: Selects the first officer/NGO in the database.
   - *Full Version*: Execute `ORDER BY location <-> ST_GeomFromText(wkt)` to find the precise geographically closest active officer.

5. **Notifications (`app/api/routes/notifications.py`)**
   - *Currently*: In-app notifications are saved to the DB. Email/Push are abstracted behind print statements.
   - *Full Version*: Integrate SMTP for emails and Firebase Admin SDK / Twilio for push/SMS.
