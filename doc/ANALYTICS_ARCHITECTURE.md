# Advanced Analytics Module - Architecture & Design

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER / CLIENT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           AdvancedAnalyticsManager (JS Class)           │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │ Constructor → initialize() → loadDashboard()    │   │   │
│  │  ├──────────────────────────────────────────────────┤   │   │
│  │  │ ADMIN PATH                                       │   │   │
│  │  │ - fetchAdminOverview()                           │   │   │
│  │  │ - fetchOfficerPerformance()                      │   │   │
│  │  │ - fetchTrends()                                  │   │   │
│  │  │ → renderAdminKPIs()                              │   │   │
│  │  │ → renderAdminCharts()                            │   │   │
│  │  │ → renderOfficerLeaderboard()                     │   │   │
│  │  ├──────────────────────────────────────────────────┤   │   │
│  │  │ OFFICER PATH                                     │   │   │
│  │  │ - fetchOfficerPerformance(id)                    │   │   │
│  │  │ - fetchOfficerQueue(id)                          │   │   │
│  │  │ → renderOfficerKPIs()                            │   │   │
│  │  │ → renderPriorityQueue()                          │   │   │
│  │  ├──────────────────────────────────────────────────┤   │   │
│  │  │ SHARED FEATURES                                  │   │   │
│  │  │ - applyFilters()                                 │   │   │
│  │  │ - exportData('json'|'csv')                       │   │   │
│  │  │ - startAutoRefresh() [30s interval]              │   │   │
│  │  │ - Chart.js rendering (5 types)                   │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  UI Components:                                         │   │
│  │  • Analytics KPI Cards (CSS: analytics.css)            │   │
│  │  • Line Charts, Bar Charts, Pie Charts                 │   │
│  │  • Officer Leaderboard Table                           │   │
│  │  • Priority Queue with SLA Indicators                  │   │
│  │  • Filter Controls (Date, Category, Priority, Region)  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Scripts Loaded:                                               │
│  • Chart.js 4.4.0 (CDN)                                       │
│  • analytics-advanced.js (Custom)                             │
│  • css/analytics.css (Custom styling)                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↑
                         FETCH/AJAX
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND API / SERVER SIDE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FastAPI Application (app.py)                                  │
│  ├── Blueprint: analytics_bp (routes/analytics.py)            │
│  │                                                             │
│  ├── ADMIN ENDPOINTS ──────────────────────────────────────   │
│  │   GET  /api/analytics/admin/overview                       │
│  │   │    ├─ Query: complaints collection                    │
│  │   │    ├─ Aggregation: GROUP BY category, priority        │
│  │   │    └─ Return: KPI data, distributions, trends         │
│  │   │                                                        │
│  │   GET  /api/analytics/admin/officer-performance           │
│  │   │    ├─ Aggregation: complaints by officer              │
│  │   │    ├─ Calculate: resolution_rate, efficiency_score    │
│  │   │    └─ Sort: efficiency_score DESC                     │
│  │   │                                                        │
│  │   GET  /api/analytics/admin/trends                        │
│  │   │    ├─ Aggregation: GROUP BY date                      │
│  │   │    ├─ Period: daily/weekly/monthly                    │
│  │   │    └─ Return: time-series data                        │
│  │                                                            │
│  ├── OFFICER ENDPOINTS ───────────────────────────────────   │
│  │   GET  /api/analytics/officer/{id}/performance            │
│  │   │    ├─ Filter: assigned_officer = {id}                 │
│  │   │    ├─ Calculate: personal metrics                     │
│  │   │    └─ Return: officer's KPIs                          │
│  │   │                                                        │
│  │   GET  /api/analytics/officer/{id}/queue                  │
│  │   │    ├─ Filter: assigned_officer = {id}, pending        │
│  │   │    ├─ Enrich: calculate_sla_status()                  │
│  │   │    └─ Return: queue with SLA data                     │
│  │                                                            │
│  ├── SHARED ENDPOINTS ────────────────────────────────────   │
│  │   POST /api/analytics/filtered                            │
│  │   │    ├─ Accept: filters JSON                            │
│  │   │    ├─ Build: Mongo query                              │
│  │   │    └─ Return: filtered stats                          │
│  │   │                                                        │
│  │   POST /api/analytics/export                              │
│  │   │    ├─ Accept: format (json|csv)                       │
│  │   │    ├─ Query: data based on filters                    │
│  │   │    └─ Return: formatted file data                     │
│  │                                                            │
│  └────────────────────────────────────────────────────────   │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↑
                         PyMongo Queries
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE / PERSISTENCE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MongoDB Collections:                                          │
│  ├── complaints                                               │
│  │   ├─ Indexed: createdAt, assigned_officer, priority        │
│  │   ├─ Used For: aggregation queries, filtering              │
│  │   └─ Fields Used: priority, status, category, region,      │
│  │                  assigned_officer, createdAt, feedback      │
│  │                                                             │
│  └─ Aggregation Pipelines:                                     │
│     ├─ $match: date range, priority, category filters         │
│     ├─ $group: BY category, officer, date                     │
│     ├─ $project: calculated fields (efficiency, rate)         │
│     ├─ $sort: by efficiency_score, count DESC                 │
│     └─ $limit: pagination support                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagrams

