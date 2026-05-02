/**
 * Registration Form Script with Map Integration
 * Handles map initialization and UI helpers for the registration page.
 * Note: Submission logic is handled in register.html.
 */

let mapManager = null;

// Initialize form on page load
document.addEventListener('DOMContentLoaded', async () => {
    initializeMap();
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
 * Select complaint category
 */
function selectCategory(element) {
    document.querySelectorAll('.cat-icon-btn').forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');
    
    const cat = element.dataset.cat;
    // Update hidden field if needed, or global variable in register.html
    if (typeof selectedCategory !== 'undefined') {
        selectedCategory = cat;
    }
    const catInput = document.getElementById('fCategory');
    if (catInput) catInput.value = cat;
    
    console.log('✓ Category selected:', cat);
}

/**
 * Preview image upload
 */
function previewImage(input) {
    const container = document.getElementById('imgPreviewContainer');
    const preview = document.getElementById('imgPreview');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
            if (preview) {
                preview.src = e.target.result;
                if (container) container.style.display = 'block';
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
        mobileNav.classList.toggle('open');
    }
}

/**
 * Handle map search
 */
async function searchLocation() {
    const searchInput = document.getElementById('mapSearchInput');
    if (!searchInput || !searchInput.value || !mapManager) return;

    const result = await mapManager.searchLocation(searchInput.value);
    if (result) {
        console.log(`✓ Location found: ${result.name}`);
    } else {
        if (typeof showToast === 'function') {
            showToast('Location not found. Please try another search.', 'error');
        }
    }
}
