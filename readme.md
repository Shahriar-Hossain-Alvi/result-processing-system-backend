# 🌟 Result Processing System

This project generates student results. It uses **FastAPI** for the backend, **Docker** for containerization, **PostgreSQL** for the database and **Alembic** for database migrations.  
It fully supports development using Docker with hot reload.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Docker** or **Docker Desktop**
- **Python 3.12** (this version is needed to suppress pylance and vscode warnings)
- **Git**

> Python is not used to run the backend — it's only needed so VSCode can provide IntelliSense and suppress import warnings.

---

# How to run this project

## 1. Clone this repository
```
git clone [repository-url]
cd [project-folder]
```

## 2. Create a `.env` 
Copy `.env.example` -> `.env` and fill in the required values

---

## 3. Optional but Recommended: Create a Virtual Environment

This is ONLY for editor (VSCode) dependencies — Docker does not use this venv. 
```
python -m venv venv     # for windows latest/default python
py -3.12 -m venv venv   # version specific venv for windows
python3 -m venv venv    # for linux
```

- Activate:
```
venv\Scripts\activate       # for windows
source venv/bin/activate    # for linux
```

- Install dependencies locally(for editor only):
```
pip install -r requirements.txt
```

---

# 🐳 Run the Backend with Docker

## 4. Development Mode (hot reload)

Build and run the docker containers (make sure you are inside the backend project folder)
```
docker compose -f docker-compose.dev.yml up --build
```

## 5. Production Mode
```
docker compose -f docker-compose.prod.yml up --build -d
```

---

## 6. 📂 Database Migrations (Alembic)

### 1️⃣ When you modify the models:
Generate migration (Locally in project folder):
```
alembic revision --autogenerate -m "message"
```

### 2️⃣ Apply migrations locally:
```
alembic upgrade head
```

### 3️⃣ Apply migrations inside Docker (dev container):
- Generate Migrations inside Docker container (if local migration fails):
```
docker exec -it edutrack_backend_dev alembic revision --autogenerate -m "message"  
```

- Apply Migrations 
> Note: Also use this the first time you run the dev mode container(**step 4**). Because the database will be empty.
```
docker exec -it edutrack_backend_dev alembic upgrade head
```

- Run seed_admin to create initial admin in database inside Docker
```
docker exec -it edutrack_backend_dev python app/db/seed_admin.py

if the previous command fails then run the following:

docker exec -it edutrack_backend_dev /bin/bash -c "PYTHONPATH=/app python app/db/seed_admin.py"
```

--- 

## 7. 🛑 Stopping Docker
```
docker compose -f docker-compose.dev.yml down       # keeps DB data: 

docker compose -f docker-compose.dev.yml down -v    # Deletes DB data: 

ctrl+c # If docker is running in the terminal 
```

# Updating Dependencies

Whenever you add/remove/upgrade Python dependencies:
```
pip install package-name
pip freeze > requirements.txt
```

### ⚠️ Then **rebuild Docker image**:
```
docker compose -f docker-compose.dev.yml up --build
```

---


# API Endpoints
- Backend API: http://localhost:8000
- Swagger UI(Docs): http://localhost:8000/docs
- PostgreSQL data persists inside Docker volume: `postgres_data`
