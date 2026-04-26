# 🎯 Advanced Analytics Module - Implementation Guide

**JanSamadhan Grievance Management System**

---

## 📋 Overview

The Advanced Analytics Module provides comprehensive data-driven insights for Officers and Admins in the JanSamadhan system. It includes real-time dashboards, advanced filtering, data exports, and AI-based recommendations.

### Key Components
- **Backend APIs** - FastAPI/Python analytics aggregations
- **Frontend Manager** - JavaScript analytics orchestration
- **Dashboard UI** - Officer & Admin HTML dashboards
- **Visualizations** - Chart.js for interactive charts
- **Real-time Updates** - Auto-refresh with configurable intervals

---

## 🚀 Quick Start

### 1. Backend Setup

#### API Endpoints Available

```
GET  /api/analytics/admin/overview              # System-wide overview
GET  /api/analytics/admin/officer-performance   # Officer rankings
GET  /api/analytics/admin/trends                # Daily/Weekly/Monthly trends
GET  /api/analytics/admin/ngo-contribution      # NGO performance
GET  /api/analytics/admin/escalation-advanced   # SLA & escalation status
GET  /api/analytics/admin/peak-times            # Peak complaint hours

GET  /api/analytics/officer/{officer_id}/performance  # Officer personal metrics
GET  /api/analytics/officer/{officer_id}/queue        # Priority queue

POST /api/analytics/filtered                    # Custom filtered analytics
POST /api/analytics/export                      # Export data (JSON/CSV)
```

### 2. Frontend Setup

#### Include Required Scripts

```html
<head>
  <!-- Chart.js (loaded automatically) -->
  <link rel="stylesheet" href="css/main.css">
  <link rel="stylesheet" href="css/analytics-dashboard.css">
</head>

<body>
  <!-- Dashboard HTML components -->
  
  <script src="js/api.js"></script>
  <script src="js/app.js"></script>
  <script src="js/advanced-analytics.js"></script>
  
  <script>
    // Initialize analytics
    document.addEventListener('DOMContentLoaded', async () => {
      await initAdvancedAnalytics({
        apiBase: '/api',
        userRole: 'admin',  // or 'officer'
        userId: 'user-123',
        refreshInterval: 30000
      });
    });
  </script>
</body>
```

### 3. Access Dashboards

**Officer Analytics Dashboard:**
```
http://localhost:5000/officer-analytics.html
```

**Admin Analytics Console:**
```
http://localhost:5000/admin-analytics.html
```

---

## 📊 Core Features

### 1. KPI Cards

Display key performance indicators with real-time updates:

```javascript
// Automatically populated based on analytics data
// Total Complaints, Resolution Rate, Pending Cases, etc.
```

### 2. Interactive Charts

Multiple chart types for data visualization:

- **Doughnut Chart** - Category distribution
- **Bar Chart** - Priority levels
- **Line Chart** - Trends over time
- **Heatmap** - Geographical density (future)

### 3. Advanced Filtering

Filter analytics by:
- Date range (start/end dates)
- Category (Water, Electricity, etc.)
- Priority (Emergency, High, Medium, Low)
- Region (Location-based)
- Status (Submitted, In Progress, Resolved)

#### Apply Filters

```javascript
// Filter triggers automatic dashboard update
advancedAnalytics.toggleFilter('priority', 'emergency');
advancedAnalytics.applyFilters();
```

### 4. Real-time Updates

Auto-refresh dashboard at configured intervals:

```javascript
// Configure in initialization
await initAdvancedAnalytics({
  refreshInterval: 30000  // 30 seconds
});

// Toggle auto-refresh
document.getElementById('autoRefreshToggle').addEventListener('change', (e) => {
  advancedAnalytics.autoRefreshEnabled = e.target.checked;
});
```

### 5. Data Export

Export analytics data in multiple formats:

```javascript
// Export as JSON or CSV
advancedAnalytics.exportData();  // Uses selected format from dropdown
```

---

## 🎨 Admin Console Features

### Overview Dashboard
- Total complaints filed
- Resolution rate percentage
- Pending cases count
- SLA breach tracking
- Average resolution time

### Officer Performance Leaderboard
Top performers ranked by:
- Resolution rate (60% weight)
- Customer satisfaction rating (40% weight)
- Efficiency score (combined)

