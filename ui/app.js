/**
 * THE ORACLE - UI Controller
 * Handles AI face animations, API communication, and user interactions
 */

class OracleUI {
    constructor() {
        this.apiBaseUrl = localStorage.getItem('apiEndpoint') || 'http://localhost:8000';
        this.currentRunId = null;
        this.pollingInterval = null;
        
        this.init();
    }

    init() {
        this.cacheElements();
        this.bindEvents();
        this.checkServerStatus();
        this.startBlinking();
        this.loadRecentRuns();
        
        // Check status every 10 seconds
        setInterval(() => this.checkServerStatus(), 10000);
    }

    cacheElements() {
        // AI Face
        this.aiAvatar = document.getElementById('aiAvatar');
        this.mouth = document.getElementById('mouth');
        this.stateTitle = document.getElementById('stateTitle');
        this.stateDescription = document.getElementById('stateDescription');
        this.thinkingAnimation = document.getElementById('thinkingAnimation');
        
        // Inputs
        this.taskInput = document.getElementById('taskInput');
        this.repoPath = document.getElementById('repoPath');
        this.modelSelect = document.getElementById('modelSelect');
        
        // Buttons
        this.runBtn = document.getElementById('runBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.approveBtn = document.getElementById('approveBtn');
        this.rejectBtn = document.getElementById('rejectBtn');
        this.refreshRuns = document.getElementById('refreshRuns');
        
        // Options
        this.toggleOptions = document.getElementById('toggleOptions');
        this.optionsContent = document.getElementById('optionsContent');
        
        // Results
        this.resultsSection = document.getElementById('resultsSection');
        this.runId = document.getElementById('runId');
        this.resultStatus = document.getElementById('resultStatus');
        this.approvalActions = document.getElementById('approvalActions');
        
        // Modal
        this.settingsModal = document.getElementById('settingsModal');
        
        // Status
        this.serverStatus = document.getElementById('serverStatus');
    }

    bindEvents() {
        // Run task
        this.runBtn.addEventListener('click', () => this.runTask());
        
        // Clear
        this.clearBtn.addEventListener('click', () => this.clearForm());
        
        // Settings
        this.settingsBtn.addEventListener('click', () => this.openSettings());
        document.getElementById('closeSettings').addEventListener('click', () => this.closeSettings());
        document.getElementById('cancelSettings').addEventListener('click', () => this.closeSettings());
        document.getElementById('saveSettings').addEventListener('click', () => this.saveSettings());
        
        // Toggle options
        this.toggleOptions.addEventListener('click', () => this.toggleOptionsPanel());
        
        // Approval
        this.approveBtn.addEventListener('click', () => this.approveRun());
        this.rejectBtn.addEventListener('click', () => this.rejectRun());
        
        // Refresh runs
        this.refreshRuns.addEventListener('click', () => this.loadRecentRuns());
        
        // Tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // Mouse tracking for eyes
        document.addEventListener('mousemove', (e) => this.trackEyes(e));
    }

    // AI Face Animations
    startBlinking() {
        setInterval(() => {
            this.aiAvatar.classList.add('blinking');
            setTimeout(() => this.aiAvatar.classList.remove('blinking'), 150);
        }, 4000 + Math.random() * 2000);
    }

    trackEyes(e) {
        const eyes = document.querySelectorAll('.eye');
        eyes.forEach(eye => {
            const rect = eye.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
            const distance = Math.min(3, Math.hypot(e.clientX - centerX, e.clientY - centerY) / 30);
            
            const pupil = eye.querySelector('.pupil');
            const x = Math.cos(angle) * distance;
            const y = Math.sin(angle) * distance;
            
            pupil.style.transform = `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
        });
    }

    setAIState(state, message = '') {
        const states = {
            ready: {
                title: 'Ready',
                description: message || "I'm ready to help you with code modifications",
                mouthClass: 'smile',
                avatarClass: ''
            },
            thinking: {
                title: 'Thinking...',
                description: message || "Analyzing your request and planning the approach...",
                mouthClass: 'thinking',
                avatarClass: 'thinking'
            },
            working: {
                title: 'Working...',
                description: message || "Executing the plan and validating changes...",
                mouthClass: 'speaking',
                avatarClass: 'working'
            },
            awaiting_approval: {
                title: 'Awaiting Approval',
                description: message || "Changes are ready for your review",
                mouthClass: 'smile',
                avatarClass: 'success'
            },
            success: {
                title: 'Complete!',
                description: message || "Task completed successfully",
                mouthClass: 'smile',
                avatarClass: 'success'
            },
            error: {
                title: 'Error',
                description: message || "Something went wrong",
                mouthClass: '',
                avatarClass: 'error'
            }
        };

        const config = states[state] || states.ready;
        
        this.stateTitle.textContent = config.title;
        this.stateDescription.textContent = config.description;
        
        // Update mouth
        this.mouth.className = 'mouth ' + config.mouthClass;
        
        // Update avatar state
        this.aiAvatar.className = 'ai-avatar ' + config.avatarClass;
        
        // Thinking animation
        this.thinkingAnimation.classList.toggle('active', 
            state === 'thinking' || state === 'working'
        );
    }

    // API Communication
    async checkServerStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' }
            });
            
            if (response.ok) {
                this.serverStatus.className = 'status-indicator online';
                this.serverStatus.querySelector('.status-text').textContent = 'Online';
                this.runBtn.disabled = false;
            } else {
                throw new Error('Server not ready');
            }
        } catch (error) {
            this.serverStatus.className = 'status-indicator offline';
            this.serverStatus.querySelector('.status-text').textContent = 'Offline';
            this.runBtn.disabled = true;
        }
    }

    async runTask() {
        const task = this.taskInput.value.trim();
        const repo = this.repoPath.value.trim();
        
        if (!task) {
            alert('Please enter a task description');
            return;
        }
        
        if (!repo) {
            alert('Please enter a repository path');
            return;
        }
        
        this.setAIState('thinking', 'Planning your code modification...');
        this.runBtn.disabled = true;
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/run`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    task: task,
                    repo_path: repo
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.currentRunId = data.run_id;
            
            this.showResults(data);
            this.loadRecentRuns();
            
            // Poll for status updates
            this.startPolling(data.run_id);
            
        } catch (error) {
            console.error('Error:', error);
            this.setAIState('error', error.message);
            this.runBtn.disabled = false;
        }
    }

    startPolling(runId) {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBaseUrl}/runs/${runId}`);
                if (response.ok) {
                    const data = await response.json();
                    this.updateResults(data);
                    
                    // Stop polling if terminal state
                    if (['applied', 'rejected', 'failed'].includes(data.status)) {
                        clearInterval(this.pollingInterval);
                        this.pollingInterval = null;
                        this.runBtn.disabled = false;
                    }
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 2000);
    }

    showResults(data) {
        this.resultsSection.style.display = 'block';
        this.runId.textContent = `Run: ${data.run_id}`;
        this.updateResults(data);
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    updateResults(data) {
        // Update status badge
        this.resultStatus.className = 'status-badge ' + data.status;
        this.resultStatus.textContent = data.status.replace('_', ' ');
        
        // Update summary
        document.getElementById('resultTask').textContent = data.task || '-';
        document.getElementById('resultRepo').textContent = data.repo_path || '-';
        document.getElementById('resultFiles').textContent = 
            data.files_changed ? data.files_changed.join(', ') : '-';
        document.getElementById('resultAttempts').textContent = data.attempts || '-';
        
        // Update AI state based on run status
        if (data.status === 'awaiting_approval') {
            this.setAIState('awaiting_approval', 'Changes are ready for your review!');
            this.approvalActions.style.display = 'block';
        } else if (data.status === 'applied') {
            this.setAIState('success', 'Changes applied successfully!');
            this.approvalActions.style.display = 'none';
        } else if (data.status === 'rejected') {
            this.setAIState('ready', 'Changes were rejected');
            this.approvalActions.style.display = 'none';
        } else if (data.status === 'failed') {
            this.setAIState('error', data.reason || 'Task failed');
            this.approvalActions.style.display = 'none';
        } else {
            this.setAIState('working', `Status: ${data.status}...`);
        }
    }

    async approveRun() {
        if (!this.currentRunId) return;
        
        this.setAIState('working', 'Applying changes...');
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/runs/${this.currentRunId}/decide`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    decision: 'approved',
                    actor: 'operator',
                    note: 'Approved via UI'
                })
            });
            
            if (!response.ok) throw new Error('Approval failed');
            
            const data = await response.json();
            this.updateResults(data.run);
            this.loadRecentRuns();
            
        } catch (error) {
            this.setAIState('error', error.message);
        }
    }

    async rejectRun() {
        if (!this.currentRunId) return;
        
        this.setAIState('working', 'Rejecting changes...');
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/runs/${this.currentRunId}/decide`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    decision: 'rejected',
                    actor: 'operator',
                    note: 'Rejected via UI'
                })
            });
            
            if (!response.ok) throw new Error('Rejection failed');
            
            const data = await response.json();
            this.updateResults(data.run);
            this.loadRecentRuns();
            
        } catch (error) {
            this.setAIState('error', error.message);
        }
    }

    async loadRecentRuns() {
        try {
            // Get runs from localStorage or fetch from API
            // For now, we'll show a message that this needs backend support
            const runsList = document.getElementById('runsList');
            
            // Try to get runs from the filesystem API if available
            const response = await fetch(`${this.apiBaseUrl}/runs`);
            if (response.ok) {
                const runs = await response.json();
                this.renderRunsList(runs);
            } else {
                runsList.innerHTML = '<p class="empty-state">Run list API not available</p>';
            }
        } catch (error) {
            document.getElementById('runsList').innerHTML = 
                '<p class="empty-state">Connect to server to see recent runs</p>';
        }
    }

    renderRunsList(runs) {
        const runsList = document.getElementById('runsList');
        
        if (!runs || runs.length === 0) {
            runsList.innerHTML = '<p class="empty-state">No recent runs</p>';
            return;
        }
        
        runsList.innerHTML = runs.slice(0, 5).map(run => `
            <div class="run-item" data-run-id="${run.run_id}">
                <div class="run-item-info">
                    <span class="run-item-task">${this.escapeHtml(run.task)}</span>
                    <span class="run-item-meta">${new Date(run.timestamp).toLocaleString()}</span>
                </div>
                <span class="run-item-status status-${run.status}">${run.status}</span>
            </div>
        `).join('');
        
        // Add click handlers
        runsList.querySelectorAll('.run-item').forEach(item => {
            item.addEventListener('click', () => this.loadRun(item.dataset.runId));
        });
    }

    async loadRun(runId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/runs/${runId}`);
            if (response.ok) {
                const data = await response.json();
                this.currentRunId = runId;
                this.showResults(data);
            }
        } catch (error) {
            console.error('Error loading run:', error);
        }
    }

    // UI Helpers
    toggleOptionsPanel() {
        this.optionsContent.classList.toggle('collapsed');
        this.toggleOptions.classList.toggle('collapsed');
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(tabName + 'Tab').classList.add('active');
    }

    clearForm() {
        this.taskInput.value = '';
        this.repoPath.value = '';
        this.setAIState('ready');
        this.resultsSection.style.display = 'none';
        this.currentRunId = null;
        
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    openSettings() {
        document.getElementById('apiEndpoint').value = this.apiBaseUrl;
        this.settingsModal.classList.add('active');
    }

    closeSettings() {
        this.settingsModal.classList.remove('active');
    }

    saveSettings() {
        this.apiBaseUrl = document.getElementById('apiEndpoint').value;
        localStorage.setItem('apiEndpoint', this.apiBaseUrl);
        
        // Save API keys to localStorage (in production, use secure storage)
        const kimiKey = document.getElementById('kimiKey').value;
        if (kimiKey && !kimiKey.includes('•')) {
            localStorage.setItem('kimiApiKey', kimiKey);
        }
        
        const openaiKey = document.getElementById('openaiKey').value;
        if (openaiKey) {
            localStorage.setItem('openaiApiKey', openaiKey);
        }
        
        this.closeSettings();
        this.checkServerStatus();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.oracle = new OracleUI();
});
