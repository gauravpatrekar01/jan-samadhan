/**
 * Advanced Heatmap Visualization for JanSamadhan
 * Features: Interactive heatmap, filters, real-time updates, clustering, legends
 */

class AdvancedHeatmapManager {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.map = null;
        this.heatLayer = null;
        this.markerClusterGroup = null;
        this.allComplaints = [];
        this.filteredComplaints = [];
        this.filters = {
            dateRange: { start: null, end: null },
            category: null,
            severity: null,
            status: null,
            region: null
        };
        this.heatmapData = [];
        
        this.options = {
            defaultZoom: 10,
            defaultCenter: [19.9975, 73.7898], // Nashik
            maxZoom: 19,
            minZoom: 5,
            enableClustering: true,
            enableHeatmap: true,
            enableMarkers: false,
            refreshInterval: 30000, // 30 seconds
            ...options
        };

        this.colorScheme = {
            low: '#4ade80',      // Green
            medium: '#facc15',   // Yellow
            high: '#f97316',     // Orange
            emergency: '#dc2626' // Red
        };

        this.priorityMap = {
            'low': { color: '#4ade80', radius: 5, intensity: 0.3 },
            'medium': { color: '#facc15', radius: 8, intensity: 0.5 },
            'high': { color: '#f97316', radius: 12, intensity: 0.7 },
            'emergency': { color: '#dc2626', radius: 15, intensity: 0.9 }
        };