### Escalation Tracking
- Total escalated complaints
- Unresolved SLA breaches
- Escalation trend charts

### Trend Analysis
- Daily/Weekly/Monthly complaint patterns
- Resolution trends over time
- Peak activity hours prediction

---

## 👮 Officer Dashboard Features

### Performance Metrics
- Total assigned complaints
- Resolved cases
- Resolution rate
- Efficiency score
- Average rating
- Average resolution time

### Priority Queue
Live queue of assigned complaints sorted by:
1. Priority level (Emergency → Low)
2. Urgency (SLA status)
3. Assignment time

### SLA Status Indicators
- % through SLA deadline
- Breach warnings (color-coded)
- Time remaining to resolve

---

## 🔧 Configuration Options

### Analytics Manager Options

```javascript
const options = {
  apiBase: '/api',              // API base URL
  userRole: 'admin',            // 'admin' or 'officer'
  userId: 'officer-123',        // For officer-specific data
  refreshInterval: 30000,       // Auto-refresh interval (ms)
  cacheExpiry: 60000            // Data cache expiry (ms)
};

advancedAnalytics = new AdvancedAnalytics(options);
```

### API Query Parameters

```
GET /api/analytics/admin/overview?days=30
GET /api/analytics/admin/trends?period=daily&days=30
GET /api/analytics/admin/officer-performance?limit=20
```

---

## 📈 Data Structure

### Admin Overview Response

```json
{
  "success": true,
  "data": {
    "total_complaints": 156,
    "resolved_complaints": 132,
    "pending_complaints": 24,
    "resolution_rate": 84.6,
    "priority_distribution": {
      "emergency": 12,
      "high": 34,
      "medium": 78,
      "low": 32
    },
    "category_distribution": [
      { "_id": "Water Supply", "count": 45 },
      { "_id": "Electricity", "count": 38 }
    ],
    "sla_breaches": 5,
    "avg_resolution_time_hours": 24.5
  }
}
```

### Officer Performance Response

```json
{
  "success": true,
  "data": {
    "officer_id": "officer-123",
    "total_assigned": 45,
    "resolved": 38,
    "resolution_rate": 84.4,
    "avg_resolution_time_hours": 18.2,
    "avg_rating": 4.3,
    "efficiency_score": 82.5
  }
}
```

---

## 🎯 Advanced Features

### 1. Filtering & Drill-down

```javascript
// Apply multiple filters
advancedAnalytics.filters.category = ['Water Supply', 'Electricity'];
advancedAnalytics.filters.priority = ['emergency', 'high'];
advancedAnalytics.filters.dateRange = {
  start: new Date('2024-01-01'),
  end: new Date('2024-01-31')
};

await advancedAnalytics.applyFilters();
```

### 2. Custom Queries

```javascript
// Post custom filter request
const response = await fetch('/api/analytics/filtered', {
  method: 'POST',
  body: JSON.stringify({
    date_range: {
      start: '2024-01-01T00:00:00',
      end: '2024-01-31T23:59:59'
    },
    category: ['Water Supply'],
    priority: ['emergency', 'high'],
    region: ['Ward-A', 'Ward-B'],
    status: ['in_progress']
  })
});
```

### 3. Data Caching

```javascript
// Automatic caching with expiry
advancedAnalytics.setCache('adminOverview', data, 60000);  // 60s expiry

// Retrieve from cache
const cached = advancedAnalytics.getCache('adminOverview');
```

### 4. Export with Filters

```javascript
// Export only filtered data
advancedAnalytics.exportData();  // Exports based on current filters
```

---

## 🔒 Security & Access Control

### Role-Based Analytics

```javascript
// Officer only sees own data
advancedAnalytics.userRole = 'officer';
advancedAnalytics.userId = 'officer-123';

// Admin sees system-wide data
advancedAnalytics.userRole = 'admin';
```

### Backend Authorization

All API endpoints require:
- Valid JWT token
- Role validation (officer/admin)
- Officer data isolation for officer role

---

## 📱 Responsive Design

The dashboards are fully responsive:

- **Desktop (>1024px)** - 2-3 column layouts
- **Tablet (768px-1024px)** - Single column with adaptive cards
- **Mobile (<768px)** - Stack all cards vertically

