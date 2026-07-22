// Smooth scrolling for navigation links
document.querySelectorAll('nav ul li a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Animate stats on scroll (optional)
const stats = document.querySelectorAll('.stat h3');
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, { threshold: 0.5 });

stats.forEach(stat => {
    stat.style.opacity = '0';
    stat.style.transform = 'translateY(20px)';
    stat.style.transition = 'all 0.5s ease';
    observer.observe(stat);
});

// Console welcome message
console.log('🎵 VCBotY Music - Made by Turki (the best)');
console.log('📡 Join our Discord: https://discord.gg/48wfDUXF8J');

// Button click tracking (optional)
document.querySelectorAll('.btn, .btn-join').forEach(button => {
    button.addEventListener('click', function() {
        console.log('🔗 Clicked:', this.textContent.trim());
    });
});

// Add a little Easter egg on the page
document.addEventListener('DOMContentLoaded', () => {
    const heroTitle = document.querySelector('.hero-content h1');
    if (heroTitle) {
        heroTitle.addEventListener('click', () => {
            alert('🎵 Made by Turki (the best)! 💪');
        });
    }
});
