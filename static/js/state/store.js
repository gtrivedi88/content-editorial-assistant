/**
 * Reactive State Store — Pub/Sub pattern.
 * Components subscribe to specific state keys and re-render when those keys change.
 */

class Store {
    constructor() {
        this._state = {
            // Content
            content: '',
            formatHint: 'auto',
            detectedFormat: null,  // { format, confidence, markers } from auto-detection
            contentType: 'concept',

            // Analysis lifecycle
            analysisStatus: 'idle', // idle | uploading | analyzing | partial | complete | error
            analysisResult: null,
            errors: [],
            structuralBlocks: [],
            readability: null,
            statistics: null,

            // UI state
            selectedErrorId: null,
            activeGroup: 'all',        // 'all' | group key
            filteredErrors: [],
            dismissedErrors: new Set(),
            resolvedErrors: new Set(),

            // Progress
            progressSteps: [],
            progressPercent: 0,
            stageProgress: null,

            // Session
            sessionId: null,

            // Score
            qualityScore: 0,

            // Error message
            errorMessage: null,

            // Analysis tracking for request cancellation
            currentAnalysisId: null,
        };

        this._subscribers = new Map();
    }

    getState() {
        return this._state;
    }

    get(key) {
        return this._state[key];
    }

    setState(partial) {
        const prev = { ...this._state };
        Object.assign(this._state, partial);

        for (const key of Object.keys(partial)) {
            if (this._subscribers.has(key)) {
                for (const cb of this._subscribers.get(key)) {
                    try {
                        cb(this._state[key], prev[key]);
                    } catch (err) {
                        console.error(`[Store] Error in subscriber for "${key}":`, err);
                    }
                }
            }
        }
    }

    /**
     * Subscribe to changes on a specific state key.
     * @returns {Function} unsubscribe function
     */
    subscribe(key, callback) {
        if (!this._subscribers.has(key)) {
            this._subscribers.set(key, new Set());
        }
        this._subscribers.get(key).add(callback);
        return () => this._subscribers.get(key).delete(callback);
    }
}

export const store = new Store();
