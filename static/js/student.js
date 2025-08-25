// Student dashboard JavaScript functionality

// Auto-refresh functionality
let refreshInterval;
const REFRESH_INTERVAL = 30000; // 30 seconds

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Start auto-refresh
    startAutoRefresh();
    
    // Add click handlers for manual refresh
    const refreshButton = document.querySelector('button[onclick="refreshData()"]');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshData);
    }
    
    // Show last update time
    updateLastRefreshTime();
    
    // Add visibility change listener to pause/resume refresh
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopAutoRefresh();
        } else {
            startAutoRefresh();
            refreshData(); // Refresh immediately when page becomes visible
        }
    });
});

// Start auto-refresh timer
function startAutoRefresh() {
    stopAutoRefresh(); // Clear any existing interval
    refreshInterval = setInterval(refreshData, REFRESH_INTERVAL);
}

// Stop auto-refresh timer
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Manual refresh function
function refreshData() {
    const refreshButton = document.querySelector('button[onclick="refreshData()"]');
    const updatesDiv = document.getElementById('realtime-updates');
    
    // Show loading state
    if (refreshButton) {
        showLoading(refreshButton);
    }
    
    if (updatesDiv) {
        updatesDiv.innerHTML = '<i class="fas fa-sync-alt fa-spin me-2"></i>Refreshing location data...';
        updatesDiv.className = 'alert alert-info';
    }
    
    // Reload the page to get fresh data
    setTimeout(() => {
        window.location.reload();
    }, 1000);
}

// Update last refresh time display
function updateLastRefreshTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    const updatesDiv = document.getElementById('realtime-updates');
    
    if (updatesDiv && !updatesDiv.innerHTML.includes('fa-spin')) {
        updatesDiv.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            Last updated: ${timeString} - Next refresh in ${REFRESH_INTERVAL/1000} seconds
        `;
    }
}

// Show loading state for buttons
function showLoading(button) {
    const originalHTML = button.innerHTML;
    button.setAttribute('data-original', originalHTML);
    button.innerHTML = '<i class="fas fa-sync-alt fa-spin me-2"></i>Refreshing...';
    button.disabled = true;
}

// Hide loading state for buttons
function hideLoading(button) {
    const originalHTML = button.getAttribute('data-original');
    if (originalHTML) {
        button.innerHTML = originalHTML;
        button.removeAttribute('data-original');
    }
    button.disabled = false;
}

// Update countdown timer
function updateCountdown() {
    const countdownElements = document.querySelectorAll('[data-countdown]');
    countdownElements.forEach(element => {
        let seconds = parseInt(element.getAttribute('data-countdown'));
        if (seconds > 0) {
            seconds--;
            element.setAttribute('data-countdown', seconds);
            element.textContent = `Next refresh in ${seconds} seconds`;
        }
    });
}

// Animate station status updates
function animateStationUpdate(stationElement, newStatus) {
    stationElement.style.transition = 'all 0.5s ease';
    stationElement.style.transform = 'scale(1.05)';
    
    setTimeout(() => {
        stationElement.style.transform = 'scale(1)';
        stationElement.className = `station-item d-flex align-items-center mb-3 p-2 rounded status-${newStatus}`;
    }, 500);
}

// Handle connection status
function updateConnectionStatus(isOnline) {
    const updatesDiv = document.getElementById('realtime-updates');
    if (!updatesDiv) return;
    
    if (isOnline) {
        updatesDiv.innerHTML = '<i class="fas fa-wifi me-2"></i>Connected - Real-time updates active';
        updatesDiv.className = 'alert alert-success';
    } else {
        updatesDiv.innerHTML = '<i class="fas fa-wifi-slash me-2"></i>Connection lost - Updates paused';
        updatesDiv.className = 'alert alert-warning';
    }
}

// Monitor network status
window.addEventListener('online', () => updateConnectionStatus(true));
window.addEventListener('offline', () => updateConnectionStatus(false));

// Format time ago
function timeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now - time) / 1000);
    
    if (diffInSeconds < 60) {
        return `${diffInSeconds} seconds ago`;
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
}

// Update relative timestamps
function updateTimestamps() {
    const timestampElements = document.querySelectorAll('[data-timestamp]');
    timestampElements.forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
        element.textContent = timeAgo(timestamp);
    });
}

// Smooth scroll to student's station
function scrollToMyStation() {
    const myStation = document.querySelector('[data-my-station="true"]');
    if (myStation) {
        myStation.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
        
        // Highlight the station temporarily
        myStation.style.backgroundColor = 'rgba(var(--bs-primary-rgb), 0.2)';
        setTimeout(() => {
            myStation.style.backgroundColor = '';
        }, 2000);
    }
}

// Initialize tooltips if Bootstrap is available
if (typeof bootstrap !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    });
}

// Emergency contact functionality
function callDriver() {
    const driverPhone = document.querySelector('[data-driver-phone]');
    if (driverPhone) {
        const phone = driverPhone.getAttribute('data-driver-phone');
        window.location.href = `tel:${phone}`;
    }
}

// Share location functionality
function shareLocation() {
    if (navigator.share && navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            navigator.share({
                title: 'My Location',
                text: 'I am currently here:',
                url: `https://maps.google.com/?q=${position.coords.latitude},${position.coords.longitude}`
            });
        });
    } else {
        alert('Location sharing not supported on this device');
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});
