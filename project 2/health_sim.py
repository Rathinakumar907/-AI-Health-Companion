import random
import time
from datetime import datetime, timedelta

class ThemeManager:
    """
    Manages the visual theme of the AI Health Companion simulation.
    Supports Light, Dark, and Medical modes.
    """
    def __init__(self):
        self.themes = {
            'light': "[LIGHT MODE]",
            'dark': "[DARK MODE]",
            'medical': "[MEDICAL MODE 🏥]"
        }
        self.current_theme = 'light'

    def change_theme(self, theme_name):
        theme_name = theme_name.strip().lower()
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False

    def get_indicator(self):
        return self.themes[self.current_theme]


class HealthEnv:
    """
    Core Simulation Engine for the AI Health Companion.
    Maintains user health state and handles state transitions based on actions.
    """

    def __init__(self):
        self.state = {}
        self.history = []
        self.current_step = 0
        self.theme_manager = ThemeManager()
        self.reset()

    def reset(self, level='easy'):
        """
        Initializes the health environment state based on difficulty level.
        Levels: 'easy', 'medium', 'hard'
        """
        self.current_step = 0
        self.history = []
        
        # Base state
        self.state = {
            'medicines': [],
            'stress_level': 2,
            'emergency_status': False,
            'upcoming_checkup': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'time_elapsed': 0 # Simulated hours
        }

        if level == 'easy':
            self.state['medicines'] = [{'name': 'Vitamin C', 'time': 8, 'taken': False}]
            self.state['stress_level'] = 1
        elif level == 'medium':
            self.state['medicines'] = [
                {'name': 'Aspirin', 'time': 8, 'taken': False},
                {'name': 'Metformin', 'time': 20, 'taken': False}
            ]
            self.state['stress_level'] = 5
        elif level == 'hard':
            self.state['medicines'] = [
                {'name': 'Lisinopril', 'time': 9, 'taken': False},
                {'name': 'Insulin', 'time': 13, 'taken': False},
                {'name': 'Atorvastatin', 'time': 21, 'taken': False}
            ]
            self.state['stress_level'] = 8
            # Hard mode might start with a random emergency or high stress
            if random.random() > 0.5:
                self.state['emergency_status'] = True

        return self.state

    def step(self, action):
        """
        Updates the state based on the action taken and returns (new_state, reward, done, info).
        Actions: 'remind_medicine', 'reduce_stress', 'handle_emergency', 'schedule_checkup', 'skip'
        """
        reward = 0
        info = ""
        self.current_step += 1
        self.state['time_elapsed'] += 1 # Increment simulated time (1 hour per step)

        # 1. Action Logic & Initial Rewards
        if action == 'handle_emergency':
            if self.state['emergency_status']:
                self.state['emergency_status'] = False
                reward += 15
                info = "Emergency handled successfully!"
            else:
                reward -= 5
                info = "No emergency to handle."

        elif action == 'remind_medicine':
            # Check for due medicines (within +/- 1 hour of scheduled time)
            current_hour = self.state['time_elapsed'] % 24
            found_due = False
            for med in self.state['medicines']:
                if not med['taken'] and abs(med['time'] - current_hour) <= 1:
                    med['taken'] = True
                    reward += 10
                    found_due = True
                    info = f"Reminder sent for {med['name']}. Medicine taken."
            
            if not found_due:
                reward -= 5
                info = "No medicine due at this time."

        elif action == 'reduce_stress':
            if self.state['stress_level'] > 5:
                self.state['stress_level'] = max(0, self.state['stress_level'] - 2)
                reward += 5
                info = "Stress reduced through guided breathing."
            else:
                self.state['stress_level'] = max(0, self.state['stress_level'] - 1)
                reward += 2 # Smaller reward for maintenance
                info = "Stress levels maintained."

        elif action == 'schedule_checkup':
            # Simple simulation: just update the date
            new_date = (datetime.now() + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d')
            self.state['upcoming_checkup'] = new_date
            reward += 2
            info = f"New checkup scheduled for {new_date}."

        elif action == 'skip':
            reward -= 1 # Small penalty for inactivity
            info = "No action taken."

        # 2. Environment Evolution (Uncontrolled factors)
        # Random stress increase
        if random.random() > 0.7:
            self.state['stress_level'] = min(10, self.state['stress_level'] + 1)
        
        # Check for missed medicines (medicine time has passed and not taken)
        current_hour = self.state['time_elapsed'] % 24
        for med in self.state['medicines']:
            if not med['taken'] and current_hour > med['time'] + 1:
                reward -= 10
                info += f" | WARNING: Missed dose of {med['name']}!"
                med['taken'] = True # Assume it's "missed" and move on to avoid repeating penalty

        # Random emergency trigger (rare, higher chance in Hard level)
        if random.random() > 0.95:
            self.state['emergency_status'] = True
            info += " | ALERT: Health Emergency Detected!"

        done = self.current_step >= 20 # Episode ends after 20 steps
        return self.state, reward, done, info

    def get_state(self):
        return self.state

    def change_theme(self, theme_name):
        """
        Dynamically update the simulation theme.
        """
        return self.theme_manager.change_theme(theme_name)

    def get_theme_indicator(self):
        """
        Get the current visual indicator for the theme.
        """
        return self.theme_manager.get_indicator()


class AICompanionAgent:
    """
    Simulated AI Assistant Agent.
    Makes decisions based on the current health state using a rule-based priority system.
    """
    def suggest_action(self, state):
        """
        Determines the best action to take based on the environment state.
        Priority: Emergency > Medicine > Stress > Checkup
        """
        # 1. Critical Priority: Emergencies
        if state['emergency_status']:
            return 'handle_emergency'

        # 2. Medium Priority: Timely Medication
        current_hour = state['time_elapsed'] % 24
        for med in state['medicines']:
            if not med['taken'] and abs(med['time'] - current_hour) <= 1:
                return 'remind_medicine'

        # 3. Health Maintenance: Stress
        if state['stress_level'] > 5:
            return 'reduce_stress'

        # 4. Routine: Checkups
        # Simple logic: avoid redundant checkup scheduling
        if state['current_step'] % 10 == 0:
            return 'schedule_checkup'

        # Default action
        return 'skip'


def run_simulation(level='medium'):
    """
    Runs a full simulation episode and logs results to the console.
    """
    env = HealthEnv()
    agent = AICompanionAgent()
    state = env.reset(level=level)
    total_reward = 0
    
    print(f"\n{'='*50}")
    print(f"Starting AI Health Companion Simulation (Level: {level.upper()})")
    print(f"{'='*50}")
    print(f"Initial State: {state}")
    print("-" * 50)

    done = False
    while not done:
        # 1. Agent suggests action
        action = agent.suggest_action({**state, 'current_step': env.current_step})
        
        # 2. Environment processes action
        state, reward, done, info = env.step(action)
        total_reward += reward
        
        # 3. Dynamic Theme Switching (Bonus: demonstrate switching during simulation)
        if env.current_step == 5:
            env.change_theme('dark')
            print(f"\n>>> THEME CHANGED: {env.get_theme_indicator()} <<<\n")
        elif env.current_step == 10:
            env.change_theme('medical')
            print(f"\n>>> THEME CHANGED: {env.get_theme_indicator()} <<<\n")

        # 4. Log results with theme indicator
        theme_indicator = env.get_theme_indicator()
        print(f"{theme_indicator} Step {env.current_step}: Action -> {action.upper()}")
        print(f"  Reward: {reward} (Total: {total_reward})")
        print(f"  Info: {info}")
        print(f"  State: {state}")
        print("-" * 50)
        
        time.sleep(0.1) # Brief pause for readability

    print(f"Simulation Complete. Final Reward: {total_reward}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    # Test different levels
    run_simulation(level='easy')
    run_simulation(level='medium')
    run_simulation(level='hard')
