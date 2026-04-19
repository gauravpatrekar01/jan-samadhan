/**
 * Map Utilities for JanSamadhan
 * Handles Leaflet.js integration, geolocation, and complaint location management
 */

class MapManager {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.map = null;
        this.marker = null;
        this.selectedLat = null;
        this.selectedLng = null;
        this.userLocation = null;
        this.clusters = null;
        this.complaintMarkers = {};
        
        this.options = {
            defaultZoom: 13,
            markerColor: '#4f46e5',
            defaultCity: 'Nashik',
            defaultLat: 19.9975,
            defaultLng: 73.7898,
            ...options
        };

        this.initialize();
    }

    /**
     * Initialize the map and get user location
     */
    async initialize() {
        // Create map instance
        this.map = L.map(this.containerId).setView([this.options.defaultLat, this.options.defaultLng], this.options.defaultZoom);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);

        // Try to get user's location
        await this.getUserLocation();

        // Add event listeners
        this.setupEventListeners();
    }

    /**
     * Get user's geolocation using browser API
     */
    async getUserLocation() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                console.warn('Geolocation not supported. Using default location.');
                this.setMapCenter(this.options.defaultLat, this.options.defaultLng);
                resolve(false);
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    this.userLocation = { lat, lng };
                    this.setMapCenter(lat, lng);
                    console.log('✓ User location obtained:', lat, lng);
                    resolve(true);
                },
                (error) => {
                    console.warn('Geolocation permission denied:', error.message);
                    this.setMapCenter(this.options.defaultLat, this.options.defaultLng);
                    resolve(false);
                },
                { 
                    timeout: 10000,
                    enableHighAccuracy: false 
                }
            );
        });
    }

    /**
     * Set map center and add user location marker
     */
    setMapCenter(lat, lng) {
        if (this.map) {
            this.map.setView([lat, lng], this.options.defaultZoom);
            
            // Add user location circle/marker (subtle)
            if (this.userLocation) {
                L.circleMarker([lat, lng], {
                    radius: 6,
                    fillColor: '#4f46e5',
                    color: '#fff',
                    weight: 2,
                    opacity: 0.3,
                    fillOpacity: 0.3
                }).addTo(this.map).bindPopup('📍 Your location');
            }
        }
    }

    /**
     * Setup map click listeners
     */
    setupEventListeners() {
        if (!this.map) return;

        // Click on map to place marker
        this.map.on('click', (e) => {
            this.placeMarker(e.latlng.lat, e.latlng.lng);
        });

        // Double-click to recenter
        this.map.on('dblclick', () => {
            if (this.userLocation) {
                this.setMapCenter(this.userLocation.lat, this.userLocation.lng);
            }
        });
    }

    /**
     * Place or move a marker on the map
     */
    placeMarker(lat, lng) {
        // Remove existing marker
        if (this.marker) {
            this.map.removeLayer(this.marker);
        }

        // Create new marker
        this.marker = L.marker([lat, lng], {
            icon: L.icon({
                iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDQwIDQwIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIxOCIgZmlsbD0iIzRmNDZlNSIvPjxjaXJjbGUgY3g9IjIwIiBjeT0iMjAiIHI9IjEyIiBmaWxsPSIjZmZmIi8+PC9zdmc+',
                iconSize: [40, 40],
                iconAnchor: [20, 40],
                popupAnchor: [0, -40]
            }),
            draggable: true
        }).addTo(this.map);

        // Update coordinates
        this.selectedLat = lat;
        this.selectedLng = lng;

        // Show popup
        this.marker.bindPopup(`📍 Location Selected<br>Lat: ${lat.toFixed(4)}<br>Lng: ${lng.toFixed(4)}`).openPopup();

        // Update input fields if they exist
        this.updateLocationInputs(lat, lng);

        // Handle marker drag
        this.marker.on('drag', () => {
            const pos = this.marker.getLatLng();
            this.selectedLat = pos.lat;
            this.selectedLng = pos.lng;
            this.updateLocationInputs(pos.lat, pos.lng);
        });

        console.log('✓ Marker placed at:', lat, lng);
    }

    /**
     * Update location input fields
     */
    updateLocationInputs(lat, lng) {
        const latInput = document.getElementById('latitude');
        const lngInput = document.getElementById('longitude');
        
        if (latInput) latInput.value = lat.toFixed(6);
        if (lngInput) lngInput.value = lng.toFixed(6);

        // Trigger change event for form validation
        if (latInput) latInput.dispatchEvent(new Event('change', { bubbles: true }));
        if (lngInput) lngInput.dispatchEvent(new Event('change', { bubbles: true }));
    }

    /**
     * Search for a location using Nominatim API
     */
    async searchLocation(query) {
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`
            );
            const data = await response.json();
            
            if (data && data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lng = parseFloat(data[0].lon);
                this.placeMarker(lat, lng);
                this.setMapCenter(lat, lng);
                return { lat, lng, name: data[0].display_name };
            } else {
                console.warn('Location not found:', query);
                return null;
            }
        } catch (error) {
            console.error('Error searching location:', error);
            return null;
        }
    }

    /**
     * Add a complaint marker to the map (for dashboard view)
     */
    addComplaintMarker(complaint) {
        if (!complaint.latitude || !complaint.longitude) return;

        const lat = complaint.latitude;
        const lng = complaint.longitude;
        const id = complaint._id || complaint.id;

        // Determine marker color based on status
        const colors = {
            'submitted': '#fbbf24',
            'under review': '#3b82f6',
            'in progress': '#f97316',
            'resolved': '#10b981',
            'closed': '#6b7280'
        };

        const color = colors[complaint.status] || '#4f46e5';

        // Create custom icon
        const icon = L.divIcon({
            html: `
                <div style="
                    width: 30px;
                    height: 30px;
                    background: ${color};
                    border: 3px solid white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 16px;
                    cursor: pointer;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                ">
                    📍
                </div>
            `,
            iconSize: [30, 30],
            iconAnchor: [15, 30],
            popupAnchor: [0, -30],
            className: 'complaint-marker'
        });

        const marker = L.marker([lat, lng], { icon }).addTo(this.map);

        // Create popup content
        const popupContent = `
            <div style="max-width: 250px;">
                <h4 style="margin: 0 0 8px 0; color: ${color};">${complaint.title}</h4>
                <p style="margin: 0 0 8px 0; font-size: 12px; color: #666;">${complaint.description?.substring(0, 80)}...</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
                    <span><strong>Status:</strong> ${complaint.status}</span>
                    <span><strong>Priority:</strong> ${complaint.priority}</span>
                    <span><strong>Category:</strong> ${complaint.category}</span>
                    <span><strong>Region:</strong> ${complaint.region}</span>
                </div>
                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee;">
                    <small style="color: #999;">ID: ${id}</small>
                </div>
            </div>
        `;

        marker.bindPopup(popupContent);
        this.complaintMarkers[id] = marker;

        return marker;
    }

    /**
     * Load and display multiple complaints on map
     */
    async loadComplaints(complaints) {
        complaints.forEach(complaint => {
            this.addComplaintMarker(complaint);
        });

        // Auto-fit map bounds to all markers
        if (Object.keys(this.complaintMarkers).length > 0) {
            this.fitBoundsToMarkers();
        }
    }

    /**
     * Fit map bounds to show all markers
     */
    fitBoundsToMarkers() {
        const markers = Object.values(this.complaintMarkers);
        if (markers.length === 0) return;

        const group = new L.featureGroup(markers);
        this.map.fitBounds(group.getBounds().pad(0.1));
    }

    /**
     * Filter markers by status
     */
    filterByStatus(status) {
        Object.values(this.complaintMarkers).forEach(marker => {
            // Toggle visibility based on filter
            marker.setOpacity(status === 'all' || marker.options.status === status ? 1 : 0.3);
        });
    }

    /**
     * Clear all complaint markers
     */
    clearComplaintMarkers() {
        Object.values(this.complaintMarkers).forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.complaintMarkers = {};
    }

    /**
     * Initialize clustering (requires Leaflet.markercluster)
     */
    initializeClustering() {
        if (!window.L.markerClusterGroup) {
            console.warn('Leaflet.markercluster not loaded');
            return;
        }

        this.clusters = L.markerClusterGroup({
            maxClusterRadius: 80,
            disableClusteringAtZoom: 16
        }).addTo(this.map);

        return this.clusters;
    }

    /**
     * Add marker to cluster group
     */
    addToCluster(marker) {
        if (this.clusters) {
            this.clusters.addLayer(marker);
        }
    }

    /**
     * Get selected location
     */
    getSelectedLocation() {
        return {
            latitude: this.selectedLat,
            longitude: this.selectedLng,
            latitudeFormatted: this.selectedLat?.toFixed(6),
            longitudeFormatted: this.selectedLng?.toFixed(6)
        };
    }

    /**
     * Set selected location programmatically
     */
    setSelectedLocation(lat, lng) {
        this.placeMarker(lat, lng);
        this.setMapCenter(lat, lng);
    }

    /**
     * Get distance between two coordinates (in meters)
     */
    getDistance(lat1, lng1, lat2, lng2) {
        const R = 6371000; // Earth's radius in meters
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLng = (lng2 - lng1) * Math.PI / 180;
        const a = 
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    /**
     * Destroy map instance
     */
    destroy() {
        if (this.map) {
            this.map.remove();
            this.map = null;
        }
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MapManager;
}