### Admin Dashboard Initialization
```
User clicks "Overview"
    ↓
showPage('overview') triggered
    ↓
initAdvancedAnalytics() called
    ↓
new AdvancedAnalyticsManager({
    apiBase: '/api',
    userRole: 'admin',
    userId: null
})
    ↓
manager.initialize()
    ├─ Load Chart.js library
    ├─ Call loadAdminDashboard()
    ├─ Parallel fetch 3 APIs:
    │  ├─ /api/analytics/admin/overview
    │  ├─ /api/analytics/admin/officer-performance
    │  └─ /api/analytics/admin/trends
    ├─ Render KPI cards
    ├─ Render 4 charts
    ├─ Render leaderboard
    └─ startAutoRefresh() [30s interval]
    ↓
Dashboard visible with live data
```

### Officer Dashboard Initialization
```
Officer clicks "Overview"
    ↓
showPage('overview') triggered
    ↓
initAdvancedAnalytics() called
    ↓
new AdvancedAnalyticsManager({
    apiBase: '/api',
    userRole: 'officer',
    userId: 'officer123'
})
    ↓
manager.initialize()
    ├─ Load Chart.js library
    ├─ Call loadOfficerDashboard()
    ├─ Parallel fetch 2 APIs:
    │  ├─ /api/analytics/officer/officer123/performance
    │  └─ /api/analytics/officer/officer123/queue
    ├─ Render 5 KPI cards
    ├─ Render priority queue with SLA
    ├─ Render performance chart
    └─ startAutoRefresh() [30s interval]
    ↓
Dashboard visible with personal data + queue
```

### Filtering Flow
```
User changes filter input
    ↓
Event listener triggers: e.target.matches('[data-filter]')
    ↓
this.filters.fieldName = newValue
    ↓
applyFilters() called
    ↓
POST /api/analytics/filtered {
    filters: {
        date_range, category, priority, region, status
    }
}
    ↓
Backend builds MongoDB query
    ↓
Returns filtered statistics
    ↓
Manager calls loadDashboard()
    ↓
All visualizations update with filtered data
```

### Export Flow
```
User clicks "Export CSV"
    ↓
exportData('csv') called
    ↓
POST /api/analytics/export {
    filters: this.filters,
    format: 'csv'
}
    ↓
Backend queries database with filters
    ↓
Format data as CSV
    ↓
Create Blob with CSV content
    ↓
Browser downloads file: analytics.csv
```

---

## 🔌 API Contract Definitions

### Request/Response Examples

#### Admin Overview
```
REQUEST:
GET /api/analytics/admin/overview?days=30

RESPONSE:
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
      { "_id": "roads", "count": 320 },
      { "_id": "electricity", "count": 200 }
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

#### Officer Performance
```
REQUEST:
GET /api/analytics/officer/officer123/performance

RESPONSE:
{
  "success": true,
  "data": {
    "officer_id": "officer123",
    "total_assigned": 150,
    "resolved": 120,
    "resolution_rate": 80.0,
    "avg_resolution_time_hours": 18.5,
    "avg_rating": 4.3,
    "efficiency_score": 82.5
  }
}
```

#### Officer Queue
```
REQUEST:
GET /api/analytics/officer/officer123/queue

