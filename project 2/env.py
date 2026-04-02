import random
import yaml
from typing import Tuple, Dict, Any
from datetime import datetime, timedelta
from models import (
    Observation, Action, Reward, Medication, PatientProfile, EnvironmentState
)

class HealthEnv:
    """
    OpenEnv-compliant Health Simulation Environment.
    """
    def __init__(self, config_path: str = "openenv.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.tasks = {t['id']: t for t in self.config['tasks']}
        self.current_task = None
        self.internal_state = None
        self.reset()

    def reset(self, task_id: str = "easy") -> Observation:
        if task_id not in self.tasks:
            task_id = "easy"
        
        task_cfg = self.tasks[task_id]
        self.current_task = task_cfg
        
        # Initialize Patient Profile (Deterministic based on task for reproducibility)
        # But we can add stochasticity in habits
        profile = PatientProfile(
            name="John Doe" if task_id == "easy" else "Jane Smith",
            age=30 if task_id == "easy" else 65,
            conditions=["None"] if task_id == "easy" else ["Hypertension", "Type 2 Diabetes"],
            habits=["Regular sleep"] if task_id == "easy" else ["Forgetful", "Coffee lover"]
        )

        # Initialize Medications
        meds = [
            Medication(**m) for m in task_cfg['medications']
        ]

        # Initial Observation
        obs = Observation(
            current_time_h=6, # Day starts at 6 AM
            medicines=meds,
            stress_level=task_cfg.get('initial_stress', 2.0),
            emergency_status=False,
            upcoming_checkup="2026-05-01",
            patient_profile=profile,
            last_action_info="Environment Reset."
        )

        self.internal_state = EnvironmentState(
            env_id="health-sim-v1",
            task_level=task_id,
            step_count=0,
            max_steps=task_cfg['max_steps'],
            total_reward=0.0,
            observation=obs,
            history=[]
        )

        return obs

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        if not self.internal_state:
            raise Exception("Environment not reset.")

        self.internal_state.step_count += 1
        obs = self.internal_state.observation
        
        # Advance time (1 hour per step)
        obs.current_time_h = (obs.current_time_h + 1) % 24
        
        reward_val = 0.0
        reason = ""

        # 1. Action Logic
        if action.action_type == 'handle_emergency':
            if obs.emergency_status:
                obs.emergency_status = False
                reward_val += 20.0
                reason = "Emergency resolved! Critical intervention successful."
            else:
                reward_val -= 5.0
                reason = "False alarm. Resources wasted on non-emergency."

        elif action.action_type == 'remind_medicine':
            found_med = False
            for med in obs.medicines:
                if med.id == action.med_id:
                    found_med = True
                    # Tolerance: +/- 1 hour
                    if not med.taken and not med.is_missed:
                        time_diff = abs(med.time_24h - obs.current_time_h)
                        if time_diff <= 1:
                            med.taken = True
                            reward_val += 15.0
                            reason = f"Medication {med.name} taken on time."
                        else:
                            reward_val += 2.0 # Partial reward for late but not missed
                            med.taken = True
                            reason = f"Medication {med.name} taken, but outside optimal window."
                    else:
                        reward_val -= 2.0
                        reason = f"Medication {med.name} already processed."
            if not found_med:
                reward_val -= 5.0
                reason = "Attempted to remind non-existent medication."

        elif action.action_type == 'reduce_stress':
            if obs.stress_level > 7.0:
                obs.stress_level = max(0.0, obs.stress_level - 3.0)
                reward_val += 10.0
                reason = "High stress effectively managed."
            else:
                obs.stress_level = max(0.0, obs.stress_level - 1.0)
                reward_val += 2.0
                reason = "Routine stress reduction performed."

        elif action.action_type == 'schedule_checkup':
            obs.upcoming_checkup = (datetime.now() + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d')
            reward_val += 5.0
            reason = "Preventative checkup scheduled."

        elif action.action_type == 'skip':
            reward_val -= 0.5
            reason = "No action taken."

        # 2. Stochastic Evolution (Human Unpredictability)
        # Random stress increase
        stress_inc = random.uniform(0, 0.5)
        if obs.stress_level > 8.0: # Stress compounding
            stress_inc += random.uniform(0, 1.0)
        obs.stress_level = min(10.0, obs.stress_level + stress_inc)

        # Random Emergency (more likely if stress is high)
        emergency_prob = 0.02 + (obs.stress_level / 100.0)
        if random.random() < emergency_prob and not obs.emergency_status:
            obs.emergency_status = True
            reason += " | ALERT: Stress-induced health emergency!"

        # Check for missed meds
        for med in obs.medicines:
            if not med.taken and not med.is_missed:
                if obs.current_time_h > med.time_24h + 1:
                    med.is_missed = True
                    reward_val -= 20.0
                    reason += f" | CRITICAL: Missed {med.name}!"

        # Update Observation
        obs.last_action_info = reason
        self.internal_state.total_reward += reward_val
        
        # Check termination
        done = self.internal_state.step_count >= self.internal_state.max_steps
        
        # Log to history
        self.internal_state.history.append({
            'step': self.internal_state.step_count,
            'action': action.dict(),
            'reward': reward_val,
            'info': reason
        })

        reward = Reward(value=reward_val, reason=reason)
        return obs, reward, done, {"total_reward": self.internal_state.total_reward}

    def state(self) -> EnvironmentState:
        return self.internal_state
