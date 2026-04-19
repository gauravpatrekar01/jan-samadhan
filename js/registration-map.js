/**
 * Registration Form Script with Map Integration
 * Handles form validation, map initialization, and complaint submission
 */

let mapManager = null;

// Initialize form on page load
document.addEventListener('DOMContentLoaded', async () => {
    initializeMap();
    setupFormListeners();
    loadUserData();
});

/**
 * Initialize Leaflet map for location selection
 */
async function initializeMap() {
    const mapContainer = document.getElementById('registrationMap');
    if (!mapContainer) return;

    // Initialize MapManager
    mapManager = new MapManager('registrationMap', {
        defaultZoom: 13,
        defaultCity: 'Nashik',
        defaultLat: 19.9975,
        defaultLng: 73.7898,
        markerColor: '#4f46e5'
    });

    console.log('✓ Map initialized');
}

/**
 * Setup form event listeners
 */
function setupFormListeners() {
    const form = document.getElementById('grievanceForm');
    const descInput = document.getElementById('fDescription');
    const priorityRadios = document.querySelectorAll('input[name="priority"]');

    // Description character counter
    if (descInput) {
        descInput.addEventListener('input', (e) => {
            const count = e.target.value.length;
            const counter = document.getElementById('descCount');
            if (counter) {
                counter.textContent = `${count} / 500`;
                counter.style.color = count > 400 ? 'var(--danger)' : 'var(--text-muted)';
            }
        });
    }

    // Priority hint
    priorityRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const hints = {
                'Low': '🟢 Expected resolution in 7–10 days.',
                'Medium': '🟠 Expected resolution in 3–5 days.',
                'High': '🔴 Expected resolution in 24–48 hours.',
                'Emergency': '🚨 Expected resolution in less than 24 hours.'
            };
            const hint = document.getElementById('priorityHint');
            if (hint) {
                hint.textContent = `ℹ️ ${hints[e.target.value] || ''}`;
            }
        });
    });

    // Form submission
    form.addEventListener('submit', (e) => submitGrievance(e));
}

/**
 * Load user data from session/JWT
 */
async function loadUserData() {
    try {
        const token = sessionStorage.getItem('token') || localStorage.getItem('token');
        if (!token) return;

        const response = await fetch(`${API_BASE_URL}/api/auth/user`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.email) document.getElementById('fEmail').value = data.email;
            if (data.name) document.getElementById('fName').value = data.name;
        }
    } catch (error) {
        console.log('Could not auto-load user data');
    }
}

/**
 * Select complaint category
 */
function selectCategory(element) {
    document.querySelectorAll('.cat-icon-btn').forEach(btn => btn.classList.remove('selected'));
    element.classList.add('selected');
    document.getElementById('fCategory').value = element.dataset.cat;
}

/**
 * Preview image upload
 */
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('imgPreview');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

/**
 * Toggle dark mode
 */
function toggleDark() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

/**
 * Toggle mobile navigation
 */
function toggleMobileNav() {
    const mobileNav = document.getElementById('mobileNav');
    if (mobileNav) {
        mobileNav.style.display = mobileNav.style.display === 'flex' ? 'none' : 'flex';
    }
}

/**
 * Validate form inputs
 */
function validateForm() {
    const errors = {};

    // Personal Info
    const name = document.getElementById('fName').value.trim();
    if (!name || name.length < 3) {
        errors.name = 'Full name is required (minimum 3 characters)';
    }

    const email = document.getElementById('fEmail').value.trim();
    if (!email || !email.includes('@')) {
        errors.email = 'Valid email is required';
    }

    const contact = document.getElementById('fContact').value.trim();
    if (!contact || contact.length !== 10 || !/^\d{10}$/.test(contact)) {
        errors.contact = 'Valid 10-digit contact number is required';
    }

    // Complaint Details
    const category = document.getElementById('fCategory').value;
    if (!category) {
        errors.cat = 'Please select a category';
    }

    const description = document.getElementById('fDescription').value.trim();
    if (!description || description.length < 10) {
        errors.desc = 'Description must be at least 10 characters';
    }

    const priority = document.querySelector('input[name="priority"]:checked');
    if (!priority) {
        errors.priority = 'Please select a priority level';
    }

    // Location
    const location = mapManager?.getSelectedLocation();
    if (!location || !location.latitude || !location.longitude) {
        errors.location = 'Please mark your location on the map';
    }

    // Consent
    const consent = document.getElementById('fConsent').checked;
    if (!consent) {
        errors.consent = 'You must agree to the consent';
    }

    // Display errors
    clearErrors();
    Object.keys(errors).forEach(key => {
        const errorDiv = document.getElementById(`err_${key}`);
        if (errorDiv) {
            errorDiv.textContent = errors[key];
            errorDiv.style.display = 'block';
        }
    });

    return Object.keys(errors).length === 0;
}

