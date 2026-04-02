import os
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from env import HealthEnv
from models import Action, Observation, Reward, EnvironmentState
from grader import HealthGrader
from baseline_agent import BaselineAgent
from database import init_db, get_db, User, pwd_context
from auth import create_access_token, get_current_user

# Initialize Database
init_db()

# Initialize FastAPI app
app = FastAPI(title="AI Health Companion - OpenEnv", version="1.0.0")

# Core Environment Instance
env = HealthEnv()
agent = BaselineAgent()
grader = HealthGrader()

# --- Authentication Models ---

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

# --- Authentication Endpoints ---

@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }

@app.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user

# --- OpenEnv Standard Endpoints (PROTECTED) ---

@app.post("/reset", response_model=Observation)
async def reset_env(payload: Dict[str, str] = None, user: dict = Depends(get_current_user)):
    task_id = payload.get("task_id", "easy") if payload else "easy"
    return env.reset(task_id=task_id)

@app.post("/step")
async def process_step(action: Action, user: dict = Depends(get_current_user)):
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs,
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/state", response_model=EnvironmentState)
async def get_state(user: dict = Depends(get_current_user)):
    return env.state()

@app.post("/grade")
async def grade_episode(user: dict = Depends(get_current_user)):
    state = env.state()
    return grader.grade(state)

# --- Agent Assistance Endpoints ---

@app.get("/suggestion", response_model=Action)
async def get_suggestion(user: dict = Depends(get_current_user)):
    obs = env.state().observation
    return agent.select_action(obs)

# --- Static File Serving (UI) ---

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return RedirectResponse(url="/login.html")

@app.get("/login.html", response_class=HTMLResponse)
async def get_login_page():
    return FileResponse("login.html")

@app.get("/student_dashboard.html", response_class=HTMLResponse)
async def get_student_dashboard():
    return FileResponse("student_dashboard.html")

@app.get("/professor_dashboard.html", response_class=HTMLResponse)
async def get_professor_dashboard():
    return FileResponse("professor_dashboard.html")

# Mount static files (JS, CSS) - Keep last to avoid over-matching
app.mount("/", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    import uvicorn
    # Start on port 5000 as requested or maintain existing
    uvicorn.run(app, host="0.0.0.0", port=5000)
