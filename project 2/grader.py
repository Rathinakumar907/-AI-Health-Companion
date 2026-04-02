from typing import List, Dict, Any
from models import EnvironmentState

class HealthGrader:
    """
    Deterministic Grader for the AI Health Companion.
    Evaluates agent performance based on state history and episode outcomes.
    """
    @staticmethod
    def grade(state: EnvironmentState) -> Dict[str, Any]:
        """
        Calculates a score from 0.0 to 1.0 based on adherence, stress, and emergency handling.
        """
        obs = state.observation
        history = [h for h in state.history if h['step'] > 0]
        
        # 1. Adherence Score (Weight: 40%)
        total_meds = len(obs.medicines)
        taken_meds = sum(1 for m in obs.medicines if m.taken and not m.is_missed)
        adherence_score = (taken_meds / total_meds) if total_meds > 0 else 1.0
        
        # 2. Stress Management Score (Weight: 20%)
        # Penalize if average stress > 7.0
        avg_stress = sum(h.get('stress_level', obs.stress_level) for h in history) / len(history) if history else obs.stress_level
        stress_score = max(0.0, 1.0 - (avg_stress / 10.0))
        
        # 3. Emergency Handling Score (Weight: 30%)
        # Track emergencies in history vs actions
        total_emergencies = 0
        handled_emergencies = 0
        for h in history:
            if "ALERT: Health Emergency" in h['info']:
                total_emergencies += 1
            if h['action']['action_type'] == 'handle_emergency' and "handled successfully" in h['info'].lower():
                handled_emergencies += 1
        
        emergency_score = (handled_emergencies / total_emergencies) if total_emergencies > 0 else 1.0
        
        # 4. Efficiency Score (Weight: 10%)
        # Penalize for skips and false alarms
        skips = sum(1 for h in history if h['action']['action_type'] == 'skip')
        efficiency_score = max(0.0, 1.0 - (skips / state.max_steps))
        
        # Final Weighted Score
        final_score = (
            (adherence_score * 0.4) +
            (stress_score * 0.2) +
            (emergency_score * 0.3) +
            (efficiency_score * 0.1)
        )
        
        return {
            'score': round(float(final_score), 3),
            'metrics': {
                'adherence_rate': adherence_score,
                'avg_stress': round(float(avg_stress), 2),
                'emergency_response_rate': emergency_score,
                'efficiency': efficiency_score
            },
            'summary': f"Final Grade: {round(final_score * 100, 1)}% | Adherence: {int(adherence_score * 100)}% | Response: {int(emergency_score * 100)}%"
        }
