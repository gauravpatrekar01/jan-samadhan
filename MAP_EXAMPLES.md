/**
 * MapManager Usage Examples
 * Practical code snippets for integrating the map into your JanSamadhan application
 */

// ============================================================================
// Example 1: Basic Map Initialization in a Form
// ============================================================================

function example1_BasicMapInit() {
  // Create a map in a container div
  const mapManager = new MapManager('myMapContainer', {
    defaultZoom: 13,
    defaultCity: 'Nashik',
    defaultLat: 19.9975,
    defaultLng: 73.7898,
    markerColor: '#4f46e5'
  });

  // Access selected location
  const location = mapManager.getSelectedLocation();
  console.log(`Latitude: ${location.latitude}, Longitude: ${location.longitude}`);
}

// ============================================================================
// Example 2: Complaint Registration Form with Map
// ============================================================================

async function example2_SubmitComplaintWithLocation() {
  // Assume mapManager is already initialized

  // Get selected location from map
  const location = mapManager.getSelectedLocation();

  // Build complaint data
  const complaintData = {
    title: 'Water Supply Issue',
    description: 'No water from 3 days',
    category: 'Water Supply',
    priority: 'high',
    location: 'Ram Nagar, Nashik',
    latitude: location.latitude,      // ← From map!
    longitude: location.longitude,    // ← From map!
    region: 'Nashik'
  };

  // Submit to backend
  const response = await fetch('/api/complaints/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(complaintData)
  });

  const result = await response.json();
  console.log(`✓ Complaint submitted: ${result.data.id}`);
}

// ============================================================================
// Example 3: Dashboard - Load All Complaints on Map
// ============================================================================