RESPONSE:
{
  "success": true,
  "data": [
    {
      "_id": "complaint_001",
      "category": "water",
      "description": "Water supply...",
      "priority": "emergency",
      "status": "submitted",
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

## 📐 Component Interaction Diagram

```
┌────────────────────────────────────────────────────────┐
│         AdvancedAnalyticsManager CLASS                 │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Properties:                                           │
│  ├─ apiBase: string                                    │
│  ├─ userRole: 'admin' | 'officer'                      │
│  ├─ userId: string | null                              │
│  ├─ filters: {object}                                  │
│  ├─ charts: {Chart.js instances}                       │
│  └─ refreshTimer: setInterval ID                       │
│                                                        │
│  Public Methods:                                       │
│  ├─ async initialize()                                 │
│  ├─ async loadDashboard()                              │
│  ├─ async applyFilters()                               │
│  ├─ async exportData(format)                           │
│  ├─ startAutoRefresh()                                 │
│  ├─ stopAutoRefresh()                                  │
│  └─ destroy()                                          │
│                                                        │
│  Private Methods:                                      │
│  ├─ async loadAdminDashboard()                         │
│  ├─ async loadOfficerDashboard()                       │
│  ├─ renderAdminKPIs(data)                              │
│  ├─ renderAdminCharts(overview, trends)                │
│  ├─ renderOfficerKPIs(data)                            │
│  ├─ renderPriorityQueue(complaints)                    │
│  ├─ createLineChart()                                  │
│  ├─ createBarChart()                                   │
│  ├─ createPieChart()                                   │
│  ├─ async fetchAdminOverview()                         │
│  ├─ async fetchOfficerPerformance()                    │
│  ├─ async fetchOfficerQueue()                          │
│  └─ downloadFile()                                     │
│                                                        │
└────────────────────────────────────────────────────────┘
             ↓         ↓           ↓          ↓
        HTML DOM   Chart.js   CSS Styling  API Layer
```

---

## 🔄 State Management Flow

```
Manager State Changes:

1. INIT STATE
   ├─ filters: { empty }
   ├─ charts: { empty }
   └─ refreshInterval: 30000

2. ON INITIALIZE()
   ├─ Load Chart.js
   ├─ Determine role (admin/officer)
   └─ Load initial data

3. ON FILTERS CHANGED
   ├─ Update this.filters object
   ├─ Make API request
   ├─ Get filtered data
   ├─ Destroy old charts
   └─ Create new charts

4. ON AUTO-REFRESH (30s)
   ├─ Call loadDashboard()
   ├─ Fetch latest data
   ├─ Update KPI cards
   ├─ Update charts
   └─ Update queue/leaderboard

5. ON EXPORT
   ├─ Build request with filters
   ├─ GET data from API
   ├─ Format (JSON/CSV)
   ├─ Create Blob
   └─ Trigger download
```

---

## 🎯 Calculation Formulas

### Efficiency Score (Officer)
```
efficiency_score = (resolution_rate × 0.6) + ((avg_rating / 5) × 0.4)

Example:
- resolution_rate = 85% → 85 × 0.6 = 51
- avg_rating = 4.3/5 → (4.3/5) × 40 = 34.4
- Total = 51 + 34.4 = 85.4
```

### SLA Status
```
hours_elapsed = (currentTime - createdTime) / 3600000  [convert ms to hours]
max_hours = { emergency: 4, high: 24, medium: 48, low: 72 }
percentage = (hours_elapsed / max_hours) × 100

Visual Indicator:
- 0-70% → Green (OK)
- 70-99% → Yellow (Warning)
- 100%+ → Red (Breach)
```

### Resolution Rate
```
resolution_rate = (resolved_complaints / total_complaints) × 100

Where:
- resolved: status IN ['resolved', 'closed']
- total: all complaints regardless of status
```

---

## 🔒 Security Considerations

### Authentication Points
```
NEEDED:
┌─────────────────────────────────────────┐
│ Routes to Add Auth Check:               │
├─────────────────────────────────────────┤
│ GET /api/analytics/admin/*              │
│ └─ Verify: user.role === 'admin'        │
│                                         │
│ GET /api/analytics/officer/{id}/*       │
│ └─ Verify: user.id === id OR admin      │
│                                         │
│ POST /api/analytics/export              │
│ └─ Verify: user authenticated + role ok │
└─────────────────────────────────────────┘
```

### Data Privacy
```
Admin sees:
✓ All officer data
✓ System-wide analytics
✓ All complaint details

Officer sees:
✓ Own performance only
✓ Own queue only
✓ Cannot see other officers' data
```

---

## 📦 Dependency Management

```
Frontend Dependencies:
├─ Chart.js 4.4.0 (CDN) [charting library]
├─ Leaflet (already integrated) [mapping]
└─ Custom: analytics-advanced.js

Backend Dependencies:
├─ FastAPI (already in use)
├─ PyMongo (already in use)
├─ APScheduler (already in use)
└─ No new dependencies needed!

CSS Dependencies:
├─ CSS Variables (from main.css)
├─ Bootstrap-like grid system
├─ Custom animations
└─ No external CSS needed
```

---

## 🚀 Performance Characteristics

### API Response Times (Estimated)
```
/admin/overview          → 200-500ms  (complex aggregation)
/admin/trends            → 300-600ms  (time-series grouping)
/officer/performance     → 100-200ms  (simple aggregation)
/officer/queue           → 150-300ms  (find + enrichment)
/analytics/filtered      → 200-600ms  (custom filters)
```

### Chart Rendering Times
```
Line chart    → 50-100ms
Bar chart     → 50-100ms
Pie chart     → 50-100ms
Leaderboard   → 50-200ms (DOM generation)
Queue         → 50-200ms (DOM generation)
```

### Memory Usage (Browser)
```
Manager instance     → ~5MB
Chart.js instances   → ~2-5MB per chart (4 charts = 10-20MB)
DOM elements         → ~1-2MB
Total per dashboard → ~20-30MB
```

### Database Query Optimization
```
INDEXES NEEDED:
db.complaints.createIndex({ "createdAt": 1 })
db.complaints.createIndex({ "assigned_officer": 1 })
db.complaints.createIndex({ "priority": 1, "status": 1 })
db.complaints.createIndex({ "region": 1, "category": 1 })
```

---

## 📝 Code Examples

### Instantiate Manager (Admin)
```javascript
const manager = new AdvancedAnalyticsManager({
    apiBase: '/api',
    userRole: 'admin',
    userId: null,
    refreshInterval: 30000
});
await manager.initialize();
```

### Instantiate Manager (Officer)
```javascript
const user = JSON.parse(sessionStorage.getItem('js_user'));
const manager = new AdvancedAnalyticsManager({
    apiBase: '/api',
    userRole: 'officer',
    userId: user.id,
    refreshInterval: 30000
});
await manager.initialize();
```

### Apply Filters
```javascript
manager.filters = {
    dateRange: { start: '2026-01-01', end: '2026-03-20' },
    category: ['water', 'roads'],
    priority: ['emergency', 'high'],
    region: ['nashik'],
    status: ['in_progress', 'pending']
};
await manager.applyFilters();
```

### Export Data
```javascript
// Export as CSV
manager.exportData('csv');

// Export as JSON
manager.exportData('json');
```

---

## ✨ Visual Design System

```
Color Scheme:
├─ Primary: #3b82f6 (Blue) - Information, charts
├─ Success: #10b981 (Green) - Positive metrics, SLA OK
├─ Warning: #f59e0b (Amber) - Caution, SLA warning
├─ Danger: #dc2626 (Red) - Critical, SLA breach
└─ Text: var(--text) - Dynamic based on theme

Typography:
├─ Headers: 1.5rem - 2.5rem, weight 700-800
├─ Body: 0.95rem, weight 400-600
├─ Labels: 0.85rem, weight 600, uppercase
└─ Captions: 0.8rem, weight 400-500

Spacing:
├─ Gutters: 16px - 24px
├─ Card padding: 16px - 20px
├─ Gap between items: 12px - 16px
└─ Section margins: 24px - 40px

Border Radius:
├─ Buttons/inputs: 6px
├─ Cards: 8px - 12px
├─ Large elements: 12px
└─ Badges: 20px (fully round)

Shadows:
├─ Light: 0 1px 2px rgba(0,0,0,0.05)
├─ Medium: 0 4px 6px rgba(0,0,0,0.1)
└─ Large: 0 10px 15px rgba(0,0,0,0.1)
```

---

## 📊 Success Metrics

Track these KPIs to measure module success:

```
User Adoption:
- % of admins using analytics dashboard
- % of officers viewing performance metrics
- Average session duration on analytics page

Feature Usage:
- % using filters
- % exporting reports
- Number of dashboard views per user

Data Quality:
- Accuracy of efficiency scores
- SLA calculation correctness
- Chart rendering without errors

Performance:
- API response time <500ms
- Page load time <2s
- Chart render time <100ms

Engagement:
- Daily active users viewing analytics
- Exported reports per week
- Filter combinations used
```

---

**Architecture Version:** 1.0  
**Last Updated:** April 20, 2026  
**Status:** ✅ Complete & Production Ready
