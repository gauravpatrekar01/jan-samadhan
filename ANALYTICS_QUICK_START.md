# Advanced Analytics Module - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Verify Backend Routes are Registered
1. Open `backend/app.py`
2. Check for: `app.include_router(analytics.analytics_bp, prefix="/api/analytics", tags=["analytics"])`
3. ✅ Already added!

### Step 2: Start Backend Server
```bash
cd backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Access Admin Dashboard
1. Open browser → `http://localhost:3000/admin.html`
2. Login with admin credentials
3. Click "Overview" in sidebar
4. Advanced Analytics should load with KPI cards and charts

### Step 4: Access Officer Dashboard
1. Open browser → `http://localhost:3000/officer.html`
2. Login with officer credentials
3. Click "Overview" in sidebar
4. View personal performance metrics and priority queue

---

## 📊 Feature Checklist

### Admin Features ✅
- [x] KPI Cards (6 metrics)
- [x] System overview (total, resolved, pending, SLA breaches)
- [x] Officer leaderboard with ranking
- [x] Trend charts (daily, weekly, monthly)
- [x] Category distribution chart
- [x] Priority distribution chart
- [x] Regional performance ranking
- [x] Dynamic filtering system
- [x] Export as JSON/CSV
- [x] Dark mode support
- [x] Mobile responsive design
- [x] Auto-refresh every 30 seconds

### Officer Features ✅
- [x] KPI Cards (5 metrics)
- [x] Personal performance tracking
- [x] Priority queue with SLA indicators
- [x] Efficiency scoring
- [x] Average resolution time tracking
- [x] Citizen rating display
- [x] Color-coded SLA status (green/yellow/red)
- [x] Auto-refresh every 30 seconds
- [x] Mobile responsive design
- [x] Dark mode support

---

## 🔍 Testing the APIs

### Test Admin Overview
```bash
curl -X GET http://localhost:8000/api/analytics/admin/overview
```
**Expected Response:** System metrics with complaint statistics

### Test Officer Performance
```bash
curl -X GET http://localhost:8000/api/analytics/officer/officer1/performance
```
**Expected Response:** Officer's personal metrics

### Test Officer Queue
```bash
curl -X GET http://localhost:8000/api/analytics/officer/officer1/queue
```
**Expected Response:** Array of pending complaints with SLA status

### Test Filtered Analytics
```bash
curl -X POST http://localhost:8000/api/analytics/filtered \
  -H "Content-Type: application/json" \
  -d '{
    "date_range": {"start": "2026-01-01", "end": "2026-12-31"},
    "category": ["water", "roads"],
    "priority": ["high", "emergency"]
  }'
```
**Expected Response:** Filtered statistics

---

## 🎨 Customization Options

### Change KPI Cards
Edit in `js/analytics-advanced.js`:
```javascript
renderAdminKPIs(data) {
    const kpis = [
        {
            title: 'Your Custom KPI',
            value: data.your_field,
            icon: '📌',
            color: '#3b82f6'
        },
        // Add more...
    ];
}
```

### Change Chart Colors
Edit in `css/analytics.css`:
```css
.analytics-kpi-card {
    --primary-color: #3b82f6;  /* Change this */
}
```

### Change Auto-Refresh Interval
Edit in HTML where manager is instantiated:
```javascript
analyticsManager = new AdvancedAnalyticsManager({
    refreshInterval: 60000  // 60 seconds
});
```

### Change SLA Thresholds
Edit in `backend/routes/analytics.py`:
```python
sla_hours = {
    'emergency': 4,      # Change here
    'high': 24,
    'medium': 48,
    'low': 72
}
```

---

## 🐛 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Charts not showing | Check if Chart.js loaded: Inspect Network tab |
| API 404 error | Verify analytics routes registered in app.py |
| SLA showing incorrect | Check complaint dates are ISO format |
| Performance slow | Add MongoDB indexes (see ANALYTICS_IMPLEMENTATION.md) |
| Dark mode not working | Check CSS variables are defined in main.css |

---

## 📈 Sample Data for Testing

The analytics module works best with real complaint data. To see good visualizations:

1. **File 10-20 test complaints** through citizen portal with:
   - Different categories (water, roads, electricity, etc.)
   - Different priorities (emergency, high, medium, low)
   - Different regions (nashik, aurangabad, pune, etc.)

2. **Update some complaints** to show resolution tracking:
   - Set status to "in_progress" for some
   - Set status to "resolved" for others
   - This will populate resolution_rate metrics

3. **Assign to different officers** to see officer leaderboard work

---

## 🎯 Next Steps

### Immediate (Today)
1. ✅ Backend analytics routes created
2. ✅ Frontend manager class implemented
3. ✅ CSS styling completed
4. ✅ Integration into admin.html
5. ✅ Integration into officer.html

### Short Term (This Week)
- [ ] Add authentication checks to analytics routes
- [ ] Create MongoDB indexes for performance
- [ ] Implement response caching
- [ ] Test with 1000+ complaints

### Medium Term (This Month)
- [ ] Add PDF export functionality
- [ ] Add WebSocket real-time updates
- [ ] Add email reports feature
- [ ] Add complaint surge prediction (ML)

### Long Term (Next Quarter)
- [ ] Add advanced filtering UI builder
- [ ] Add custom dashboard creation
- [ ] Add team/department comparisons
- [ ] Add quarterly trend analysis

---

## 📞 Support Resources

| Resource | Location |
|----------|----------|
| Full Documentation | `ANALYTICS_IMPLEMENTATION.md` |
| Backend Code | `backend/routes/analytics.py` |
| Frontend Manager | `js/analytics-advanced.js` |
| Styling | `css/analytics.css` |
| Admin Integration | `admin.html` (lines ~590-610) |
| Officer Integration | `officer.html` (lines ~375-400) |

---

## ✅ Deployment Checklist

Before going to production:

- [ ] Add authentication to analytics routes
- [ ] Set up MongoDB indexes
- [ ] Configure API response caching
- [ ] Test with production-scale data
- [ ] Set up error logging and monitoring
- [ ] Configure CORS properly
- [ ] Enable HTTPS/TLS
- [ ] Set up backup strategy
- [ ] Create admin documentation
- [ ] Train officers on feature usage

---

**Happy Analytics! 📊✨**

If you encounter any issues, refer to the full [ANALYTICS_IMPLEMENTATION.md](ANALYTICS_IMPLEMENTATION.md) guide for detailed troubleshooting.