/**
 * Clear error messages
 */
function clearErrors() {
    document.querySelectorAll('.form-error').forEach(el => {
        el.textContent = '';
        el.style.display = 'none';
    });
}

/**
 * Submit grievance
 */
async function submitGrievance(event) {
    event.preventDefault();

    if (!validateForm()) {
        showToast('Please fix the errors in the form', 'error');
        return;
    }

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '⏳ Submitting...';

    try {
        const token = sessionStorage.getItem('token') || localStorage.getItem('token');
        if (!token) {
            showToast('Please login before submitting a grievance', 'error');
            window.location.href = 'index.html';
            return;
        }

        // Get form data
        const location = mapManager.getSelectedLocation();
        const complaintData = {
            title: `${document.getElementById('fSubcategory').value || document.getElementById('fCategory').value}`,
            category: document.getElementById('fCategory').value,
            subcategory: document.getElementById('fSubcategory').value,
            priority: document.querySelector('input[name="priority"]:checked').value.toLowerCase(),
            description: document.getElementById('fDescription').value,
            location: document.getElementById('fAddress').value || `${location.latitude}, ${location.longitude}`,
            region: document.getElementById('fRegion').value || 'Not specified',
            latitude: location.latitude,
            longitude: location.longitude
        };

        // Validate title
        if (!complaintData.title || complaintData.title.length < 5) {
            complaintData.title = `${complaintData.category} Complaint`;
        }

        console.log('Submitting complaint:', complaintData);

        // Submit to backend
        const response = await fetch(`${API_BASE_URL}/api/complaints/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(complaintData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to submit complaint');
        }

        const result = await response.json();
        const complaintId = result.data?.id || result.data?._id || 'JSM-XXXX';

        // Show success
        showSuccess(complaintId);
        
    } catch (error) {
        console.error('Submission error:', error);
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '📤 Submit Grievance';
    }
}

/**
 * Show success overlay
 */
function showSuccess(complaintId) {
    const successOverlay = document.getElementById('successOverlay');
    const successID = document.getElementById('successID');
    
    if (successID) {
        successID.textContent = complaintId || 'JSM-2026-XXXX';
    }

    if (successOverlay) {
        successOverlay.classList.add('show');
    }

    // Reset form
    document.getElementById('grievanceForm').reset();
    if (mapManager) {
        mapManager.clearComplaintMarkers();
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div style="display: flex; gap: 12px; align-items: center;">
            <span>${type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️'}</span>
            <span>${message}</span>
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slide-out 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/**
 * Handle map search
 */
async function searchLocation() {
    const searchInput = document.querySelector('.location-search-input');
    if (!searchInput || !searchInput.value || !mapManager) return;

    const result = await mapManager.searchLocation(searchInput.value);
    if (result) {
        showToast(`Location found: ${result.name}`, 'success');
    } else {
        showToast('Location not found. Please try another search.', 'error');
    }
}

// Add keyboard support for location search
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('.location-search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchLocation();
            }
        });
    }
});

// Update form preview
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('grievanceForm');
    if (form) {
        form.addEventListener('change', updateFormPreview);
        form.addEventListener('input', updateFormPreview);
    }
});

function updateFormPreview() {
    const preview = document.getElementById('formPreview');
    if (!preview) return;

    const category = document.getElementById('fCategory').value;
    const priority = document.querySelector('input[name="priority"]:checked')?.value;
    const address = document.getElementById('fAddress').value;
    const location = mapManager?.getSelectedLocation();

    let content = '<div style="font-size: 0.82rem;">';
    if (category) content += `<div>📋 <strong>${category}</strong></div>`;
    if (priority) content += `<div>⚡ Priority: ${priority}</div>`;
    if (address) content += `<div>📍 ${address}</div>`;
    if (location?.latitude) content += `<div>🗺️ Coordinates: ${location.latitudeFormatted}, ${location.longitudeFormatted}</div>`;
    content += '</div>';

    if (content.includes('div') && content.split('div').length > 3) {
        preview.innerHTML = content;
    }
}

// Page loader
window.addEventListener('load', () => {
    const loader = document.getElementById('pageLoader');
    if (loader) {
        setTimeout(() => {
            loader.style.opacity = '0';
            setTimeout(() => {
                loader.style.display = 'none';
            }, 300);
        }, 500);
    }
});
