/**
 * World-Class Responsive Navigation System
 * Handles sidebar toggle, mobile behavior, and accessibility
 */

class ResponsiveNavigation {
    constructor() {
        this.sidebar = null;
        this.toggleButton = null;
        this.backdrop = null;
        this.isExpanded = false;
        this.isMobile = false;
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeNavigation());
        } else {
            this.initializeNavigation();
        }
    }
    
    initializeNavigation() {
        // Get DOM elements
        this.sidebar = document.getElementById('page-sidebar');
        this.toggleButton = document.getElementById('page-sidebar-toggle');
        
        if (!this.sidebar || !this.toggleButton) {
            console.warn('Navigation elements not found');
            return;
        }
        
        // Create backdrop for mobile
        this.createBackdrop();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize state based on screen size
        this.handleResize();
        
        // Set initial accessibility attributes
        this.updateAccessibilityAttributes();
        
        console.log('✅ World-class responsive navigation initialized');
    }
    
    createBackdrop() {
        // Remove existing backdrop if present
        const existingBackdrop = document.querySelector('.sidebar-backdrop');
        if (existingBackdrop) {
            existingBackdrop.remove();
        }
        
        // Create new backdrop
        this.backdrop = document.createElement('div');
        this.backdrop.className = 'sidebar-backdrop';
        this.backdrop.setAttribute('role', 'presentation');
        document.body.appendChild(this.backdrop);
        
        // Add click listener to backdrop
        this.backdrop.addEventListener('click', () => {
            this.closeSidebar();
            // Ensure hamburger animation is reset when clicking outside
            this.toggleButton.classList.remove('active');
        });
    }
    
    setupEventListeners() {
        // Toggle button click
        this.toggleButton.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleSidebar();
            
            // Add visual feedback with the modern hamburger animation
            this.toggleButton.classList.toggle('active');
        });
        
        // Window resize
        window.addEventListener('resize', () => this.handleResize());
        
        // Navigation link clicks on mobile
        const navLinks = this.sidebar.querySelectorAll('.pf-v5-c-nav__link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                // Close sidebar on mobile when nav item is clicked
                if (this.isMobile && this.isExpanded) {
                    setTimeout(() => {
                        this.closeSidebar();
                        // Remove active state from toggle button
                        this.toggleButton.classList.remove('active');
                    }, 150); // Small delay for UX
                }
            });
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isExpanded && this.isMobile) {
                this.closeSidebar();
                // Reset hamburger animation when closing with ESC
                this.toggleButton.classList.remove('active');
            }
        });
        
        // Focus trap when sidebar is open on mobile
        this.sidebar.addEventListener('keydown', (e) => {
            if (e.key === 'Tab' && this.isMobile && this.isExpanded) {
                this.handleFocusTrap(e);
            }
        });
    }
    
    handleResize() {
        const wasExpanded = this.isExpanded;
        const wasMobile = this.isMobile;
        
        // Determine if we're in mobile/tablet mode
        this.isMobile = window.innerWidth < 1200;
        
        if (!this.isMobile) {
            // Desktop mode - always show sidebar
            this.isExpanded = true;
            this.sidebar.classList.add('pf-m-expanded');
            this.backdrop.classList.remove('active');
            
            // Reset hamburger animation on desktop
            this.toggleButton.classList.remove('active');
            
            document.body.style.overflow = '';
        } else {
            // Mobile/tablet mode - sidebar starts closed unless it was already open
            if (wasMobile === false) {
                // Just switched to mobile - close sidebar
                this.isExpanded = false;
                this.sidebar.classList.remove('pf-m-expanded');
                this.backdrop.classList.remove('active');
                this.toggleButton.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
        
        this.updateAccessibilityAttributes();
        
        // Log state changes in development
        if (wasExpanded !== this.isExpanded || wasMobile !== this.isMobile) {
            console.log(`📱 Navigation state: mobile=${this.isMobile}, expanded=${this.isExpanded}`);
        }
    }
    
    toggleSidebar() {
        if (!this.isMobile) {
            return; // Don't toggle on desktop
        }
        
        if (this.isExpanded) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    }
    
    openSidebar() {
        if (!this.isMobile) return;
        
        this.isExpanded = true;
        this.sidebar.classList.add('pf-m-expanded');
        this.backdrop.classList.add('active');
        
        // Add active state for hamburger animation
        this.toggleButton.classList.add('active');
        
        // Prevent body scroll on mobile
        document.body.style.overflow = 'hidden';
        
        // Focus first nav link for accessibility
        const firstNavLink = this.sidebar.querySelector('.pf-v5-c-nav__link');
        if (firstNavLink) {
            setTimeout(() => firstNavLink.focus(), 100);
        }
        
        this.updateAccessibilityAttributes();
        
        // Analytics/tracking
        this.trackEvent('sidebar_opened');
    }
    
    closeSidebar() {
        if (!this.isMobile) return;
        
        this.isExpanded = false;
        this.sidebar.classList.remove('pf-m-expanded');
        this.backdrop.classList.remove('active');
        
        // Remove active state from hamburger animation
        this.toggleButton.classList.remove('active');
        
        // Restore body scroll
        document.body.style.overflow = '';
        
        // Return focus to toggle button
        this.toggleButton.focus();
        
        this.updateAccessibilityAttributes();
        
        // Analytics/tracking
        this.trackEvent('sidebar_closed');
    }
    
    updateAccessibilityAttributes() {
        // Update toggle button
        this.toggleButton.setAttribute('aria-expanded', this.isExpanded.toString());
        
        // Update sidebar
        this.sidebar.setAttribute('aria-hidden', (!this.isExpanded && this.isMobile).toString());
        
        // Update toggle button text for screen readers
        const srText = this.isExpanded ? 'Close navigation' : 'Open navigation';
        this.toggleButton.setAttribute('aria-label', srText);
    }
    
    handleFocusTrap(e) {
        const focusableElements = this.sidebar.querySelectorAll(
            'a[href], button:not([disabled]), textarea:not([disabled]), input[type="text"]:not([disabled]), input[type="radio"]:not([disabled]), input[type="checkbox"]:not([disabled]), select:not([disabled])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    }
    
    trackEvent(eventName) {
        // Analytics tracking - replace with your analytics provider
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, {
                'event_category': 'navigation',
                'screen_size': this.isMobile ? 'mobile' : 'desktop'
            });
        }
        
        console.log(`📊 Navigation event: ${eventName}`);
    }
    
    // Public API methods
    getState() {
        return {
            isExpanded: this.isExpanded,
            isMobile: this.isMobile
        };
    }
    
    forceClose() {
        if (this.isMobile && this.isExpanded) {
            this.closeSidebar();
        }
    }
    
    forceOpen() {
        if (this.isMobile && !this.isExpanded) {
            this.openSidebar();
        }
    }
}

// Initialize navigation when script loads
const responsiveNavigation = new ResponsiveNavigation();

// Export for global access
window.ResponsiveNavigation = responsiveNavigation;

// Legacy support for existing code
window.toggleSidebar = () => responsiveNavigation.toggleSidebar();
window.closeSidebar = () => responsiveNavigation.forceClose();
window.openSidebar = () => responsiveNavigation.forceOpen();

// Handle page transitions (if using SPA or AJAX navigation)
window.addEventListener('beforeunload', () => {
    // Clean up any open states
    document.body.style.overflow = '';
});

// Advanced features for developer experience
// Add debug helpers for development (always available for easier debugging)
window.navDebug = {
    getState: () => responsiveNavigation.getState(),
    forceClose: () => responsiveNavigation.forceClose(),
    forceOpen: () => responsiveNavigation.forceOpen(),
    handleResize: () => responsiveNavigation.handleResize(),
    info: () => console.log('📱 Navigation Debug Info:', responsiveNavigation.getState())
};
