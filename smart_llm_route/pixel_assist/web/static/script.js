const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const newSessionBtn = document.getElementById('newSessionBtn');
const sessionList = document.getElementById('sessionList');
const statsDiv = document.getElementById('stats');
const modelSelect = document.getElementById('modelSelect');
const personalitySelect = document.getElementById('personalitySelect');
const customInstructions = document.getElementById('customInstructions');
const saveInstructionsBtn = document.getElementById('saveInstructionsBtn');
const newRuleInput = document.getElementById('newRule');
const addRuleBtn = document.getElementById('addRuleBtn');
const rulesList = document.getElementById('rulesList');
const discoverModelsBtn = document.getElementById('discoverModelsBtn');
const customModelNameInput = document.getElementById('customModelName');
const customModelUrlInput = document.getElementById('customModelUrl');
const customModelEndpointSelect = document.getElementById('customModelEndpoint');
const addCustomModelBtn = document.getElementById('addCustomModelBtn');
const customModelsList = document.getElementById('customModelsList');

let currentSessionId = localStorage.getItem('pixel_session_id') || null;
let selectedModel = '';

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const models = await response.json();
        
        modelSelect.innerHTML = '<option value="">Select a model...</option>';
        models.forEach(m => {
            const option = document.createElement('option');
            option.value = m.name;
            const desc = m.description || m.provider || 'custom';
            option.textContent = `${m.name} - ${desc}`;
            modelSelect.appendChild(option);
        });
        
        await loadCustomModels();
    } catch (error) {
        console.error('Failed to load models:', error);
    }
}

async function loadCustomModels() {
    try {
        const response = await fetch('/api/custom-models');
        const models = await response.json();
        
        customModelsList.innerHTML = models.map(m => `
            <div class="custom-model-item">
                <span>${m.name}</span>
                <button class="remove-model" data-name="${m.name}">&times;</button>
            </div>
        `).join('');
        
        customModelsList.querySelectorAll('.remove-model').forEach(btn => {
            btn.addEventListener('click', () => removeCustomModel(btn.dataset.name));
        });
        
        models.forEach(m => {
            const option = document.createElement('option');
            option.value = m.name;
            option.textContent = `${m.name} (Custom)`;
            modelSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load custom models:', error);
    }
}

async function discoverModels() {
    discoverModelsBtn.disabled = true;
    discoverModelsBtn.textContent = 'Discovering...';
    
    try {
        const response = await fetch('/api/custom-models/discover');
        const results = await response.json();
        
        if (results.length === 0) {
            addMessage('system', 'No local models found. Make sure Ollama or LM Studio is running.');
        } else {
            let msg = 'Discovered models:\n';
            results.forEach(r => {
                msg += `\n${r.server}: ${r.models.join(', ')}`;
                r.models.forEach(modelName => {
                    const option = document.createElement('option');
                    option.value = modelName;
                    option.textContent = `${modelName} (${r.server})`;
                    modelSelect.appendChild(option);
                });
            });
            addMessage('system', msg);
        }
    } catch (error) {
        addMessage('error', 'Failed to discover models: ' + error.message);
    } finally {
        discoverModelsBtn.disabled = false;
        discoverModelsBtn.textContent = 'Discover Models';
    }
}

async function addCustomModel() {
    const name = customModelNameInput.value.trim();
    const base_url = customModelUrlInput.value.trim();
    const endpoint = customModelEndpointSelect.value;
    
    if (!name || !base_url) {
        addMessage('error', 'Please enter model name and base URL');
        return;
    }
    
    try {
        const response = await fetch('/api/custom-models', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                base_url: base_url,
                endpoint: endpoint,
                provider: endpoint === '/api/generate' ? 'local' : 'openai-compatible',
                capabilities: ['general', 'coding'],
                cost_per_1k: 0.0,
                description: `Custom model: ${name}`
            })
        });
        
        const data = await response.json();
        if (data.success) {
            customModelNameInput.value = '';
            customModelUrlInput.value = '';
            loadCustomModels();
            addMessage('system', `Model ${name} added!`);
        } else {
            addMessage('error', data.error || 'Failed to add model');
        }
    } catch (error) {
        addMessage('error', 'Failed to add model: ' + error.message);
    }
}

async function removeCustomModel(name) {
    try {
        const response = await fetch(`/api/custom-models/${name}`, { method: 'DELETE' });
        const data = await response.json();
        if (data.success) {
            loadCustomModels();
            loadModels();
        }
    } catch (error) {
        console.error('Failed to remove model:', error);
    }
}

