# This Dockerfile is for production mode
# 1. Base Image: Start from an official, lightweight Python image - it includes Python 3.12 and necessary OS components. Docker downloads the image only once
FROM python:3.12-slim

# 2. Create a virtual environment inside container (optional but clean)
ENV VENV_PATH="/opt/venv"
RUN python -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# 3. Working Directory: Everything inside the container happens from /app
WORKDIR /app


# 4. Install OS-level dependencies for PostgreSQL & others(psycopg/argon2/bcrypt)
RUN apt-get update && apt-get install -y \
 build-essential \
 libpq-dev \
 && rm -rf /var/lib/apt/lists/*


# 5. Install Python dependencies inside the container
# --no-cache-dir reduces the image size
# -r installs all packages listed in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# 6. Copy the entire project (except the files in .dockerignore)
# The first '.' is the source (your local project root, defined by the build context)
# The second '.' is the destination (/app, the WORKDIR inside the container)
COPY . .


# 7. Expose Port: Inform Docker which port the container will listen on (FastAPI default is 8000)
EXPOSE 8000


# 8. FastAPI Server Start Command: Define the command to run when the container starts
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# TODO: --reload flag for uvicorn? gunicorn?

# 1. Ths command works in local
# CMD bash -c "alembic upgrade head && python app/db/seed_admin.py && uvicorn app.main:app --host 0.0.0.0 --port 8000" 

# 2. The below commmand faild to start backend in Render. ModuleNotFoundError: No module named 'app' This happens because when you run python app/db/seed_admin.py, Python looks for a folder named app inside the folder where the script lives. It can't find it because app is the parent directory.
# CMD bash -c "alembic upgrade head && python app/db/seed_admin.py && gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000"

# 3. The below commad needs pre-deploy command for alembic in Render to work. But its paid plan so no free tier
# CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]

# 4. The below command works in Render
CMD bash -c "alembic upgrade head && PYTHONPATH=. python app/db/seed_admin.py && gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000"