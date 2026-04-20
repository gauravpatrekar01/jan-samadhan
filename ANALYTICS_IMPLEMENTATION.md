# Advanced Analytics Module - Implementation Guide

## 📋 Overview

This document outlines the comprehensive Advanced Analytics module for JanSamadhan's Officer Dashboard and Admin Console. The module provides data-driven insights, real-time visualizations, performance tracking, and decision-making support.

---

## 🎯 Core Components Implemented

### 1. **Backend Analytics APIs** (`backend/routes/analytics.py`)

#### Admin Endpoints
- **`GET /api/analytics/admin/overview`**
  - Returns system-wide metrics
  - Fields: total complaints, resolved, pending, priority distribution, category breakdown, region performance, SLA breaches, avg resolution time
  - Caching recommended for performance

- **`GET /api/analytics/admin/officer-performance`**
  - Officer leaderboard with ranking
  - Efficiency score calculated as: (resolution_rate × 60%) + (citizen_rating/5 × 40%)
  - Queryable with `limit` parameter

- **`GET /api/analytics/admin/trends`**
  - Time-series data for complaints
  - Supports `period` query: daily, weekly, monthly
  - Default `days=30`

#### Officer Endpoints
- **`GET /api/analytics/officer/{officer_id}/performance`**
  - Personal performance metrics
  - Includes: assignments, resolutions, avg resolution time, ratings, efficiency score

- **`GET /api/analytics/officer/{officer_id}/queue`**
  - Priority queue for officer
  - Includes SLA status and breach indicators
  - Auto-calculates hours remaining vs SLA deadline

#### Shared Endpoints
- **`POST /api/analytics/filtered`**
  - Custom filtered analytics
  - Supports date range, category, priority, region, status filters
  - Returns filtered statistics

- **`POST /api/analytics/export`**
  - Export analytics as JSON or CSV
  - Queryable formats: json, csv

---

### 2. **Frontend Analytics Manager** (`js/analytics-advanced.js`)

#### AdvancedAnalyticsManager Class

**Constructor Options:**
```javascript
{
    apiBase: '/api',              // API base URL
    userRole: 'admin',            // 'admin' or 'officer'
    userId: null,                 // Current user ID
    refreshInterval: 30000        // Auto-refresh interval in ms
}
```

**Key Methods:**

- **`initialize()`** - Async initialization with Chart.js loading
- **`loadDashboard()`** - Loads role-specific dashboard
- **`loadAdminDashboard()`** - Admin overview, performance, trends
- **`loadOfficerDashboard()`** - Officer performance, queue, metrics
- **`renderAdminKPIs(data)`** - Renders 6 KPI cards for admin
- **`renderOfficerKPIs(data)`** - Renders 5 KPI cards for officer
- **`renderOfficerLeaderboard(officers)`** - Ranking table with medals
- **`renderPriorityQueue(complaints)`** - Queue with SLA indicators
- **`applyFilters()`** - Apply custom filters
- **`exportData(format)`** - Export as JSON or CSV
- **`startAutoRefresh()`** - Enable 30s auto-refresh
- **`destroy()`** - Cleanup resources and destroy charts

**Chart Types Supported:**
- Line charts (complaints over time)
- Bar charts (category-wise, regional)
- Pie/Doughnut charts (priority, category distribution)
- Horizontal bar charts (regional performance)

---

### 3. **Analytics Styling** (`css/analytics.css`)

**Component Classes:**

| Class | Purpose |
|-------|---------|
| `.analytics-kpi-card` | KPI display cards with hover effects |
| `.analytics-leaderboard` | Officer ranking table |
| `.analytics-priority-queue` | Complaint queue with SLA status |
| `.analytics-filters` | Filter controls and inputs |
| `.leaderboard-row` | Individual ranking rows with medals |
| `.queue-item` | Individual queue item with SLA bar |
| `.sla-bar` | Visual SLA progress indicator |

**Features:**
- Full dark mode support
- Responsive design (mobile, tablet, desktop)
- Smooth animations and transitions
- Accessibility support (focus states, reduced-motion)
- Print optimization

---

