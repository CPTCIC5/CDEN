from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from utils.auth import SECRET_KEY
from routers import users, founders, mentors, funding, admin, events, newsletter, cohort
from db.models import engine, Base
from db.admin import setup_admin

import os
import sqladmin
import shutil
from fastapi.staticfiles import StaticFiles
from pathlib import Path



app= FastAPI()

# Add SessionMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="session_cookie",
    max_age=1800000000000  # 30 minutes in seconds
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#app.add_middleware(HTTPSRedirectMiddleware)

static_path = Path("static")
static_path.mkdir(exist_ok=True)

# Path to sqladmin's statics directory
sqladmin_static_path = os.path.join(os.path.dirname(sqladmin.__file__), "statics")

# Copy files from sqladmin/statics to your static/ dir
for item in os.listdir(sqladmin_static_path):
    src = os.path.join(sqladmin_static_path, item)
    dest = os.path.join(static_path, item)
    if os.path.isdir(src):
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dest)

# Mount your static directory
app.mount("/static", StaticFiles(directory="static"), name="static")


# Schema is managed by Alembic migrations (run: alembic upgrade head)


# Include routers
app.include_router(users.router)
app.include_router(founders.router)
app.include_router(mentors.router)
app.include_router(funding.router)
app.include_router(events.router)
app.include_router(admin.router)
app.include_router(newsletter.router)
app.include_router(cohort.router)

# Mount the SQLAdmin back-office at /admin
setup_admin(app, engine)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000, host="0.0.0.0")