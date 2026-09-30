// Enhanced scroll-triggered animations for landing page

document.addEventListener('DOMContentLoaded', function() {
    // Enhanced Intersection Observer with better options
    const observerOptions = {
        threshold: 0.15,  // Trigger when 15% of element is visible
        rootMargin: '0px 0px -100px 0px'  // Trigger slightly before element enters viewport
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add visible class with animation
                entry.target.classList.add('visible');
                
                // Add stagger delay for multiple elements
                const siblings = Array.from(entry.target.parentElement.children);
                const index = siblings.indexOf(entry.target);
                if (index > 0) {
                    entry.target.style.transitionDelay = `${index * 0.1}s`;
                }
            }
        });
    }, observerOptions);

    // Make hero section visible immediately (no animation needed)
    document.querySelectorAll('.hero-section .fade-in-left, .hero-section .fade-in-right, .hero-section .fade-in-up').forEach(el => {
        el.classList.add('visible');
        el.style.opacity = '1';
        el.style.transform = 'translateY(0) translateX(0) scale(1)';
    });
    
    // Observe all other elements with animation classes for scroll animations
    document.querySelectorAll('.fade-in-up, .fade-in-left, .fade-in-right').forEach(el => {
        // Skip hero section elements - they're already visible
        if (!el.closest('.hero-section')) {
            observer.observe(el);
        }
    });

    // Subtle parallax effect for hero section (without fading out)
    const hero = document.querySelector('.hero-section');
    if (hero) {
        let ticking = false;
        window.addEventListener('scroll', () => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    const scrolled = window.pageYOffset;
                    // Only apply subtle parallax, don't fade out
                    const rate = scrolled * 0.1;
                    hero.style.transform = `translateY(${rate}px)`;
                    // Keep hero visible - don't fade out
                    hero.style.opacity = '1';
                    ticking = false;
                });
                ticking = true;
            }
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
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

    // Navbar background on scroll - ensure it stays visible
    const navbar = document.querySelector('.sticky-nav');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
                navbar.style.backgroundColor = 'rgba(255, 255, 255, 0.98)';
                navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.05)';
            } else {
                navbar.classList.remove('scrolled');
                navbar.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                navbar.style.boxShadow = 'none';
            }
        });
        
        // Ensure navbar is always visible
        navbar.style.position = 'sticky';
        navbar.style.top = '0';
        navbar.style.zIndex = '1000';
    }

    // Add hover animations to cards
    document.querySelectorAll('.card, .feature-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Animate numbers/counters
    function animateValue(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const current = Math.floor(progress * (end - start) + start);
            element.textContent = current.toLocaleString();
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Animate stats when they come into view
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.classList.contains('animated')) {
                entry.target.classList.add('animated');
                const targetValue = parseInt(entry.target.textContent.replace(/[^0-9]/g, ''));
                if (targetValue > 0) {
                    animateValue(entry.target, 0, targetValue, 1000);
                }
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.text-2xl.font-bold, .text-3xl.font-bold').forEach(stat => {
        if (stat.textContent.match(/^\d/)) {
            statsObserver.observe(stat);
        }
    });
});