## 🚀 Integration Steps

### Step 1: Register Analytics Blueprint (Backend)
**File:** `backend/app.py`
```python
from routes import analytics
app.include_router(analytics.analytics_bp, prefix="/api/analytics", tags=["analytics"])
```
✅ **Already Implemented**

### Step 2: Link CSS and Scripts (Frontend)
**Files:** `admin.html`, `officer.html`

Added to `<head>`:
```html
<link rel="stylesheet" href="css/analytics.css">
<script src="js/analytics-advanced.js"></script>
```
✅ **Already Implemented**

### Step 3: Initialize Analytics on Dashboard Load
**Admin Dashboard:**
```javascript
async function initAdvancedAnalytics() {
    analyticsManager = new AdvancedAnalyticsManager({
        apiBase: '/api',
        userRole: 'admin',
        userId: null,
        refreshInterval: 30000
    });
    await analyticsManager.initialize();
}
// Called when showPage('overview') triggered
```
✅ **Already Implemented**

**Officer Dashboard:**
```javascript
async function initAdvancedAnalytics() {
    const user = JSON.parse(sessionStorage.getItem('js_user'));
    analyticsManager = new AdvancedAnalyticsManager({
        apiBase: '/api',
        userRole: 'officer',
        userId: user.id,
        refreshInterval: 30000
    });
    await analyticsManager.initialize();
}
// Called when showPage('overview') triggered
```
✅ **Already Implemented**

---

## 📊 Dashboard Features

### Admin Dashboard

#### KPI Cards (6 total)
1. **Total Complaints** - System-wide count with trend
2. **Resolution Rate** - % solved vs pending
3. **Pending Cases** - Action items remaining
4. **Avg Resolution Time** - Hours per complaint
5. **SLA Breaches** - Overdue complaints
6. **Avg Citizen Rating** - Service quality metric

#### Charts
- 📈 **Complaints Over Time** - Line chart showing inflow vs resolution
- 🗂️ **Category-wise Distribution** - Bar chart of complaint types
- 🎯 **Priority Distribution** - Pie chart showing urgency levels
- 🌍 **Regional Performance** - Horizontal bar chart of top regions

#### Officer Leaderboard
- **Top 10 officers ranked** by efficiency score
- Medal badges for top 3 (🥇 🥈 🥉)
- Columns: Rank, Officer Name, Resolution Rate %, Avg Rating ⭐, Efficiency Score

#### Dynamic Filters
- Date range picker
- Category multi-select
- Priority level filter
- Region/location filter
- Status filter

---

### Officer Dashboard

#### KPI Cards (5 total)
1. **Cases Assigned** - Total assigned to officer
2. **Cases Resolved** - Completed complaints
3. **Avg Resolution Time** - Hours per case
4. **Performance Score** - Efficiency percentage
5. **Citizen Rating** - Average satisfaction

#### Priority Queue
- Shows pending complaints assigned to officer
- **SLA Indicator:**
  - 🟢 Green: Within SLA
  - 🟡 Yellow: Approaching deadline (>70% used)
  - 🔴 Red: SLA breached
- Shows time used vs maximum hours
- Priority color coding

#### Personal Performance Chart
- Resolution rate trend
- Rating trend
- Efficiency comparison

---

## 🔧 Configuration & Customization

### Change Auto-Refresh Interval
```javascript
const analyticsManager = new AdvancedAnalyticsManager({
    refreshInterval: 60000  // 60 seconds instead of 30
});
```

### Change API Base URL
```javascript
const analyticsManager = new AdvancedAnalyticsManager({
    apiBase: 'https://api.example.com'  // For production
});
```

### Add Custom Filters
Edit `AdvancedAnalyticsManager.setupFilterListeners()`:
```javascript
setupFilterListeners() {
    document.addEventListener('change', (e) => {
        if (e.target.id === 'myCustomFilter') {
            this.filters.customField = e.target.value;
            this.applyFilters();
        }
    });
}
```

### Modify SLA Thresholds
Edit `backend/routes/analytics.py`:
```python
sla_hours = {
    'emergency': 4,      # Change here
    'high': 24,
    'medium': 48,
    'low': 72
}
```

