from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class PatientProfile(BaseModel):
    name: str = "Anonymous Patient"
    age: int = 45
    conditions: List[str] = ["Hypertension"]
    stress_threshold: float = 7.0
    habits: List[str] = ["Morning coffee", "Late sleeper"]

class Medication(BaseModel):
    id: int
    name: str
    time_24h: int
    taken: bool = False
    is_missed: bool = False

class Observation(BaseModel):
    current_time_h: int
    medicines: List[Medication]
    stress_level: float
    emergency_status: bool
    upcoming_checkup: Optional[str]
    patient_profile: PatientProfile
    last_action_info: str

class Action(BaseModel):
    action_type: str # 'remind_medicine', 'reduce_stress', 'handle_emergency', 'schedule_checkup', 'skip'
    med_id: Optional[int] = None

class Reward(BaseModel):
    value: float
    reason: str

class EnvironmentState(BaseModel):
    env_id: str
    task_level: str
    step_count: int
    max_steps: int
    total_reward: float
    history: List[dict] = []
    observation: Observation