---

## 🧪 Testing

### Manual Testing Checklist

- [ ] Load dashboards with valid user roles
- [ ] Verify all KPI cards update correctly
- [ ] Test date range filtering
- [ ] Check chart rendering and responsiveness
- [ ] Test auto-refresh toggle
- [ ] Export data in both JSON and CSV formats
- [ ] Test on mobile devices
- [ ] Verify dark mode compatibility

### Sample Test Data

```bash
# Create test complaints for analytics
POST /api/complaints
{
  "title": "Test Complaint",
  "category": "Water Supply",
  "priority": "high",
  "region": "Ward-A",
  "description": "Test data for analytics"
}
```

---

## 🚀 Performance Optimization

### 1. Caching Strategy
- Cache API responses for 60 seconds
- Clear cache on filter changes
- Implement incremental updates

### 2. API Optimization
- Use pagination for large datasets
- Limit returned records (default 20)
- Aggregate at database level

### 3. Frontend Optimization
- Lazy-load Chart.js
- Destroy old charts before creating new ones
- Debounce filter inputs (300ms)

### 4. Database Indexing

```python
# Required MongoDB indexes
db.complaints.create_index([('assigned_officer', 1), ('status', 1)])
db.complaints.create_index([('priority', 1), ('createdAt', -1)])
db.complaints.create_index([('category', 1), ('region', 1)])
db.complaints.create_index([('createdAt', -1)])
```

---

## 📊 Visualization Best Practices

### Chart Types by Use Case

| Use Case | Chart Type | Example |
|----------|-----------|---------|
| Part-to-whole | Doughnut | Category distribution |
| Comparison | Bar | Priority levels |
| Trends | Line | Complaints over time |
| Distribution | Histogram | Resolution times |
| Geographic | Heatmap | Region density |

### Color Scheme

```css
/* Use consistent colors */
--chart-primary: #3b82f6;    /* Blue */
--chart-success: #10b981;    /* Green */
--chart-warning: #f97316;    /* Orange */
--chart-danger: #dc2626;     /* Red */
--chart-info: #0ea5e9;       /* Cyan */
```

---

## 🔗 Integration Points

### With Main Dashboard

```html
<!-- Add link from main officer/admin dashboard -->
<a href="officer-analytics.html" class="btn btn-primary">
  📈 View Advanced Analytics
</a>
```

### With Notifications

```javascript
// Show alerts for critical insights
if (escalations.unresolved_sla_breaches > 10) {
  showToast('⚠️ High SLA breaches detected!', 'warning');
}
```

---

## 📝 Future Enhancements

### Planned Features

1. **Predictive Analytics**
   - ML model for complaint volume forecasting
   - Resource allocation recommendations

2. **Advanced Heatmaps**
   - Geographical density visualization
   - Interactive map drill-down

3. **Custom Reports**
   - Report builder UI
   - Scheduled email exports

4. **Real-time Collaboration**
   - WebSocket updates
   - Multi-user dashboard sync

5. **Mobile App**
   - Native app for officers
   - Offline analytics access

---

## 🐛 Troubleshooting

### Charts Not Rendering

```javascript
// Check if Chart.js loaded
console.log(typeof Chart);  // Should be 'function'

// Ensure canvas elements exist
console.log(document.getElementById('categoryChart'));
```

### No Data Appearing

```javascript
// Verify API connectivity
fetch('/api/analytics/admin/overview')
  .then(r => r.json())
  .then(d => console.log(d));

// Check browser console for errors
// Verify user authentication
```

### Auto-refresh Not Working

```javascript
// Check refresh interval
console.log(advancedAnalytics.refreshInterval);

// Verify toggle state
console.log(advancedAnalytics.autoRefreshEnabled);
```

---

## 📞 Support & Documentation

### Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Chart.js Documentation](https://www.chartjs.org/)
- [MongoDB Aggregation](https://docs.mongodb.com/manual/aggregation/)

### Development Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --reload

# Frontend
cd ..
python -m http.server 5000
# Navigate to http://localhost:5000/admin-analytics.html
```

---

## 📄 License & Credits

Part of JanSamadhan Grievance Management System
Built with ❤️ for transparent governance

---

**Last Updated:** April 2026  
**Version:** 2.0.0
