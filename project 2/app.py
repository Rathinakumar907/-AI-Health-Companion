import random
import os
from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime, timedelta

class ThemeManager:
    """
    Manages the visual theme of the AI Health Companion.
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

app = Flask(__name__, static_folder='.')

# --- Simulation Logic (From health_sim.py) ---
class HealthEnv:
    def __init__(self):
        self.state = {}
        self.current_step = 0
        self.theme_manager = ThemeManager()
        self.reset()

    def reset(self, level='easy'):
        self.current_step = 0
        self.state = {
            'medicines': [],
            'stress_level': 2,
            'emergency_status': False,
            'upcoming_checkup': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'time_elapsed': 0,
            'log': "Environment Reset."
        }

        if level == 'easy':
            self.state['medicines'] = [{'id': 1, 'name': 'Vitamin C', 'time': 8, 'taken': False}]
            self.state['stress_level'] = 1
        elif level == 'medium':
            self.state['medicines'] = [
                {'id': 1, 'name': 'Aspirin', 'time': 8, 'taken': False},
                {'id': 2, 'name': 'Metformin', 'time': 20, 'taken': False}
            ]
            self.state['stress_level'] = 5
        elif level == 'hard':
            self.state['medicines'] = [
                {'id': 1, 'name': 'Lisinopril', 'time': 9, 'taken': False},
                {'id': 2, 'name': 'Insulin', 'time': 13, 'taken': False},
                {'id': 3, 'name': 'Atorvastatin', 'time': 21, 'taken': False}
            ]
            self.state['stress_level'] = 8
            if random.random() > 0.5:
                self.state['emergency_status'] = True
        return self.state

    def step(self, action):
        reward = 0
        info = ""
        self.current_step += 1
        self.state['time_elapsed'] += 1

        if action == 'handle_emergency':
            if self.state['emergency_status']:
                self.state['emergency_status'] = False
                reward += 15
                info = "Emergency handled successfully!"
            else:
                reward -= 5
                info = "No emergency to handle."
        elif action == 'remind_medicine':
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
                reward += 2
                info = "Stress levels maintained."
        elif action == 'schedule_checkup':
            new_date = (datetime.now() + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d')
            self.state['upcoming_checkup'] = new_date
            reward += 2
            info = f"New checkup scheduled for {new_date}."
        elif action == 'skip':
            reward -= 1
            info = "No action taken."

        if random.random() > 0.7:
            self.state['stress_level'] = min(10, self.state['stress_level'] + 1)
        
        current_hour = self.state['time_elapsed'] % 24
        for med in self.state['medicines']:
            if not med['taken'] and current_hour > med['time'] + 1:
                reward -= 10
                info += f" | WARNING: Missed dose of {med['name']}!"
                med['taken'] = True 

        if random.random() > 0.98: # Lowered for demo stability
            self.state['emergency_status'] = True
            info += " | ALERT: Health Emergency Detected!"

        self.state['log'] = f"{self.theme_manager.get_indicator()} {info}"
        return self.state, reward

    def change_theme(self, theme_name):
        return self.theme_manager.change_theme(theme_name)

    def get_theme_indicator(self):
        return self.theme_manager.get_indicator()

class AICompanionAgent:
    def suggest_action(self, state, current_step):
        if state['emergency_status']: return 'handle_emergency'
        current_hour = state['time_elapsed'] % 24
        for med in state['medicines']:
            if not med['taken'] and abs(med['time'] - current_hour) <= 1:
                return 'remind_medicine'
        if state['stress_level'] > 5: return 'reduce_stress'
        if current_step % 10 == 0: return 'schedule_checkup'
        return 'skip'

# Initialize Global Instances
env = HealthEnv()
agent = AICompanionAgent()

# --- Flask Routes ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('.', path)

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify({
        'state': env.state,
        'current_step': env.current_step
    })

@app.route('/api/suggest', methods=['GET'])
def get_suggestion():
    suggestion = agent.suggest_action(env.state, env.current_step)
    return jsonify({'suggestion': suggestion})

@app.route('/api/step', methods=['POST'])
def process_step():
    data = request.json
    action = data.get('action', 'skip')
    new_state, reward = env.step(action)
    return jsonify({
        'state': new_state,
        'reward': reward,
        'current_step': env.current_step
    })

@app.route('/api/reset', methods=['POST'])
def reset_env():
    data = request.json
    level = data.get('level', 'easy')
    new_state = env.reset(level=level)
    return jsonify({
        'state': new_state,
        'current_step': env.current_step
    })

@app.route('/api/theme', methods=['POST'])
def change_theme():
    data = request.json
    theme_name = data.get('theme', 'light')
    success = env.change_theme(theme_name)
    return jsonify({
        'success': success,
        'current_theme': env.get_theme_indicator()
    })

if __name__ == '__main__':
    # Ensure port 5000 is used
    app.run(host='0.0.0.0', port=5000, debug=True)
