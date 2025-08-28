class ProductQueryBot {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.updateStatus();
    }

    initializeElements() {
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.messages = document.getElementById('messages');
        this.sourcesPanel = document.getElementById('sourcesPanel');
        this.sourcesContent = document.getElementById('sourcesContent');
        this.closeSources = document.getElementById('closeSources');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.status = document.getElementById('status');
    }

    bindEvents() {
        this.messageForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.closeSources.addEventListener('click', () => this.hideSources());
        this.messageInput.addEventListener('input', () => this.handleInput());
        
        // Close sources panel when clicking outside
        document.addEventListener('click', (e) => {
            if (this.sourcesPanel.classList.contains('open') && 
                !this.sourcesPanel.contains(e.target) && 
                !e.target.classList.contains('sources-trigger')) {
                this.hideSources();
            }
        });
    }

    handleInput() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText;
    }

    async handleSubmit(e) {
        e.preventDefault();
        const query = this.messageInput.value.trim();
        
        if (!query) return;

        // Add user message
        this.addUserMessage(query);
        this.messageInput.value = '';
        this.sendButton.disabled = true;

        // Show loading with pipeline simulation
        this.showLoading();
        
        try {
            const startTime = Date.now();
            const response = await this.queryAPI(query);
            const endTime = Date.now();
            const latency = endTime - startTime;
            
            this.hideLoading();
            this.addBotMessage(response, latency);
            
        } catch (error) {
            this.hideLoading();
            this.addErrorMessage(error.message);
        }
    }

    async queryAPI(query) {
        const payload = {
            user_id: this.generateUserId(),
            query: query
        };

        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(text)}</div>
                <div class="message-meta">
                    <span class="message-time">${this.formatTime()}</span>
                </div>
            </div>
        `;
        
        this.messages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addBotMessage(response, latency) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        
        const sourcesCount = response.sources?.length || 0;
        const sourcesInfo = sourcesCount > 0 
            ? `<span class="sources-trigger" onclick="bot.showSources(${JSON.stringify(response.sources).replace(/"/g, '&quot;')})">📚 ${sourcesCount} sources</span>`
            : '';
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">${this.formatBotResponse(response.answer)}</div>
                <div class="message-meta">
                    <span class="message-time">${this.formatTime()}</span>
                    <span class="latency-info">${latency}ms</span>
                    ${sourcesInfo}
                </div>
            </div>
        `;
        
        this.messages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Auto-show sources if available
        if (sourcesCount > 0) {
            setTimeout(() => {
                this.showSources(response.sources);
            }, 500);
        }
    }

    addErrorMessage(errorMessage) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">
                    ❌ Sorry, an error occurred while processing your query.<br>
                    <small style="color: #666; margin-top: 0.5rem; display: block;">
                        ${this.escapeHtml(errorMessage)}
                    </small>
                </div>
                <div class="message-meta">
                    <span class="message-time">${this.formatTime()}</span>
                    <span class="pipeline-info">⚠️ Error</span>
                </div>
            </div>
        `;
        
        this.messages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatBotResponse(answer) {
        if (!answer) return 'Sorry, I could not generate a response.';
        
        // Convert [doc_id] references to badges
        let formatted = answer.replace(/\[([^\]]+)\]/g, '<span class="doc-badge">$1</span>');
        
        // Convert line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }

    showLoading() {
        this.loadingOverlay.classList.add('show');
        
        // Simulate pipeline steps
        setTimeout(() => {
            document.getElementById('step1').classList.remove('active');
            document.getElementById('step2').classList.add('active');
        }, 800);
        
        setTimeout(() => {
            document.getElementById('step2').classList.remove('active');
            document.getElementById('step3').classList.add('active');
        }, 1600);
    }

    hideLoading() {
        this.loadingOverlay.classList.remove('show');
        
        // Reset steps
        document.getElementById('step1').classList.add('active');
        document.getElementById('step2').classList.remove('active');
        document.getElementById('step3').classList.remove('active');
    }

    showSources(sources) {
        if (!sources || sources.length === 0) {
            this.sourcesContent.innerHTML = '<p class="sources-placeholder">No sources found.</p>';
        } else {
            this.sourcesContent.innerHTML = sources.map(source => `
                <div class="source-item">
                    <div class="source-header">
                        <span class="source-id">📄 ${source.doc_id}</span>
                        <span class="source-score">Score: ${(source.score || 0).toFixed(3)}</span>
                    </div>
                    <div class="source-text">${this.escapeHtml(source.text || 'Text not available')}</div>
                </div>
            `).join('');
        }
        
        this.sourcesPanel.classList.add('open');
    }

    hideSources() {
        this.sourcesPanel.classList.remove('open');
    }

    async updateStatus() {
        try {
            const response = await fetch('/health');
            const health = await response.json();
            
            if (health.status === 'ok') {
                this.status.innerHTML = `
                    <span class="status-dot"></span>
                    <span>RAG Pipeline Ready</span>
                `;
            }
        } catch (error) {
            this.status.innerHTML = `
                <span class="status-dot" style="background: #ff6b6b;"></span>
                <span>Connection Error</span>
            `;
        }
    }

    generateUserId() {
        return `user_${Math.random().toString(36).substr(2, 9)}`;
    }

    formatTime() {
        return new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        setTimeout(() => {
            this.messages.scrollTop = this.messages.scrollHeight;
        }, 100);
    }
}

// Initialize the bot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.bot = new ProductQueryBot();
});

// Add some CSS for doc badges
const style = document.createElement('style');
style.textContent = `
    .doc-badge {
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.1rem 0.4rem;
        border-radius: 8px;
        font-size: 0.85em;
        font-weight: 500;
        margin: 0 0.1rem;
    }
`;
document.head.appendChild(style);
