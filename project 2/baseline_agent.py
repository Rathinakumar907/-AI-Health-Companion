import time
import uuid
from typing import Optional
from env import HealthEnv
from models import Observation, Action
from grader import HealthGrader

class BaselineAgent:
    """
    Baseline AI Agent for the Health Companion environment.
    Uses a priority-based deterministic policy for reproducible testing.
    """
    def __init__(self, agent_name: str = "HealthAI-Baseline"):
        self.agent_name = agent_name
        self.episode_id = str(uuid.uuid4())[:8]

    def select_action(self, obs: Observation) -> Action:
        """
        Policy: Emergency > Medication > Stress > Routine
        """
        # 1. Critical: Emergency
        if obs.emergency_status:
            return Action(action_type='handle_emergency')

        # 2. Timely: Medication
        # Check for due meds (within +/- 1 hour)
        for med in obs.medicines:
            if not med.taken and not med.is_missed:
                # Agent knows the scheduled time and current time
                time_diff = abs(med.time_24h - obs.current_time_h)
                if time_diff <= 1:
                    return Action(action_type='remind_medicine', med_id=med.id)

        # 3. Preventative: Stress
        if obs.stress_level > 6.0:
            return Action(action_type='reduce_stress')

        # 4. Routine: Periodic checkups
        # Every 10 steps skip if no urgent meds
        # (This avoids redundant scheduling)
        return Action(action_type='skip')

def run_episode(task_id: str = "medium"):
    env = HealthEnv()
    agent = BaselineAgent()
    grader = HealthGrader()

    print(f"\n{'='*60}")
    print(f"RUNNING BASELINE AGENT | TASK: {task_id.upper()} | EPISODE: {agent.episode_id}")
    print(f"{'='*60}\n")

    obs = env.reset(task_id=task_id)
    done = False
    
    while not done:
        # Agent suggests action
        action = agent.select_action(obs)
        
        # Environment steps
        obs, reward, done, info = env.step(action)
        
        # Log Step
        time_str = f"{obs.current_time_h:02d}:00"
        print(f"Step {env.state().step_count} [{time_str}] | Action: {action.action_type.upper():<15}")
        print(f"  Reward: {reward.value:<5.1f} | Stress: {obs.stress_level:<5.2f} | Emergency: {'YES' if obs.emergency_status else 'NO'}")
        print(f"  Info: {reward.reason}")
        print("-" * 60)
        
        time.sleep(0.05) # Simulated latency

    # Grading
    results = grader.grade(env.state())
    
    print(f"\n{'='*60}")
    print(f"EPISODE COMPLETE | TASK: {task_id.upper()}")
    print(f"SCORE: {results['score']} / 1.0")
    print(f"SUMMARY: {results['summary']}")
    print(f"METRICS: {results['metrics']}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Test across multiple tasks
    run_episode("easy")
    run_episode("medium")
    run_episode("hard")