async function example3_LoadComplaintsOnDashboard() {
  // Initialize map
  const mapManager = new MapManager('dashboardMap', {
    defaultZoom: 11,
    defaultLat: 19.9975,
    defaultLng: 73.7898
  });

  // Fetch all complaints from API
  const response = await fetch('/api/complaints/', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const data = await response.json();
  const complaints = data.data;

  // Load all complaints on map
  mapManager.loadComplaints(complaints);

  console.log(`✓ Loaded ${complaints.length} complaints on map`);
}

// ============================================================================
// Example 4: Search Location by Name
// ============================================================================

async function example4_SearchLocation() {
  // Initialize map
  const mapManager = new MapManager('mapContainer');

  // Search for a location
  const location = await mapManager.searchLocation('Nashik');

  if (location) {
    console.log(`Found: ${location.name}`);
    console.log(`Coordinates: ${location.lat}, ${location.lng}`);
    // Marker automatically placed on map
  } else {
    console.log('Location not found');
  }
}

// ============================================================================
// Example 5: Filter Complaints by Status on Dashboard
// ============================================================================

function example5_FilterComplaintsByStatus() {
  // Assume mapManager has loaded complaints

  // Show only 'resolved' complaints
  mapManager.filterByStatus('resolved');

  // Show only 'emergency' priority
  mapManager.filterByStatus('emergency');

  // Show all
  mapManager.filterByStatus('all');
}

// ============================================================================
// Example 6: Get Distance Between Two Locations
// ============================================================================

function example6_CalculateDistance() {
  // Initialize map
  const mapManager = new MapManager('mapContainer');

  // Current location (Nashik)
  const lat1 = 19.9975;
  const lng1 = 73.7898;

  // Selected complaint location
  const lat2 = 20.0050;
  const lng2 = 73.7950;

  // Calculate distance in meters
  const distanceMeters = mapManager.getDistance(lat1, lng1, lat2, lng2);
  const distanceKm = (distanceMeters / 1000).toFixed(2);

  console.log(`Distance: ${distanceKm} km`);
}

// ============================================================================
// Example 7: Add Multiple Complaint Markers
// ============================================================================

function example7_AddMultipleMarkers() {
  // Initialize map
  const mapManager = new MapManager('mapContainer');

  // Sample complaints
  const complaints = [
    {
      _id: 'JSM-001',
      title: 'Pothole',
      description: 'Large pothole on main road',
      latitude: 19.9975,
      longitude: 73.7898,
      status: 'in progress',
      priority: 'high',
      category: 'Infrastructure',
      region: 'Nashik'
    },
    {
      _id: 'JSM-002',
      title: 'Water Issue',
      description: 'No water supply',
      latitude: 19.9925,
      longitude: 73.7950,
      status: 'submitted',
      priority: 'emergency',
      category: 'Water Supply',
      region: 'Nashik'
    }
  ];

  // Add each complaint
  complaints.forEach(complaint => {
    mapManager.addComplaintMarker(complaint);
  });
}

// ============================================================================
// Example 8: Handle Marker Click Events
// ============================================================================

function example8_MarkerClickHandler() {
  // Initialize map
  const mapManager = new MapManager('mapContainer');

  // Add a complaint marker
  const complaint = {
    _id: 'JSM-001',
    title: 'Infrastructure Issue',
    description: 'Pothole on Main Road',
    latitude: 19.9975,
    longitude: 73.7898,
    status: 'in progress',
    priority: 'high'
  };

  const marker = mapManager.addComplaintMarker(complaint);

  // Listen for marker click
  marker.on('click', () => {
    console.log(`Clicked complaint: ${complaint.title}`);
    // Can open detail view, modal, etc.
    showComplaintDetail(complaint._id);
  });
}

// ============================================================================
// Example 9: Real-Time Location Updates
// ============================================================================

function example9_RealTimeUpdates() {
  // Initialize map
  const mapManager = new MapManager('mapContainer');

  // Simulate receiving updates every 5 seconds
  setInterval(async () => {
    const response = await fetch('/api/complaints/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const data = await response.json();
    const newComplaints = data.data;

    // Clear old markers
    mapManager.clearComplaintMarkers();

    // Load new ones
    mapManager.loadComplaints(newComplaints);

    console.log('✓ Map updated with latest complaints');
  }, 5000); // Every 5 seconds
}

// ============================================================================
// Example 10: Custom Map Styling with Dark Mode
// ============================================================================

function example10_DarkModeMap() {
  // Initialize map
  const mapManager = new MapManager('mapContainer', {
    markerColor: '#6366f1' // Indigo for dark theme
  });

  // Toggle dark mode
  const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';

  if (isDarkMode) {
    // Apply dark theme to map tiles
    document.querySelectorAll('.leaflet-tile').forEach(tile => {
      tile.style.filter = 'brightness(0.8)';
    });
  }
}

// ============================================================================
// Example 11: Export Complaints with Locations as CSV
// ============================================================================

function example11_ExportAsCSV() {
  // Get all markers from mapManager
  const complaints = Object.values(mapManager.complaintMarkers);

  // Build CSV
  const headers = ['ID', 'Title', 'Status', 'Priority', 'Latitude', 'Longitude'];
  const rows = complaints.map(marker => [
    marker.options.id,
    marker.options.title,
    marker.options.status,
    marker.options.priority,
    marker.getLatLng().lat.toFixed(6),
    marker.getLatLng().lng.toFixed(6)
  ]);

  // Create CSV content
  const csv = [headers, ...rows]
    .map(row => row.join(','))
    .join('\n');

  // Download
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `complaints-${new Date().toISOString().split('T')[0]}.csv`;
  a.click();

  console.log('✓ CSV exported');
}

// ============================================================================
// Example 12: Show Cluster Markers for Density View
// ============================================================================

function example12_ClusterMarkers() {
  // Initialize map
  const mapManager = new MapManager('mapContainer');

  // Initialize clustering (requires Leaflet.markercluster)
  mapManager.initializeClustering();

  // Load complaints with clustering
  const complaints = [
    // ... 100+ complaints
  ];

  complaints.forEach(complaint => {
    const marker = mapManager.addComplaintMarker(complaint);
    mapManager.addToCluster(marker);
  });

  console.log('✓ Complaints clustered');
}

// ============================================================================
// Example 13: Use Geolocation to Pre-fill Location
// ============================================================================

async function example13_AutoFillLocation() {
  // Initialize map
  const mapManager = new MapManager('mapContainer');

  // User's current location is automatically detected
  if (mapManager.userLocation) {
    // Pre-fill location field
    document.getElementById('latitude').value = mapManager.userLocation.lat.toFixed(6);
    document.getElementById('longitude').value = mapManager.userLocation.lng.toFixed(6);

    console.log('✓ User location auto-filled');
  }
}

// ============================================================================
// Example 14: Programmatically Set Location
// ============================================================================

function example14_SetLocationProgrammatically() {
  // Initialize map
  const mapManager = new MapManager('mapContainer');

  // Set location programmatically (e.g., from saved data)
  const savedLat = 19.9975;
  const savedLng = 73.7898;

  mapManager.setSelectedLocation(savedLat, savedLng);

  console.log('✓ Location set to:', savedLat, savedLng);
}

// ============================================================================
// Example 15: Responsive Map with Window Resize
// ============================================================================

function example15_ResponsiveMap() {
  // Initialize map
  const mapManager = new MapManager('mapContainer');

  // Handle window resize
  window.addEventListener('resize', () => {
    setTimeout(() => {
      if (mapManager.map) {
        mapManager.map.invalidateSize();
        console.log('✓ Map resized');
      }
    }, 100);
  });

  // Also handle orientation change for mobile
  window.addEventListener('orientationchange', () => {
    setTimeout(() => {
      if (mapManager.map) {
        mapManager.map.invalidateSize();
        console.log('✓ Map rotated');
      }
    }, 100);
  });
}

// ============================================================================
// INTEGRATION CHECKLIST
// ============================================================================

/**
 * ✅ Tasks Completed:
 * 
 * [x] Create MapManager class with all methods
 * [x] Add Leaflet.js and OpenStreetMap integration
 * [x] Implement geolocation detection
 * [x] Add location search (Nominatim)
 * [x] Create registration form map
 * [x] Create dashboard map view
 * [x] Add filter/search functionality
 * [x] Implement marker clustering
 * [x] Add dark mode support
 * [x] Create responsive design
 * [x] Add CSV export
 * [x] Implement status-based coloring
 * [x] Add popup markers
 * [x] Create documentation
 * 
 * 🚀 Ready for Production!
 */

// ============================================================================
// QUICK REFERENCE
// ============================================================================

/**
 * MapManager Public API:
 * 
 * Constructor:
 *   new MapManager(containerId, options)
 * 
 * Location Methods:
 *   getUserLocation()              - Get browser location
 *   searchLocation(query)          - Search by place name
 *   setSelectedLocation(lat, lng)  - Set location programmatically
 *   getSelectedLocation()          - Get current selection
 *   placeMarker(lat, lng)          - Place/move marker
 * 
 * Complaint Methods:
 *   addComplaintMarker(complaint)  - Add single complaint
 *   loadComplaints(complaints)     - Load multiple complaints
 *   clearComplaintMarkers()        - Clear all complaint markers
 *   filterByStatus(status)         - Filter displayed markers
 * 
 * Utility Methods:
 *   getDistance(lat1, lng1, lat2, lng2) - Calculate distance
 *   fitBoundsToMarkers()           - Auto-zoom to fit all
 *   initializeClustering()         - Enable marker clustering
 *   destroy()                      - Cleanup map instance
 */
