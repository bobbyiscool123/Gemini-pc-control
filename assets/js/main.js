/**
 * Gemini PC Control - Main JavaScript
 * Handles interactive elements and Material Design component initialization
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Material Design components
    initializeMDC();
    
    // Initialize tabs
    initializeTabs();
    
    // Add scroll animation for navigation links
    initializeSmoothScroll();
    
    // Add header shadow on scroll
    initializeHeaderScroll();
});

/**
 * Initialize Material Design components
 */
function initializeMDC() {
    // Initialize all buttons
    const buttons = document.querySelectorAll('.mdc-button');
    buttons.forEach(button => {
        mdc.ripple.MDCRipple.attachTo(button);
    });
    
    // Initialize top app bar
    const topAppBarElement = document.querySelector('.mdc-top-app-bar');
    if (topAppBarElement) {
        const topAppBar = mdc.topAppBar.MDCTopAppBar.attachTo(topAppBarElement);
    }
    
    // Initialize tab bar
    const tabBar = document.querySelector('.mdc-tab-bar');
    if (tabBar) {
        const tabBarComponent = mdc.tabBar.MDCTabBar.attachTo(tabBar);
        
        // Add tab selection handler
        tabBarComponent.listen('MDCTabBar:activated', (event) => {
            const tabIndex = event.detail.index;
            
            // Find all tab content elements
            const tabContents = document.querySelectorAll('.tab-content');
            
            // Hide all tab contents
            tabContents.forEach(content => {
                content.classList.remove('tab-content--active');
            });
            
            // Show the selected tab content
            if (tabContents[tabIndex]) {
                tabContents[tabIndex].classList.add('tab-content--active');
            }
        });
    }
    
    // Initialize all list items
    const listItems = document.querySelectorAll('.mdc-list-item');
    listItems.forEach(item => {
        mdc.ripple.MDCRipple.attachTo(item);
    });
}

/**
 * Initialize tabs functionality
 */
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.mdc-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Show the first tab by default
    if (tabContents.length > 0) {
        tabContents[0].classList.add('tab-content--active');
    }
    
    tabButtons.forEach((button, index) => {
        button.addEventListener('click', () => {
            // Update active state for tab buttons
            tabButtons.forEach(btn => {
                btn.classList.remove('mdc-tab--active');
                btn.setAttribute('aria-selected', 'false');
                
                // Get the tab indicator element
                const indicator = btn.querySelector('.mdc-tab-indicator');
                indicator.classList.remove('mdc-tab-indicator--active');
            });
            
            // Set active state for the clicked tab
            button.classList.add('mdc-tab--active');
            button.setAttribute('aria-selected', 'true');
            
            // Get the tab indicator element
            const indicator = button.querySelector('.mdc-tab-indicator');
            indicator.classList.add('mdc-tab-indicator--active');
            
            // Hide all tab contents
            tabContents.forEach(content => {
                content.classList.remove('tab-content--active');
            });
            
            // Show the corresponding tab content
            if (tabContents[index]) {
                tabContents[index].classList.add('tab-content--active');
            }
        });
    });
}

/**
 * Add smooth scrolling for navigation links
 */
function initializeSmoothScroll() {
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Only process internal links
            if (this.getAttribute('href').startsWith('#')) {
                const targetId = this.getAttribute('href');
                
                // Skip if it's just "#" (empty)
                if (targetId === '#') {
                    return;
                }
                
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    e.preventDefault();
                    
                    // Get the header height for offset
                    const headerHeight = document.querySelector('.mdc-top-app-bar')?.offsetHeight || 0;
                    
                    // Scroll to the element with offset
                    window.scrollTo({
                        top: targetElement.offsetTop - headerHeight - 20,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
}

/**
 * Add shadow to header on scroll
 */
function initializeHeaderScroll() {
    const header = document.querySelector('.mdc-top-app-bar');
    
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 10) {
                header.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
            } else {
                header.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
            }
        });
    }
}

/**
 * Animation for sections when they become visible
 */
function animateSections() {
    const sections = document.querySelectorAll('section');
    
    // Create an Intersection Observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('section-visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    // Observe each section
    sections.forEach(section => {
        observer.observe(section);
    });
} 