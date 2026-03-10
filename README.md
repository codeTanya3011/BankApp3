# 🌟 Credits & Plans Analytics System 🚀

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-05998b.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791.svg)
![Docker](https://img.shields.io/badge/Docker-enabled-2496ed.svg)

An intelligent financial system for credit data management and performance analytics. This project automates bank data processing,
calculates plan execution efficiency, and provides deep user-level insights.

---

## 🌐 Live Demo & Testing
The application is deployed and available for interactive testing:
🔗 **[Interactive App Documentation (Swagger)](https://tanya-dev.help/docs)**

### 💡 Quick Sandbox Guide:
To see the system in action without uploading your own files, use these predefined ranges:

1. **`GET /user_credits/{user_id}`**: 
   * Use IDs between **`1`** and **`4000`** (e.g., `123` or `288`).

2. **`GET /plans/performance`** (Monthly): 
   * Use dates between **`2020-01-01`** and **`2022-07-01`** for actual data.

3. **`GET /plans/year_performance`** (Annual): 
   * **Data Range:** Active plans are available for **2020, 2021, and 2022**.
   * **Future Dates:** You can test years like **2025** or **2026** — the system will process the request correctly and
   * return `0` values, demonstrating stable logic even without records.

**How to test:** Click **"Try it out"** ➡️ Enter the value ➡️ Click **"Execute"**.

---

## ✨ Key Features

* 📥 **Smart Import:** Seamless data loading from `CSV` and `Excel` using Pandas with automated validation.
* 📊 **Performance Analytics:** Real-time calculation of plan execution (Issuance, Collection, Percentages).
* 🔍 **Credit Tracker:** Comprehensive history for each `user_id` including body, interest, and overdue status.
* 🛡️ **Advanced Exception Handling:** Custom error hierarchy (`AppException`, `IntegrityError`) for clear API responses.
* 🚀 **Docker Ready:** Fully containerized environment for instant deployment.

---

## 🛠 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | **FastAPI** (Asynchronous) |
| **Database** | **PostgreSQL** |
| **ORM** | **SQLAlchemy 2.0** (Async) |
| **Data Science** | **Pandas** (ETL processes) |
| **Testing** | **Pytest** (Asyncio) |
| **Infrastructure** | **Docker / Docker Compose** |

---

## ⚡ Quick Start (Local Development)

### 1️⃣ Deployment
Ensure you have Docker installed, then run:

docker-compose up -d --build

2️⃣ Database Initialization
Once the containers are running, navigate to http://127.0.0.1:8000/docs and execute the setup endpoint to prepopulate your database:

HTTP
POST /plans/setup-database
✨ Pro Tip: This command automatically creates all necessary SQL tables and migrates initial data from the documents/ folder.
You only need to run this once.

3️⃣ Running Tests
To verify system stability and ensure all endpoints are working as expected within the Docker environment, use this command:
docker-compose exec app pytest -v

---

### 📋 API Reference

## 📈 Plans & Performance

1. GET /plans/performance — Monthly efficiency calculation (compares planned vs actual data).

2. GET /plans/year_performance — Annual analytics broken down by month with summary totals.

3. POST /plans/insert — Manual upload for new plan files (.csv or .xlsx).

---

## 👤 User Credits
GET /user_credits/{user_id} — Client detailed card: includes all credits, payment history, and overdue tracking.

---

## 🛡️ Error Handling
The project implements a robust custom exception hierarchy to ensure the API always returns clear and actionable responses:

NotFoundUserError (404) — Triggered when a requested user ID does not exist in the database.

AppException (400/409) — Handles business logic conflicts, such as attempting to create duplicate plans for the same period or invalid file formats.

IntegrityError — Automatic database-level protection that ensures data consistency and prevents duplicate primary keys.
