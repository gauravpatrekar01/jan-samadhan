/**
 * Registration Form Script with Map Integration
 * Handles form validation, map initialization, and complaint submission
 */

let mapManager = null;

// API Base URL configuration
const REGISTRATION_API_BASE_URL = (() => {
    if (!window.location.hostname || window.location.hostname === '') {
        // Local file (file://) - default to localhost:8000
        return 'http://localhost:8000';
    }
    // For any other hostname, assume same host with port 8000
    return `http://${window.location.hostname}:8000`;
})();

console.log("📡 Registration API Base URL:", REGISTRATION_API_BASE_URL);

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

    // Form submission is already wired inline in `register.html` via onsubmit.
    // Avoid double submission (inline handler + JS listener) which can trigger duplicate API calls.
}

/**
 * Load user data from session/JWT
 */
async function loadUserData() {
    try {
        const token = sessionStorage.getItem('token') || localStorage.getItem('token');
        if (!token) return;

        const response = await fetch(`${REGISTRATION_API_BASE_URL}/api/auth/user`, {
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
    clearErrors();
    const errors = {};
    
    console.log('🔍 Starting form validation...');
    
    // Get form values
    const title = document.getElementById('fSubcategory')?.value || document.getElementById('fCategory')?.value;
    const category = document.getElementById('fCategory')?.value;
    const description = document.getElementById('fDescription')?.value;
    const priority = document.querySelector('input[name="priority"]:checked')?.value;
    const location = document.getElementById('fAddress')?.value;
    const region = document.getElementById('fRegion')?.value;
    
    console.log('📋 Form values:', {
        title, category, description, priority, location, region,
        descriptionLength: description?.length || 0
    });
    
    // Title validation
    if (!title || title.trim().length < 5) {
        errors.title = 'Title must be at least 5 characters long';
        console.error('❌ Title validation failed:', title);
    }
    
    // Description validation
    if (!description || description.trim().length < 10) {
        errors.description = 'Description must be at least 10 characters long';
        console.error('❌ Description validation failed:', description?.length || 0);
    } else if (description.trim().length > 2000) {
        errors.description = 'Description must be less than 2000 characters';
        console.error('❌ Description too long:', description.length);
    }
    
    // Priority validation
    if (!priority) {
        errors.priority = 'Please select a priority level';
        console.error('❌ Priority validation failed');
    }
    
    // Location validation
    if (!location || location.trim().length < 5) {
        errors.location = 'Please provide a valid location (minimum 5 characters)';
        console.error('❌ Location validation failed:', location);
    }
    
    // Region validation
    if (!region || region.trim() === '') {
        errors.region = 'Please select a region';
        console.error('❌ Region validation failed:', region);
    }
    
    // Check map location
    const mapLocation = mapManager?.getSelectedLocation();
    if (!mapLocation || !mapLocation.latitude || !mapLocation.longitude) {
        errors.map = 'Please mark the location on the map';
        console.error('❌ Map location validation failed');
    }
    
    // Display errors
    Object.keys(errors).forEach(field => {
        const errorEl = document.getElementById(`err_${field}`);
        if (errorEl) {
            errorEl.textContent = errors[field];
            errorEl.style.display = 'block';
            errorEl.style.color = 'var(--danger)';
        }
    });
    
    const isValid = Object.keys(errors).length === 0;
    console.log('✅ Form validation result:', isValid ? 'PASSED' : 'FAILED');
    if (!isValid) {
        console.log('🚨 Validation errors:', errors);
    }
    
    return isValid;
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
 * Submit grievance with enhanced error handling
 */
async function submitGrievance(event) {
    event.preventDefault();
    
    console.log('🚀 Starting complaint submission process...');
    
    if (!validateForm()) {
        console.log('❌ Form validation failed - aborting submission');
        showToast('Please fix the errors in the form', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '⏳ Submitting...';

    try {
        // Check authentication
        const token = sessionStorage.getItem('token') || localStorage.getItem('token');
        if (!token) {
            console.error('❌ No authentication token found');
            showToast('Please login before submitting a grievance', 'error');
            setTimeout(() => window.location.href = 'index.html', 2000);
            return;
        }
        
        console.log('✅ Authentication token found:', token.substring(0, 20) + '...');

        // Get form data with validation
        const location = mapManager?.getSelectedLocation();
        if (!location || !location.latitude || !location.longitude) {
            throw new Error('Please mark the location on the map');
        }
        
        const complaintData = {
            title: document.getElementById('fSubcategory')?.value || document.getElementById('fCategory')?.value || 'General Complaint',
            category: document.getElementById('fCategory')?.value,
            subcategory: document.getElementById('fSubcategory')?.value || '',
            priority: document.querySelector('input[name="priority"]:checked')?.value.toLowerCase() || 'medium',
            description: document.getElementById('fDescription')?.value,
            location: document.getElementById('fAddress')?.value || `${location.latitude}, ${location.longitude}`,
            region: document.getElementById('fRegion')?.value || 'Not specified',
            latitude: location.latitude,
            longitude: location.longitude,
            media: []
        };

        // Validate required fields
        const requiredFields = ['title', 'category', 'description', 'location', 'region'];
        const missingFields = requiredFields.filter(field => !complaintData[field] || complaintData[field].trim() === '');
        
        if (missingFields.length > 0) {
            throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
        }
        
        // Validate field lengths
        if (complaintData.title.length < 5 || complaintData.title.length > 100) {
            throw new Error('Title must be between 5 and 100 characters');
        }
        
        if (complaintData.description.length < 10 || complaintData.description.length > 2000) {
            throw new Error('Description must be between 10 and 2000 characters');
        }

        console.log('📤 Submitting complaint data:', JSON.stringify(complaintData, null, 2));

        // Submit to backend
        console.log('🌐 Sending API request to:', `${REGISTRATION_API_BASE_URL}/api/complaints/`);
        
        const response = await fetch(`${REGISTRATION_API_BASE_URL}/api/complaints/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(complaintData)
        });

        console.log('📥 API Response Status:', response.status);
        console.log('📥 API Response Headers:', Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ API Error Response:', errorText);
            
            let errorDetail = 'Failed to submit complaint';
            try {
                const errorData = JSON.parse(errorText);
                errorDetail = errorData.detail || errorData.message || errorText;
            } catch (e) {
                errorDetail = `Server error: ${response.status} ${response.statusText}`;
            }
            
            throw new Error(errorDetail);
        }

        const result = await response.json();
        console.log('✅ API Success Response:', JSON.stringify(result, null, 2));

        const complaintId = result.data?.id || result.data?._id || result.data?.grievanceID || 'JSM-XXXX';
        console.log('🎉 Complaint submitted successfully with ID:', complaintId);

        // Show success
        showSuccess(complaintId);
        showToast(`Complaint submitted successfully! ID: ${complaintId}`, 'success');
        
    } catch (error) {
        console.error('💥 Submission error:', error);
        console.error('💥 Error stack:', error.stack);
        
        // User-friendly error messages
        let userMessage = error.message;
        if (error.message.includes('fetch')) {
            userMessage = 'Network error. Please check your internet connection and try again.';
        } else if (error.message.includes('401') || error.message.includes('Unauthorized')) {
            userMessage = 'Session expired. Please login again.';
            setTimeout(() => window.location.href = 'index.html', 2000);
        } else if (error.message.includes('429') || error.message.includes('rate limit')) {
            userMessage = 'Too many requests. Please wait a moment and try again.';
        } else if (error.message.includes('500') || error.message.includes('Internal Server Error')) {
            userMessage = 'Server error. Please try again later.';
        }
        
        showToast(`Error: ${userMessage}`, 'error');
        
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        console.log('🏁 Submission process completed');
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

// Global debug function for troubleshooting
window.debugComplaintSystem = async function() {
    console.log('🔍 === COMPLAINT SYSTEM DEBUG ===');
    
    // Check authentication
    const token = sessionStorage.getItem('token') || localStorage.getItem('token');
    const user = JSON.parse(sessionStorage.getItem('js_user') || localStorage.getItem('js_user') || '{}');
    
    console.log('🔐 Authentication Status:');
    console.log('  Token exists:', !!token);
    console.log('  Token length:', token?.length || 0);
    console.log('  User data:', user);
    console.log('  User role:', user?.role);
    console.log('  User email:', user?.email);
    
    // Check API connectivity
    console.log('🌐 API Connectivity:');
    console.log('  API Base URL:', REGISTRATION_API_BASE_URL);
    
    try {
        const authResponse = await fetch(`${REGISTRATION_API_BASE_URL}/api/auth/me`, {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        console.log('  Auth check status:', authResponse.status);
        if (authResponse.ok) {
            const authData = await authResponse.json();
            console.log('  Auth response:', authData);
        }
    } catch (error) {
        console.error('  Auth check failed:', error.message);
    }
    
    // Check form elements
    console.log('📋 Form Elements:');
    const formElements = {
        'fCategory': document.getElementById('fCategory')?.value,
        'fSubcategory': document.getElementById('fSubcategory')?.value,
        'fDescription': document.getElementById('fDescription')?.value,
        'fAddress': document.getElementById('fAddress')?.value,
        'fRegion': document.getElementById('fRegion')?.value,
        'priority': document.querySelector('input[name="priority"]:checked')?.value
    };
    console.log('  Form values:', formElements);
    
    // Check map status
    console.log('🗺️ Map Status:');
    console.log('  Map manager exists:', !!mapManager);
    if (mapManager) {
        const location = mapManager.getSelectedLocation();
        console.log('  Selected location:', location);
    }
    
    // Test API endpoint directly
    console.log('🧪 API Endpoint Test:');
    try {
        const testResponse = await fetch(`${REGISTRATION_API_BASE_URL}/api/complaints/debug`, {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        console.log('  Debug endpoint status:', testResponse.status);
        if (testResponse.ok) {
            const debugData = await testResponse.json();
            console.log('  Debug response:', debugData);
        }
    } catch (error) {
        console.error('  Debug endpoint failed:', error.message);
    }
    
    console.log('🔍 === END DEBUG ===');
};

// Auto-run debug on page load (in development)
if (window.location.hostname === 'localhost' || window.location.hostname === '') {
    setTimeout(() => {
        console.log('🔧 Running auto-debug in development mode...');
        window.debugComplaintSystem();
    }, 2000);
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
