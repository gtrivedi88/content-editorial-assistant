document.addEventListener('DOMContentLoaded', function() {
    // Add click feedback for active cards
    const activeCards = document.querySelectorAll('.option-card:not(.coming-soon)');
    
    activeCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Add a subtle scale animation on click
            this.style.transform = 'translateY(-4px) scale(0.98)';
            
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
        
        // Add keyboard support
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });

    // Add hover sound effect (subtle, optional)
    const cards = document.querySelectorAll('.option-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            // Subtle visual feedback - the CSS handles the main animation
            // This is where you could add a very subtle audio cue if desired
        });
    });
});