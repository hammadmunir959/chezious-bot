/**
 * Application State Management
 */

class AppState {
    constructor() {
        this.state = {
            user: {
                id: null,
                name: null,
                city: null,
            },
            currentSession: {
                id: null,
                created_at: null,
                message_count: 0,
                status: 'active',
            },
            sessions: [],
            messages: [],
            ui: {
                sidebarOpen: window.innerWidth > 1024,
                isTyping: false,
                isConnected: false,
                settingsOpen: false,
                isSending: false,
            },
        };

        this.listeners = [];
    }

    /**
     * Update state and notify listeners
     */
    setState(updates) {
        this.state = this.deepMerge(this.state, updates);
        this.notify();
    }

    /**
     * Deep merge objects
     */
    deepMerge(target, source) {
        const output = { ...target };

        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                output[key] = this.deepMerge(target[key] || {}, source[key]);
            } else {
                output[key] = source[key];
            }
        }

        return output;
    }

    /**
     * Subscribe to state changes
     */
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    /**
     * Notify all listeners
     */
    notify() {
        this.listeners.forEach(listener => listener(this.state));
    }

    /**
     * Get current state
     */
    getState() {
        return this.state;
    }
}

// Create global state instance
const appState = new AppState();
