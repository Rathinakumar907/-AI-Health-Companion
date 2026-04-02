import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from env import HealthEnv
from models import Action, Observation, Reward, EnvironmentState
from grader import HealthGrader
from baseline_agent import BaselineAgent

# Initialize FastAPI app
app = FastAPI(title="AI Health Companion - OpenEnv", version="1.0.0")

# Core Environment Instance
env = HealthEnv()
agent = BaselineAgent()
grader = HealthGrader()

# --- OpenEnv Standard Endpoints ---

@app.post("/reset", response_model=Observation)
async def reset_env(payload: Dict[str, str] = None):
    task_id = payload.get("task_id", "easy") if payload else "easy"
    return env.reset(task_id=task_id)

@app.post("/step")
async def process_step(action: Action):
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs,
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/state", response_model=EnvironmentState)
async def get_state():
    return env.state()

@app.post("/grade")
async def grade_episode():
    state = env.state()
    return grader.grade(state)

# --- Agent Assistance Endpoints ---

@app.get("/suggestion", response_model=Action)
async def get_suggestion():
    obs = env.state().observation
    return agent.select_action(obs)

# --- Static File Serving (UI) ---

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse("index.html")

# Mount static files (JS, CSS)
app.mount("/", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
