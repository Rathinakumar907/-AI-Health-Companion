/**
 * AI Health Companion - Simulation Frontend
 * Connects to the Flask backend to drive the health simulation.
 */

const App = {
    state: {
        health: {},
        currentStep: 0,
        totalReward: 0,
        suggestion: 'skip'
    },

    async init() {
        console.log('Initializing AI Health Companion Simulator...');
        await this.resetEnv('easy'); // Start with easy mode
        this.initEventListeners();
        this.startSuggestionTimer();
    },

    initEventListeners() {
        document.getElementById('sos-trigger').onclick = () => {
            document.getElementById('sos-overlay').classList.remove('hidden');
        };

        document.getElementById('execute-ai-btn').onclick = () => {
            this.step(this.state.suggestion);
        };
    },

    // --- API Calls ---
    async resetEnv(level) {
        try {
            const response = await fetch('/api/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ level })
            });
            const data = await response.json();
            this.updateState(data);
            this.state.totalReward = 0; // Reset rewards on manual reset
            this.render();
        } catch (err) {
            console.error('Failed to reset environment:', err);
        }
    },

    async step(action) {
        try {
            const response = await fetch('/api/step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });
            const data = await response.json();
            this.state.totalReward += data.reward;
            this.updateState(data);
            this.render();
            
            // Re-fetch suggestion after step
            this.fetchSuggestion();
        } catch (err) {
            console.error('Failed to execute step:', err);
        }
    },

    async fetchSuggestion() {
        try {
            const response = await fetch('/api/suggest');
            const data = await response.json();
            this.state.suggestion = data.suggestion;
            this.updateSuggestionUI(data.suggestion);
        } catch (err) {
            console.error('Failed to fetch suggestion:', err);
        }
    },

    // --- UI Rendering ---
    updateState(data) {
        this.state.health = data.state;
        this.state.currentStep = data.current_step;
    },

    render() {
        const h = this.state.health;
        
        // Stats
        document.getElementById('stress-display').innerHTML = `${h.stress_level}<span>/10</span>`;
        document.getElementById('checkup-display').innerText = h.upcoming_checkup;
        document.getElementById('step-counter').innerText = `Step: ${this.state.currentStep}`;
        document.getElementById('reward-display').innerText = `Total Reward: ${this.state.totalReward}`;
        
        // Med List
        const medList = document.getElementById('med-list');
        medList.innerHTML = '';
        if (h.medicines.length === 0) {
            medList.innerHTML = '<li class="empty-state">No medications scheduled.</li>';
        } else {
            h.medicines.forEach(med => {
                const li = document.createElement('li');
                li.className = 'task-item';
                li.innerHTML = `
                    <div class="task-info">
                        <strong>${med.name}</strong> at ${this.formatTime(med.time)}
                    </div>
                    <div class="status-marker">
                        ${med.taken ? '<i data-lucide="check-circle-2" class="check-circle" style="color:#10b981"></i>' : '<i data-lucide="clock" style="color:#64748b"></i>'}
                    </div>
                `;
                medList.appendChild(li);
            });
        }

        // Log
        const logArea = document.getElementById('env-log');
        logArea.innerText = `[${new Date().toLocaleTimeString()}] ${h.log}`;
        logArea.scrollTop = logArea.scrollHeight;

        // Emergency Overlay
        const sosOverlay = document.getElementById('sos-overlay');
        if (h.emergency_status) {
            sosOverlay.classList.remove('hidden');
        } else {
            sosOverlay.classList.add('hidden');
        }

        // Re-initialize Lucide icons
        if (window.lucide) window.lucide.createIcons();
    },

    updateSuggestionUI(suggestion) {
        const textArea = document.getElementById('suggestion-text');
        const actions = {
            'handle_emergency': 'EMERGENCY DETECTED! Use "Resolve Emergency" immediately.',
            'remind_medicine': 'A medicine dose is due. Send a reminder now.',
            'reduce_stress': 'Stress levels are climbing. Guided breathing is recommended.',
            'schedule_checkup': 'Time to schedule your routine checkup.',
            'skip': 'Health is stable. No urgent actions needed.'
        };
        textArea.innerText = actions[suggestion] || 'Awaiting state analysis...';
    },

    // --- Helpers ---
    startSuggestionTimer() {
        this.fetchSuggestion();
        setInterval(() => this.fetchSuggestion(), 3000); // Polling suggestion for demo
    },

    formatTime(hour) {
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const h = hour % 12 || 12;
        return `${h}:00 ${ampm}`;
    }
};

// Start the app
window.onload = () => App.init();
