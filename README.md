# CareConnect 🩺

**CareConnect** is a Django-based web platform connecting patients with healthcare practitioners (doctors and psychologists), featuring online appointment booking, AI-powered practitioner search by symptoms (Gemini), and geolocation.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Teleconsultation (Jitsi Meet)](#teleconsultation-jitsi-meet)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Author](#author)

---

## Features

**Patient**
- Sign up / log in with email verification (verification code)
- Search for practitioners based on described symptoms (analyzed via the Gemini API) to suggest the appropriate specialty
- Sort practitioners by proximity (GPS distance, Haversine formula)
- Book appointments (in-office or teleconsultation)
- Track appointments, request rescheduling
- Leave a review (rating + comment) after a consultation
- Personal account space

**Doctor**
- Sign up / log in with email verification
- Dashboard: calendar, statistics, today's appointments
- Appointment management (create, edit, delete, confirm/decline)
- Patient record (symptoms, diagnosis, notes, prescription)
- Request / respond to rescheduling proposals
- Email notifications
- Profile and practice location

**Psychologist**
- Same features as the doctor role (sign-up, dashboard, appointments, profile)
- Upload of supporting documents during registration

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 5.2 |
| **Database** | SQLite (default) |
| **AI** | Google Generative AI (Gemini) — symptom analysis to route patients to the right specialty |
| **Image processing** | Pillow |
| **Video conferencing** | Jitsi Meet (public instance `meet.jit.si`) — for teleconsultations |
| **Frontend** | Django templates (HTML/CSS/JS) |

---

## Teleconsultation (Jitsi Meet)

Appointments of type *teleconsultation* use [Jitsi Meet](https://meet.jit.si), a free video conferencing solution that requires no account creation:

- Each appointment generates a unique room: `https://meet.jit.si/CareConnect-RDV-<appointment_id>`
- Patient and practitioner automatically join the same room based on the appointment ID
- The "Join teleconsultation" button is only visible when the appointment is **confirmed** and the current time falls between **10 minutes before** and **60 minutes after** the scheduled time
- ⚠️ The room link is predictable (based on the appointment ID) and the public Jitsi instance requires no authentication — this should be secured (e.g. a random token per appointment) before any production use involving real health data.

---

## Project Structure

```
care/
├── config/          # Django project settings (settings, urls, wsgi/asgi)
├── users/           # Patient, doctor and psychologist accounts (registration, auth, profiles)
├── appointments/    # Appointment management, reviews, emails
├── recherche/       # Practitioner search (AI + geolocation)
├── fichiers/        # Uploaded files (psychologist credentials, etc.)
├── manage.py
└── requirements.txt
```

---

## Installation

1. **Clone the project and enter the folder**
   ```bash
   git clone <repo-url>
   cd care
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux / Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file at the root of the `care/` folder with:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   ```

5. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

6. **Run the server**
   ```bash
   python manage.py runserver
   ```

   The application is available at `http://127.0.0.1:8000/`

---

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | API key for symptom analysis via Google Gemini |

---

## Author

Project developed by **Nour Yahya** and **Roua Tbarki** — 4th-year Data Science & AI Engineering students, TEK-UP University.
