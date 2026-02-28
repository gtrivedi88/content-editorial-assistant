/**
 * Theme Manager — PF5 dark/light toggle with localStorage persistence.
 */

const STORAGE_KEY = 'cea-theme';
const DARK_CLASS = 'pf-v5-theme-dark';
const LIGHT_CLASS = 'pf-v5-theme-light';

class ThemeManager {
    constructor() {
        this._preference = localStorage.getItem(STORAGE_KEY) || 'auto';
    }

    init() {
        const toggleBtn = document.getElementById('cea-theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
        }

        // Watch system preference changes
        globalThis.matchMedia('(prefers-color-scheme: dark)')
            .addEventListener('change', (e) => {
                if (this._preference === 'auto') {
                    this._apply(e.matches ? 'dark' : 'light');
                }
            });

        this._updateIcon();
    }

    toggle() {
        const isDark = document.documentElement.classList.contains(DARK_CLASS);
        const next = isDark ? 'light' : 'dark';
        this._preference = next;
        localStorage.setItem(STORAGE_KEY, next);

        // Add transition class briefly
        document.documentElement.classList.add('cea-theme-transitioning');
        this._apply(next);
        setTimeout(() => {
            document.documentElement.classList.remove('cea-theme-transitioning');
        }, 350);
    }

    _apply(theme) {
        const root = document.documentElement;
        if (theme === 'dark') {
            root.classList.remove(LIGHT_CLASS);
            root.classList.add(DARK_CLASS);
        } else {
            root.classList.remove(DARK_CLASS);
            root.classList.add(LIGHT_CLASS);
        }
        this._updateIcon();
    }

    _updateIcon() {
        // Icon stays as circle-half-stroke (matches prototype).
        // No dynamic icon swap needed.
    }
}

export const themeManager = new ThemeManager();