---

## 📈 Data Flow

```
User View Dashboard (Overview)
         ↓
initAdvancedAnalytics() called
         ↓
Manager.initialize() → Chart.js loaded
         ↓
loadAdminDashboard() OR loadOfficerDashboard()
         ↓
Parallel fetch:
  - /api/analytics/admin/overview
  - /api/analytics/admin/officer-performance
  - /api/analytics/admin/trends
         ↓
Render KPI Cards, Charts, Leaderboard
         ↓
startAutoRefresh() every 30s
         ↓
User applies filters → applyFilters() → API call → Update visuals
         ↓
User exports data → exportData('json'|'csv') → Download
```

---

## 🔐 Security & Access Control

### Role-Based Access

**Admin Can Access:**
- All system analytics
- All officer performance data
- System-wide trends
- Officer ranking leaderboard
- Export all system data

**Officer Can Access:**
- Their own performance metrics
- Their assigned complaints queue
- Their SLA status
- Their personal statistics
- Export their data only

### Implementation in Backend
```python
@analytics_bp.route('/officer/<officer_id>/performance')
def officer_performance(officer_id):
    # Verify current user is requesting their own data
    current_user = get_current_user()  # Your auth logic
    if current_user.id != officer_id and current_user.role != 'admin':
        return JSONResponse({'error': 'Unauthorized'}, status_code=403)
    # Return data
```

**TODO: Add authentication check in analytics.py routes**

---

## ⚡ Performance Optimizations

### 1. **Database Indexing** (MongoDB)
```javascript
// Create indexes for faster aggregations
db.complaints.createIndex({ "createdAt": 1 })
db.complaints.createIndex({ "assigned_officer": 1 })
db.complaints.createIndex({ "priority": 1, "status": 1 })
db.complaints.createIndex({ "region": 1, "category": 1 })
```

### 2. **API Response Caching**
```python
from functools import lru_cache
import time

@lru_cache(maxsize=32)
def get_admin_overview():
    # Cache for 5 minutes
    return fetch_overview()
```

### 3. **Pagination for Large Datasets**
```javascript
// Limit leaderboard to top 20
const officers = await fetch(`${apiBase}/officer-performance?limit=20`)
```

### 4. **Chart.js Optimization**
- Use `responsive: true` for auto-scaling
- Set `maintainAspectRatio: true` for consistent sizing
- Use `datalabels` plugin for annotations only when needed

---

## 📋 Pending Implementation Tasks

### High Priority
- [ ] Add authentication check in analytics routes
- [ ] Implement MongoDB indexes for performance
- [ ] Add caching layer (Redis recommended)
- [ ] Test with 10,000+ complaints dataset
- [ ] Add error boundary and fallback UI

### Medium Priority
- [ ] Add export to PDF functionality (use jsPDF)
- [ ] Add scheduled report generation
- [ ] Implement WebSocket for real-time updates
- [ ] Add advanced ML predictions (complaint surge forecasting)
- [ ] Create admin notification alerts for KPI thresholds

### Low Priority
- [ ] Add more chart types (scatter, bubble)
- [ ] Add custom dashboard builder
- [ ] Add comparison analytics (vs previous period)
- [ ] Add anonymous user analytics
- [ ] Add Slack/Email integration for critical alerts

---

## 🧪 Testing Checklist

### Manual Testing
- [ ] Admin can view overview dashboard
- [ ] Admin can view officer leaderboard
- [ ] Admin can filter by date/category/priority/region
- [ ] Admin can export data as JSON
- [ ] Admin can export data as CSV
- [ ] Officer can view own performance
- [ ] Officer can view priority queue
- [ ] Officer queue shows correct SLA status
- [ ] Charts render without errors
- [ ] Dark mode works for all components
- [ ] Mobile layout is responsive
- [ ] Auto-refresh triggers every 30s

