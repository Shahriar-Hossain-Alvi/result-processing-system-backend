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

# IF using alembic migrations then use the following command => On Render, you can set a "Pre-deploy Command." Move alembic upgrade head there so it runs once before the new version of your app goes live
# CMD bash -c "alembic upgrade head && python app/db/seed_admin.py && uvicorn app.main:app --host 0.0.0.0 --port 8000" 

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]