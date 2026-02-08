/**
 * UI Components and Rendering Functions
 */

/**
 * Render a user message
 */
function renderUserMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = content;

    messageDiv.appendChild(bubble);
    return messageDiv;
}

/**
 * Render a bot message
 */
function renderBotMessage(content = '') {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    // Render markdown if content exists
    if (content && typeof renderMarkdown === 'function') {
        bubble.innerHTML = renderMarkdown(content);
    } else {
        bubble.textContent = content;
    }

    messageDiv.appendChild(bubble);
    return messageDiv;
}

/**
 * Render typing indicator
 */
function renderTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.id = 'typingIndicator';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'typing-dot';
        indicator.appendChild(dot);
    }

    bubble.appendChild(indicator);
    messageDiv.appendChild(bubble);

    return messageDiv;
}

/**
 * Remove typing indicator
 */
function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Scroll messages to bottom
 */
function scrollToBottom() {
    const messagesArea = document.getElementById('messagesArea');
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

/**
 * Add welcome message
 */
function addWelcomeMessage(userName = null) {
    const messagesArea = document.getElementById('messagesArea');
    const greeting = userName ? `Hey ${userName}! 👋` : "Hey! 🍕";
    const welcomeMsg = renderBotMessage(
        `${greeting} I'm CheziousBot. Ask me about our menu, locations, hours, or how to order!`
    );
    messagesArea.appendChild(welcomeMsg);
}

/**
 * Render session item in sidebar
 */
function renderSessionItem(session, isActive = false) {
    const item = document.createElement('div');
    item.className = `session-item ${isActive ? 'active' : ''}`;
    item.dataset.sessionId = session.id;

    // Content wrapper (clickable area)
    const content = document.createElement('div');
    content.className = 'session-content';
    content.onclick = () => loadSession(session.id);

    const title = document.createElement('div');
    title.className = 'session-title';
    title.textContent = `Chat ${session.id.substring(0, 8)}...`;

    const meta = document.createElement('div');
    meta.className = 'session-meta';
    meta.textContent = `${session.message_count} messages`;

    content.appendChild(title);
    content.appendChild(meta);

    // Delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'session-delete-btn';
    deleteBtn.innerHTML = '×';
    deleteBtn.title = 'Delete session';
    deleteBtn.onclick = (e) => {
        e.stopPropagation();
        deleteSession(session.id);
    };

    item.appendChild(content);
    item.appendChild(deleteBtn);
    return item;
}

/**
 * Group sessions by date
 */
function groupSessionsByDate(sessions) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const lastWeek = new Date(today);
    lastWeek.setDate(lastWeek.getDate() - 7);

    const groups = {
        today: [],
        yesterday: [],
        lastWeek: [],
        older: [],
    };

    sessions.forEach(session => {
        const sessionDate = new Date(session.created_at);
        const sessionDay = new Date(sessionDate.getFullYear(), sessionDate.getMonth(), sessionDate.getDate());

        if (sessionDay.getTime() === today.getTime()) {
            groups.today.push(session);
        } else if (sessionDay.getTime() === yesterday.getTime()) {
            groups.yesterday.push(session);
        } else if (sessionDay >= lastWeek) {
            groups.lastWeek.push(session);
        } else {
            groups.older.push(session);
        }
    });

    return groups;
}

/**
 * Render sessions list
 */
function renderSessionsList(sessions, currentSessionId) {
    const sessionsList = document.getElementById('sessionsList');
    sessionsList.innerHTML = '';

    const groups = groupSessionsByDate(sessions);

    const groupLabels = {
        today: 'Today',
        yesterday: 'Yesterday',
        lastWeek: 'Last 7 Days',
        older: 'Older',
    };

    for (const [key, label] of Object.entries(groupLabels)) {
        if (groups[key].length > 0) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'session-group';

            const labelDiv = document.createElement('div');
            labelDiv.className = 'group-label';
            labelDiv.textContent = label;

            groupDiv.appendChild(labelDiv);

            groups[key].forEach(session => {
                const isActive = session.id === currentSessionId;
                groupDiv.appendChild(renderSessionItem(session, isActive));
            });

            sessionsList.appendChild(groupDiv);
        }
    }
}

/**
 * Update connection status
 */
function updateConnectionStatus(isConnected) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    if (isConnected) {
        statusDot.classList.remove('offline');
        statusText.textContent = 'Connected';
    } else {
        statusDot.classList.add('offline');
        statusText.textContent = 'Offline';
    }
}

/**
 * Update session info in header
 */
function updateSessionInfo(sessionId) {
    const sessionIdElement = document.getElementById('currentSessionId');
    if (sessionId) {
        sessionIdElement.textContent = sessionId.substring(0, 8) + '...';
    } else {
        sessionIdElement.textContent = '---';
    }
}

/**
 * Update user name display
 */
function updateUserNameDisplay(name) {
    const sidebarUserName = document.getElementById('sidebarUserName');
    const settingsUserName = document.getElementById('settingsUserName');

    if (sidebarUserName) {
        sidebarUserName.textContent = name || 'Guest';
    }

    if (settingsUserName) {
        settingsUserName.value = name || '';
    }
}

/**
 * Clear messages area
 */
function clearMessages() {
    const messagesArea = document.getElementById('messagesArea');
    messagesArea.innerHTML = '';
}

/**
 * Load and render previous messages
 */
function renderMessages(messages) {
    const messagesArea = document.getElementById('messagesArea');

    messages.forEach(msg => {
        let messageElement;

        if (msg.role === 'user') {
            messageElement = renderUserMessage(msg.content);
        } else {
            messageElement = renderBotMessage(msg.content);
        }

        messagesArea.appendChild(messageElement);
    });

    scrollToBottom();
}