async function loadInstructions() {
    try {
        const response = await fetch('/api/instructions');
        const data = await response.json();
        
        personalitySelect.value = 'default';
        for (const key in data.system_prompts) {
            if (data.system_prompts[key] === data.current) {
                personalitySelect.value = key;
                break;
            }
        }
        
        if (personalitySelect.value === 'custom' || !data.system_prompts[personalitySelect.value]) {
            personalitySelect.value = 'custom';
            customInstructions.value = data.current;
        }
        
        rulesList.innerHTML = data.rules.map(r => `
            <div class="rule-item">
                ${escapeHtml(r)}
                <button class="remove-rule" data-rule="${escapeHtml(r)}">&times;</button>
            </div>
        `).join('');
        
        rulesList.querySelectorAll('.remove-rule').forEach(btn => {
            btn.addEventListener('click', () => removeRule(btn.dataset.rule));
        });
    } catch (error) {
        console.error('Failed to load instructions:', error);
    }
}

async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        const sessions = await response.json();
        
        sessionList.innerHTML = sessions.map(s => `
            <div class="session-item" data-id="${s.id}">
                ${s.title || s.id.substring(0, 8)} (${s.message_count})
            </div>
        `).join('');
        
        sessionList.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', () => loadSession(item.dataset.id));
        });
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    localStorage.setItem('pixel_session_id', sessionId);
    chatMessages.innerHTML = '';
    addMessage('assistant', 'Session loaded. Start chatting!');
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        statsDiv.innerHTML = `
            <div>Sessions: ${data.sessions || 0}</div>
            <div>Messages: ${data.total_messages || 0}</div>
        `;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `<div class="message-content">${escapeHtml(content)}</div>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    addMessage('user', message);
    messageInput.value = '';
    
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="loading"></span>';
    
    try {
        const payload = {
            message: message,
            session_id: currentSessionId
        };
        
        if (selectedModel) {
            payload.model_preference = selectedModel;
        }
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.error) {
            addMessage('error', data.error);
        } else {
            currentSessionId = data.session_id;
            localStorage.setItem('pixel_session_id', currentSessionId);
            addMessage('assistant', data.message);
        }
    } catch (error) {
        addMessage('error', 'Failed to send message: ' + error.message);
    } finally {
        sendButton.disabled = false;
        sendButton.innerHTML = 'Send';
        loadStats();
    }
}

async function newSession() {
    currentSessionId = null;
    localStorage.removeItem('pixel_session_id');
    chatMessages.innerHTML = '';
    addMessage('assistant', 'New chat session started. How can I help you?');
}

async function saveInstructions() {
    try {
        const response = await fetch('/api/instructions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instructions: customInstructions.value })
        });
        const data = await response.json();
        if (data.success) {
            addMessage('system', 'Instructions saved!');
        } else {
            addMessage('error', data.error || 'Failed to save');
        }
    } catch (error) {
        addMessage('error', 'Failed to save instructions');
    }
}

async function addRule() {
    const rule = newRuleInput.value.trim();
    if (!rule) return;
    
    try {
        const response = await fetch('/api/instructions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rule: rule })
        });
        const data = await response.json();
        if (data.success) {
            newRuleInput.value = '';
            loadInstructions();
        }
    } catch (error) {
        console.error('Failed to add rule:', error);
    }
}

async function removeRule(rule) {
    try {
        const response = await fetch('/api/instructions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rule: rule, action: 'remove' })
        });
        const data = await response.json();
        if (data.success) {
            loadInstructions();
        }
    } catch (error) {
        console.error('Failed to remove rule:', error);
    }
}

modelSelect.addEventListener('change', () => {
    selectedModel = modelSelect.value;
});

personalitySelect.addEventListener('change', async () => {
    const value = personalitySelect.value;
    if (value === 'custom') {
        customInstructions.style.display = 'block';
    } else {
        customInstructions.style.display = 'none';
        try {
            await fetch('/api/instructions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ system_prompt: value })
            });
            loadInstructions();
        } catch (error) {
            console.error('Failed to set personality:', error);
        }
    }
});

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

newSessionBtn.addEventListener('click', newSession);
saveInstructionsBtn.addEventListener('click', saveInstructions);
addRuleBtn.addEventListener('click', addRule);
discoverModelsBtn.addEventListener('click', discoverModels);
addCustomModelBtn.addEventListener('click', addCustomModel);

loadModels();
loadInstructions();
loadSessions();
loadStats();
addMessage('assistant', 'Welcome to Pixel-assist! Your AI coding assistant with local model support.\n\nClick "Discover Models" to find local models, or add a custom model URL.');