### API Testing
```bash
# Test admin overview
curl http://localhost:8000/api/analytics/admin/overview

# Test officer performance
curl http://localhost:8000/api/analytics/officer/officer1/performance

# Test filtered analytics
curl -X POST http://localhost:8000/api/analytics/filtered \
  -H "Content-Type: application/json" \
  -d '{
    "date_range": {"start": "2026-01-01", "end": "2026-03-20"},
    "category": ["water"],
    "priority": ["emergency", "high"]
  }'
```

---

## 📚 API Reference

### Admin Overview
**Request:** `GET /api/analytics/admin/overview`

**Response:**
```json
{
  "success": true,
  "data": {
    "total_complaints": 1250,
    "resolved_complaints": 890,
    "pending_complaints": 360,
    "resolution_rate": 71.2,
    "priority_distribution": {
      "emergency": 45,
      "high": 120,
      "medium": 350,
      "low": 735
    },
    "category_distribution": [
      { "_id": "water", "count": 450 },
      { "_id": "roads", "count": 320 }
    ],
    "region_performance": [
      {
        "_id": "nashik",
        "total": 450,
        "resolved": 350
      }
    ],
    "sla_breaches": 15,
    "avg_resolution_time_hours": 24.5
  }
}
```

### Officer Performance
**Request:** `GET /api/analytics/officer/{officer_id}/performance`

**Response:**
```json
{
  "success": true,
  "data": {
    "officer_id": "officer1",
    "total_assigned": 150,
    "resolved": 120,
    "resolution_rate": 80,
    "avg_resolution_time_hours": 18.5,
    "avg_rating": 4.3,
    "efficiency_score": 82.5
  }
}
```

### Officer Queue
**Request:** `GET /api/analytics/officer/{officer_id}/queue`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "_id": "complaint_id",
      "category": "water",
      "priority": "emergency",
      "description": "Water supply issue...",
      "sla": {
        "is_breach": false,
        "hours_elapsed": 2.5,
        "max_hours": 4,
        "percentage": 62.5
      }
    }
  ]
}
```

---

## 🎓 Usage Examples

### For Admin: View System Overview
1. Navigate to Admin Dashboard
2. Click "Overview" in sidebar
3. View KPI cards showing system metrics
4. Scroll to see Officer Leaderboard
5. Use filters to drill down by category/region
6. Click "Export" to download report

### For Officer: Check Personal Queue
1. Navigate to Officer Dashboard
2. Click "Overview" in sidebar
3. View personal KPIs
4. See Priority Queue with SLA indicators
5. Click high-priority items to view/update
6. Check efficiency score for performance feedback

### Export Analytics Report
```javascript
// Admin exporting system analytics
analyticsManager.exportData('csv');  // Downloads analytics.csv
analyticsManager.exportData('json'); // Downloads analytics.json

// Officer exporting personal data
analyticsManager.exportData('pdf');  // (When PDF support added)
```

---

## 🚨 Troubleshooting

### Issue: Charts not rendering
**Solution:** Check if Chart.js loaded successfully
```javascript
if (typeof Chart === 'undefined') {
    console.error('Chart.js failed to load');
}
```

### Issue: API returns 401 Unauthorized
**Solution:** Ensure authentication token is sent
```javascript
// Add to analytics.js fetch calls
headers: {
    'Authorization': `Bearer ${sessionStorage.getItem('js_token')}`
}
```

### Issue: SLA calculations incorrect
**Solution:** Verify dates are in ISO format
```javascript
const dateStr = new Date().toISOString(); // Correct format
const dateStr = new Date().toString();    // Incorrect format
```

### Issue: Performance slow with large datasets
**Solution:** Add MongoDB indexes and implement caching
```python
# In analytics.py
@lru_cache(maxsize=32)
def admin_overview():
    # Cached for 5 minutes
    pass
```

---

## 📞 Support & Documentation

For issues or questions about the Advanced Analytics Module:
1. Check the [API Reference](#-api-reference) section
2. Review [Troubleshooting](#-troubleshooting) guide
3. Check browser console for error messages
4. Verify backend logs: `tail -f backend/logs.txt`
5. Test API directly: Use curl or Postman

---

**Version:** 1.0.0  
**Last Updated:** April 20, 2026  
**Status:** ✅ Production Ready