        this.categoryColorMap = {
            'Infrastructure': '#2563eb',
            'Water Supply': '#0891b2',
            'Electricity': '#ca8a04',
            'Sanitation': '#7c3aed',
            'Transport': '#059669',
            'Law & Order': '#dc2626',
            'Healthcare': '#db2777',
            'Other': '#64748b'
        };
    }

    async initialize() {
        try {
            // Check if container exists
            const container = document.getElementById(this.containerId);
            if (!container) {
                throw new Error(`Container with ID "${this.containerId}" not found in DOM`);
            }

            // Validate required Leaflet libraries
            if (typeof L === 'undefined') {
                throw new Error('Leaflet library not loaded');
            }
            if (typeof L.heatLayer !== 'function') {
                console.warn('⚠️ Leaflet-Heat library not loaded. Heat visualization will be skipped.');
                this.options.enableHeatmap = false;
            }
            if (typeof L.markerClusterGroup !== 'function') {
                console.warn('⚠️ Leaflet-MarkerCluster library not loaded. Clustering will be disabled.');
                this.options.enableClustering = false;
            }

            // Initialize map
            this.map = L.map(this.containerId).setView(this.options.defaultCenter, this.options.defaultZoom);

            // Add tile layer with better styling for dashboard
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: this.options.maxZoom,
                minZoom: this.options.minZoom,
                className: 'map-tiles'
            }).addTo(this.map);

            // Initialize marker cluster group
            if (this.options.enableClustering) {
                this.markerClusterGroup = L.markerClusterGroup({
                    maxClusterRadius: 60,
                    iconCreateFunction: (cluster) => {
                        const count = cluster.getChildCount();
                        const size = count > 100 ? 'large' : count > 20 ? 'medium' : 'small';
                        const intensity = Math.min(count / 50, 1);
                        const color = this.getColorByIntensity(intensity);
                        
                        return L.divIcon({
                            html: `<div class="heatmap-cluster heatmap-cluster-${size}" style="background-color: ${color}; border-color: ${color}20;">${count}</div>`,
                            className: 'heatmap-cluster-icon',
                            iconSize: [40, 40]
                        });
                    }
                });
                this.map.addLayer(this.markerClusterGroup);
            }

            // Setup event listeners
            this.setupEventListeners();

            // Auto-refresh data
            this.startAutoRefresh();

            console.log('✓ Advanced Heatmap initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing heatmap:', error);
            throw error;
        }
    }

    invalidateSize() {
        if (this.map) {
            this.map.invalidateSize();
        }
    }

    async loadData() {
        try {
            const geoResponse = await window.JanSamadhanAPI.getGeoComplaintData();
            const points = geoResponse?.points || [];
            if (points.length > 0) {
                this.allComplaints = points.map(p => ({
                    ...p,
                    lat: p.latitude,
                    lng: p.longitude
                }));
            } else {
                const response = await window.JanSamadhanAPI.getAllGrievances();
                this.allComplaints = response || [];
            }
            
            // Apply filters and update visualization
            this.applyFilters();
        } catch (error) {
            console.warn('Failed to load grievances, using dummy data:', error);
            this.allComplaints = this.generateDummyData();
            this.applyFilters();
        }
    }

    generateDummyData() {
        const regions = ['Nashik', 'Aurangabad', 'Pune', 'Nagpur', 'Akola', 'Parbhani'];
        const categories = ['Road Damage', 'Water Supply', 'Electricity', 'Sanitation', 'Safety'];
        const statuses = ['submitted', 'under_review', 'in_progress', 'resolved', 'closed'];
        const priorities = ['low', 'medium', 'high', 'emergency'];
        
        return Array.from({ length: 150 }, (_, i) => ({
            id: `CMPLT-${String(i + 1).padStart(6, '0')}`,
            title: `Sample Complaint ${i + 1}`,
            category: categories[Math.floor(Math.random() * categories.length)],
            priority: priorities[Math.floor(Math.random() * priorities.length)],
            region: regions[Math.floor(Math.random() * regions.length)],
            status: statuses[Math.floor(Math.random() * statuses.length)],
            lat: 19.9975 + (Math.random() - 0.5) * 3,
            lng: 73.7898 + (Math.random() - 0.5) * 3,
            createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
            description: `Sample complaint description for complaint ${i + 1}`
        }));
    }

    applyFilters() {
        this.filteredComplaints = this.allComplaints.filter(complaint => {
            // Date range filter
            if (this.filters.dateRange.start && new Date(complaint.createdAt) < this.filters.dateRange.start) {
                return false;
            }
            if (this.filters.dateRange.end && new Date(complaint.createdAt) > this.filters.dateRange.end) {
                return false;
            }

            // Category filter
            if (this.filters.category && complaint.category !== this.filters.category) {
                return false;
            }

            // Severity/Priority filter
            if (this.filters.severity && complaint.priority !== this.filters.severity) {
                return false;
            }

            // Status filter
            if (this.filters.status && complaint.status !== this.filters.status) {
                return false;
            }

            // Region filter
            if (this.filters.region && complaint.region !== this.filters.region) {
                return false;
            }

            return true;
        });

        // Update visualization
        this.updateHeatmap();
        this.updateMarkers();
        this.updateStats();
    }

    updateHeatmap() {
        if (!this.options.enableHeatmap) return;

        // Check if L.heatLayer is available
        if (typeof L.heatLayer !== 'function') {
            console.warn('⚠️ L.heatLayer is not available. Make sure leaflet-heat library is loaded.');
            return;
        }

        // Remove existing heatmap layer
        if (this.heatLayer) {
            this.map.removeLayer(this.heatLayer);
        }

        // Prepare heatmap data with intensity based on priority
        this.heatmapData = this.filteredComplaints.map(complaint => {
            const priority = complaint.priority?.toLowerCase() || 'low';
            const intensity = this.priorityMap[priority]?.intensity || 0.3;
            return [
                complaint.lat || 19.9975,
                complaint.lng || 73.7898,
                intensity
            ];
        });

        // Create heatmap layer
        this.heatLayer = L.heatLayer(this.heatmapData, {
            radius: 25,
            blur: 15,
            maxZoom: 17,
            gradient: {
                0.0: '#4ade80',   // Green
                0.4: '#facc15',   // Yellow
                0.7: '#f97316',   // Orange
                1.0: '#dc2626'    // Red
            }
        }).addTo(this.map);
    }

    updateMarkers() {
        if (!this.options.enableClustering || !this.markerClusterGroup) return;

        // Clear existing markers
        this.markerClusterGroup.clearLayers();

        // Add markers for each complaint
        this.filteredComplaints.forEach(complaint => {
            const priority = complaint.priority?.toLowerCase() || 'low';
            const categoryColor = this.categoryColorMap[complaint.category] || '#64748b';

            const marker = L.circleMarker([complaint.lat || 19.9975, complaint.lng || 73.7898], {
                radius: this.priorityMap[priority]?.radius || 8,
                fillColor: categoryColor,
                color: categoryColor,
                weight: 2,
                opacity: 0.8,
                fillOpacity: 0.6,
                className: `priority-${priority}`
            });

            // Add tooltip with complaint details
            marker.bindTooltip(`
                <div class="heatmap-tooltip">
                    <div class="tooltip-title">${complaint.id}</div>
                    <div class="tooltip-category">${complaint.category}</div>
                    <div class="tooltip-priority priority-badge-${priority}">${priority.toUpperCase()}</div>
                    <div class="tooltip-status">${complaint.status || 'N/A'}</div>
                    <div class="tooltip-region">${complaint.region || 'N/A'}</div>
                </div>
            `, {
                permanent: false,
                direction: 'top',
                className: 'heatmap-tooltip-container'
            });

            // Add popup with more details
            marker.bindPopup(`
                <div class="heatmap-popup">
                    <div class="popup-id">${complaint.id}</div>
                    <div class="popup-title">${complaint.title || 'No Title'}</div>
                    <div class="popup-details">
                        <p><strong>Category:</strong> ${complaint.category}</p>
                        <p><strong>Priority:</strong> <span class="priority-badge priority-badge-${priority}">${priority.toUpperCase()}</span></p>
                        <p><strong>Status:</strong> ${complaint.status || 'N/A'}</p>
                        <p><strong>Region:</strong> ${complaint.region || 'N/A'}</p>
                        <p><strong>Location:</strong> ${complaint.lat?.toFixed(4)}, ${complaint.lng?.toFixed(4)}</p>
                    </div>
                    <div class="popup-date">${new Date(complaint.createdAt).toLocaleDateString()}</div>
                </div>
            `);

            this.markerClusterGroup.addLayer(marker);
        });
    }

    updateStats() {
        const statsContainer = document.getElementById('heatmapStats');
        if (!statsContainer) return;

        const stats = {
            total: this.filteredComplaints.length,
            emergency: this.filteredComplaints.filter(c => c.priority?.toLowerCase() === 'emergency').length,
            high: this.filteredComplaints.filter(c => c.priority?.toLowerCase() === 'high').length,
            medium: this.filteredComplaints.filter(c => c.priority?.toLowerCase() === 'medium').length,
            low: this.filteredComplaints.filter(c => c.priority?.toLowerCase() === 'low').length,
            resolved: this.filteredComplaints.filter(c => c.status === 'resolved' || c.status === 'closed').length,
            inProgress: this.filteredComplaints.filter(c => c.status === 'in_progress').length
        };

        const resolutionRate = stats.total > 0 ? Math.round((stats.resolved / stats.total) * 100) : 0;

        statsContainer.innerHTML = `
            <div class="heatmap-stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${stats.total}</div>
                    <div class="stat-label">Total Complaints</div>
                </div>
                <div class="stat-card stat-emergency">
                    <div class="stat-value">${stats.emergency}</div>
                    <div class="stat-label">Emergency</div>
                </div>
                <div class="stat-card stat-high">
                    <div class="stat-value">${stats.high}</div>
                    <div class="stat-label">High Priority</div>
                </div>
                <div class="stat-card stat-medium">
                    <div class="stat-value">${stats.medium}</div>
                    <div class="stat-label">Medium</div>
                </div>
                <div class="stat-card stat-low">
                    <div class="stat-value">${stats.low}</div>
                    <div class="stat-label">Low Priority</div>
                </div>
                <div class="stat-card stat-resolved">
                    <div class="stat-value">${resolutionRate}%</div>
                    <div class="stat-label">Resolved</div>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        // Filter event listeners will be attached by the page using this manager
        this.setupZoomControls();
    }

    setupZoomControls() {
        const zoomInBtn = document.getElementById('heatmapZoomIn');
        const zoomOutBtn = document.getElementById('heatmapZoomOut');
        const resetViewBtn = document.getElementById('heatmapResetView');

        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => {
                this.map.zoomIn();
            });
        }

        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => {
                this.map.zoomOut();
            });
        }

        if (resetViewBtn) {
            resetViewBtn.addEventListener('click', () => {
                this.map.setView(this.options.defaultCenter, this.options.defaultZoom);
            });
        }
    }

    setDateRangeFilter(startDate, endDate) {
        this.filters.dateRange = { start: startDate, end: endDate };
        this.applyFilters();
    }

    setCategoryFilter(category) {
        this.filters.category = category || null;
        this.applyFilters();
    }

    setSeverityFilter(severity) {
        this.filters.severity = severity || null;
        this.applyFilters();
    }

    setStatusFilter(status) {
        this.filters.status = status || null;
        this.applyFilters();
    }

    setRegionFilter(region) {
        this.filters.region = region || null;
        this.applyFilters();
    }

    resetFilters() {
        this.filters = {
            dateRange: { start: null, end: null },
            category: null,
            severity: null,
            status: null,
            region: null
        };
        this.applyFilters();
    }

    getColorByIntensity(intensity) {
        if (intensity < 0.25) return '#4ade80';      // Green
        if (intensity < 0.5) return '#facc15';       // Yellow
        if (intensity < 0.75) return '#f97316';      // Orange
        return '#dc2626';                            // Red
    }

    startAutoRefresh() {
        setInterval(() => {
            this.loadData();
        }, this.options.refreshInterval);
    }

    toggleHeatmap(enable) {
        this.options.enableHeatmap = enable;
        if (enable) {
            this.updateHeatmap();
        } else if (this.heatLayer) {
            this.map.removeLayer(this.heatLayer);
        }
    }

    toggleMarkers(enable) {
        this.options.enableClustering = enable;
        if (enable && this.markerClusterGroup) {
            this.updateMarkers();
            this.map.addLayer(this.markerClusterGroup);
        } else if (this.markerClusterGroup) {
            this.map.removeLayer(this.markerClusterGroup);
        }
    }

    exportAsJSON() {
        return {
            timestamp: new Date().toISOString(),
            filters: this.filters,
            stats: {
                total: this.filteredComplaints.length,
                data: this.filteredComplaints
            }
        };
    }

    printMap() {
        window.print();
    }
}
