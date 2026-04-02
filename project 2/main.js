/**
 * AI Health Companion - Simulation Frontend (OpenEnv Compliant)
 * Connects to the FastAPI backend to drive the health simulation.
 */

const App = {
    state: {
        observation: {},
        currentStep: 0,
        totalReward: 0,
        suggestion: { action_type: 'skip' },
        done: false
    },

    async init() {
        console.log('Initializing AI Health Companion (Authenticated Edition)...');
        // Check if token exists
        if (!localStorage.getItem('auth_token')) {
            window.location.href = '/login.html';
            return;
        }

        await this.resetEnv('easy');
        this.initEventListeners();
        this.startPolling();
    },

    initEventListeners() {
        // SOS / Emergency Handling
        const sosTrigger = document.getElementById('sos-trigger');
        if (sosTrigger) {
            sosTrigger.onclick = () => {
                 this.step({ action_type: 'handle_emergency' });
            };
        }

        // Execute AI Suggestion
        const execBtn = document.getElementById('execute-ai-btn');
        if (execBtn) {
            execBtn.onclick = () => {
                if (this.state.done) {
                    alert("Episode complete. Please reset to start again.");
                    return;
                }
                this.step(this.state.suggestion);
            };
        }
    },

    // --- Auth Helper ---
    async authFetch(url, options = {}) {
        const token = localStorage.getItem('auth_token');
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };

        const response = await fetch(url, { ...options, headers });
        
        if (response.status === 401) {
            console.error('Session expired or unauthorized');
            this.logout();
            return null;
        }
        
        return response;
    },

    logout() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_role');
        window.location.href = '/login.html';
    },

    // --- API Calls ---
    async resetEnv(taskId = 'easy') {
        try {
            const response = await this.authFetch('/reset', {
                method: 'POST',
                body: JSON.stringify({ task_id: taskId })
            });
            if (!response) return;

            const data = await response.json();
            this.state.observation = data;
            this.state.currentStep = 0;
            this.state.totalReward = 0;
            this.state.done = false;
            this.render();
        } catch (err) {
            console.error('Failed to reset environment:', err);
        }
    },

    async step(action) {
        if (this.state.done) return;

        try {
            const response = await this.authFetch('/step', {
                method: 'POST',
                body: JSON.stringify(action)
            });
            if (!response) return;

            const data = await response.json();
            
            this.state.observation = data.observation;
            this.state.totalReward += data.reward.value;
            this.state.done = data.done;
            this.state.currentStep++;

            this.render();
            
            if (this.state.done) {
                this.showFinalGrade();
            } else {
                this.fetchSuggestion();
            }
        } catch (err) {
            console.error('Failed to execute step:', err);
        }
    },

    async fetchSuggestion() {
        try {
            const response = await this.authFetch('/suggestion');
            if (!response) return;

            const data = await response.json();
            this.state.suggestion = data;
            this.updateSuggestionUI(data);
        } catch (err) {
            console.error('Failed to fetch suggestion:', err);
        }
    },

    async showFinalGrade() {
        try {
            const response = await this.authFetch('/grade', { method: 'POST' });
            if (!response) return;

            const data = await response.json();
            
            const logArea = document.getElementById('env-log');
            if (logArea) {
                logArea.innerHTML += `<div style="color: #f59e0b; font-weight: bold; margin-top: 10px;">${data.summary}</div>`;
                logArea.scrollTop = logArea.scrollHeight;
            }
            
            alert(`Simulation Complete!\nScore: ${data.score}\n${data.summary}`);
        } catch (err) {
            console.error('Failed to fetch grade:', err);
        }
    },

    // --- UI Rendering ---
    render() {
        const obs = this.state.observation;
        if (!obs || !obs.medicines) return;

        const stressDisp = document.getElementById('stress-display');
        if (stressDisp) stressDisp.innerHTML = `${obs.stress_level.toFixed(1)}<span>/10</span>`;
        
        const checkupDisp = document.getElementById('checkup-display');
        if (checkupDisp) checkupDisp.innerText = obs.upcoming_checkup || 'N/A';
        
        const stepCounter = document.getElementById('step-counter');
        if (stepCounter) stepCounter.innerText = `Step: ${this.state.currentStep}`;
        
        const rewardDisp = document.getElementById('reward-display');
        if (rewardDisp) rewardDisp.innerText = `Total Reward: ${this.state.totalReward.toFixed(1)}`;
        
        // Med List
        const medList = document.getElementById('med-list');
        if (medList) {
            medList.innerHTML = '';
            if (obs.medicines.length === 0) {
                medList.innerHTML = '<li class="empty-state">No medications scheduled.</li>';
            } else {
                obs.medicines.forEach(med => {
                    const li = document.createElement('li');
                    li.className = 'task-item';
                    const statusColor = med.is_missed ? '#ef4444' : (med.taken ? '#10b981' : '#64748b');
                    const statusIcon = med.is_missed ? 'alert-triangle' : (med.taken ? 'check-circle-2' : 'clock');
                    
                    li.innerHTML = `
                        <div class="task-info">
                            <strong>${med.name}</strong> at ${this.formatTime(med.time_24h)}
                        </div>
                        <div class="status-marker">
                            <i data-lucide="${statusIcon}" style="color:${statusColor}"></i>
                        </div>
                    `;
                    medList.appendChild(li);
                });
            }
        }

        // Log
        if (obs.last_action_info) {
            const logArea = document.getElementById('env-log');
            if (logArea) {
                const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                logArea.innerHTML += `<div>[${timestamp}] ${obs.last_action_info}</div>`;
                logArea.scrollTop = logArea.scrollHeight;
            }
        }

        // Emergency Overlay
        const sosOverlay = document.getElementById('sos-overlay');
        if (sosOverlay) {
            if (obs.emergency_status) {
                sosOverlay.classList.remove('hidden');
            } else {
                sosOverlay.classList.add('hidden');
            }
        }

        // Re-initialize Lucide icons
        if (window.lucide) window.lucide.createIcons();
    },

    updateSuggestionUI(suggestion) {
        const textArea = document.getElementById('suggestion-text');
        if (textArea) {
            const actions = {
                'handle_emergency': 'EMERGENCY! Resolving emergency is critical.',
                'remind_medicine': 'Medication is due. Remind patient now.',
                'reduce_stress': 'Stress is high. Initiating guided breathing.',
                'schedule_checkup': 'Scheduling routine checkup.',
                'skip': 'All clear. No urgent tasks.'
            };
            textArea.innerText = actions[suggestion.action_type] || 'Analyzing state...';
        }
    },

    // --- Helpers ---
    startPolling() {
        this.fetchSuggestion();
        setInterval(() => {
            if (!this.state.done && localStorage.getItem('auth_token')) {
                this.fetchSuggestion();
            }
        }, 5000);
    },

    formatTime(hour) {
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const h = hour % 12 || 12;
        return `${h}:00 ${ampm}`;
    }
};

// Start the app
window.onload = () => App.init();
