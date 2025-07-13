// Sidebar JavaScript for EduRAG Platform

// Sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
});

function initializeSidebar() {
    // Initialize sidebar sections
    initializeSidebarSections();
    
    // Set up auto-refresh for dynamic content
    setupSidebarAutoRefresh();
}

function initializeSidebarSections() {
    // Add click handlers for sidebar buttons
    const sidebarButtons = document.querySelectorAll('.sidebar-btn');
    sidebarButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Add loading state
            this.disabled = true;
            const originalText = this.textContent;
            this.textContent = 'Loading...';
            
            // Re-enable after a short delay
            setTimeout(() => {
                this.disabled = false;
                this.textContent = originalText;
            }, 2000);
        });
    });
    
    // Initialize collapsible sections (if needed)
    const sectionHeaders = document.querySelectorAll('.sidebar-section-header');
    sectionHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const section = this.closest('.sidebar-section');
            const content = section.querySelector('.sidebar-section-content');
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                this.classList.remove('collapsed');
            } else {
                content.style.display = 'none';
                this.classList.add('collapsed');
            }
        });
    });
}

function setupSidebarAutoRefresh() {
    // Auto-refresh session stats every 30 seconds
    setInterval(() => {
        updateSessionStatsDisplay();
    }, 30000);
    
    // Auto-refresh system status every 10 seconds
    setInterval(() => {
        updateSystemStatus();
    }, 10000);
}

function updateSessionStatsDisplay() {
    // This would typically fetch updated stats from the server
    // For now, we'll just update the display with current values
    const questionsAsked = document.getElementById('questionsAsked');
    const avgResponseTime = document.getElementById('avgResponseTime');
    const avgRating = document.getElementById('avgRating');
    const sourcesUsed = document.getElementById('sourcesUsed');
    
    // Update with current values (in a real app, this would come from the server)
    if (questionsAsked) {
        const current = parseInt(questionsAsked.textContent) || 0;
        questionsAsked.textContent = current;
    }
    
    if (avgResponseTime) {
        const current = avgResponseTime.textContent;
        avgResponseTime.textContent = current;
    }
    
    if (avgRating) {
        const current = avgRating.textContent;
        avgRating.textContent = current;
    }
    
    if (sourcesUsed) {
        const current = parseInt(sourcesUsed.textContent) || 0;
        sourcesUsed.textContent = current;
    }
}

function updateSystemStatus() {
    // Check system status and update indicators
    const statusIndicators = document.querySelectorAll('.status-indicator');
    
    statusIndicators.forEach(indicator => {
        // Simulate status check (in a real app, this would ping the server)
        const isOnline = Math.random() > 0.1; // 90% chance of being online
        
        if (isOnline) {
            indicator.className = 'status-indicator status-online';
        } else {
            indicator.className = 'status-indicator status-offline';
        }
    });
}

// Sidebar-specific utility functions
function toggleSidebarSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        const content = section.querySelector('.sidebar-section-content');
        const header = section.querySelector('.sidebar-section-header');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            header.classList.remove('collapsed');
        } else {
            content.style.display = 'none';
            header.classList.add('collapsed');
        }
    }
}

function refreshSidebarContent() {
    // Refresh all sidebar content
    loadTopics();
    loadMetrics();
    loadHistory();
    updateSessionStatsDisplay();
    updateSystemStatus();
}

// Sidebar responsive behavior
function handleSidebarResponsive() {
    const sidebar = document.querySelector('.sidebar');
    const chatLayout = document.querySelector('.chat-layout');
    
    if (window.innerWidth <= 768) {
        // Mobile layout
        if (sidebar && chatLayout) {
            sidebar.style.flexDirection = 'row';
            sidebar.style.overflowX = 'auto';
            chatLayout.style.gridTemplateColumns = '1fr';
        }
    } else {
        // Desktop layout
        if (sidebar && chatLayout) {
            sidebar.style.flexDirection = 'column';
            sidebar.style.overflowX = 'visible';
            chatLayout.style.gridTemplateColumns = '1fr 350px';
        }
    }
}

// Listen for window resize
window.addEventListener('resize', handleSidebarResponsive);

// Initialize responsive behavior on load
document.addEventListener('DOMContentLoaded', function() {
    handleSidebarResponsive();
});

// Sidebar keyboard navigation
function setupSidebarKeyboardNav() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    
    sidebar.addEventListener('keydown', function(e) {
        const focusableElements = sidebar.querySelectorAll('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.key === 'Tab') {
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
    });
}

// Initialize keyboard navigation
document.addEventListener('DOMContentLoaded', function() {
    setupSidebarKeyboardNav();
});

// Sidebar performance optimization
function optimizeSidebarPerformance() {
    // Use Intersection Observer to lazy load sidebar content
    const sidebarSections = document.querySelectorAll('.sidebar-section');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const section = entry.target;
                const content = section.querySelector('.sidebar-section-content');
                
                // Load content when section becomes visible
                if (content && !content.dataset.loaded) {
                    loadSectionContent(section);
                    content.dataset.loaded = 'true';
                }
            }
        });
    }, {
        threshold: 0.1
    });
    
    sidebarSections.forEach(section => {
        observer.observe(section);
    });
}

function loadSectionContent(section) {
    const sectionId = section.id;
    
    switch (sectionId) {
        case 'topics-panel':
            loadTopics();
            break;
        case 'metrics-panel':
            loadMetrics();
            break;
        case 'history-panel':
            loadHistory();
            break;
        default:
            break;
    }
}

// Initialize performance optimization
document.addEventListener('DOMContentLoaded', function() {
    optimizeSidebarPerformance();
}); 