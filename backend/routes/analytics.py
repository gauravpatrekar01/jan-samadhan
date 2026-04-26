"""
Advanced Analytics Module for JanSamadhan
Provides comprehensive data-driven insights for Officers and Admins
"""

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
import json
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

# Request models for type validation
class FilterRequest(BaseModel):
    date_range: Optional[dict] = None
    category: Optional[List[str]] = None
    priority: Optional[List[str]] = None
    region: Optional[List[str]] = None
    status: Optional[List[str]] = None

class ExportRequest(BaseModel):
    filters: dict
    format: str = 'json'

# ════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_date_range_filter(days=30):
    """Generate date range filter for analytics"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return {'start': start_date, 'end': end_date}


def calculate_sla_status(created_date, status, priority='low'):
    """Calculate SLA breach status"""
    sla_hours = {
        'emergency': 4,
        'high': 24,
        'medium': 48,
        'low': 72
    }
    
    max_hours = sla_hours.get(priority.lower(), 72)
    hours_elapsed = (datetime.now() - created_date).total_seconds() / 3600
    
    return {
        'is_breach': hours_elapsed > max_hours and status not in ['resolved', 'closed'],
        'hours_elapsed': round(hours_elapsed, 1),
        'max_hours': max_hours,
        'percentage': min(round((hours_elapsed / max_hours) * 100), 100)
    }


# ════════════════════════════════════════════════════════════════
# ADMIN ANALYTICS
# ════════════════════════════════════════════════════════════════

@router.get('/admin/overview')
async def admin_overview(days: int = Query(30)):
    """
    Comprehensive system overview for admins
    Returns: Total complaints, resolution rate, trends, department performance
    """
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        date_filter = get_date_range_filter(days)
        
        # Total complaints
        total = complaints_collection.count_documents({})
        resolved = complaints_collection.count_documents({'status': {'$in': ['resolved', 'closed']}})
        pending = complaints_collection.count_documents({'status': {'$nin': ['resolved', 'closed']}})
        
        # Priority distribution
        priority_dist = {
            'emergency': complaints_collection.count_documents({'priority': 'emergency'}),
            'high': complaints_collection.count_documents({'priority': 'high'}),
            'medium': complaints_collection.count_documents({'priority': 'medium'}),
            'low': complaints_collection.count_documents({'priority': 'low'})
        }
        
        # Category distribution
        category_dist = list(complaints_collection.aggregate([
            {
                '$group': {
                    '_id': '$category',
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}}
        ]))
        
        # Convert to proper dicts
        category_dist = [{'_id': doc['_id'], 'count': doc['count']} for doc in category_dist]
        
        # Region performance
        region_perf = list(complaints_collection.aggregate([
            {
                '$group': {
                    '_id': '$region',
                    'total': {'$sum': 1},
                    'resolved': {
                        '$sum': {'$cond': [{'$in': ['$status', ['resolved', 'closed']]}, 1, 0]}
                    }
                }
            },
            {'$sort': {'total': -1}},
            {'$limit': 10}
        ]))
        
        # Convert to proper dicts
        region_perf = [{'_id': doc['_id'], 'total': doc['total'], 'resolved': doc['resolved']} for doc in region_perf]
        
        # SLA breaches
        sla_breaches = complaints_collection.count_documents({
            'status': {'$nin': ['resolved', 'closed']},
            'createdAt': {'$lt': datetime.now() - timedelta(hours=72)}
        })
        
        # Average resolution time - using simple Python calculation
        avg_resolution_time = 0
        resolved_docs = list(complaints_collection.find(
            {'status': {'$in': ['resolved', 'closed']}, 'updatedAt': {'$exists': True}, 'createdAt': {'$exists': True}},
            {'updatedAt': 1, 'createdAt': 1}
        ))
        
        if resolved_docs:
            total_hours = 0
            for doc in resolved_docs:
                try:
                    if isinstance(doc.get('updatedAt'), datetime) and isinstance(doc.get('createdAt'), datetime):
                        delta = doc['updatedAt'] - doc['createdAt']
                        total_hours += delta.total_seconds() / 3600
                except:
                    pass
            avg_resolution_time = total_hours / len(resolved_docs) if resolved_docs else 0
        
        return {
            'success': True,
            'data': {
                'total_complaints': total,
                'resolved_complaints': resolved,
                'pending_complaints': pending,
                'resolution_rate': round((resolved / total * 100) if total > 0 else 0, 1),
                'priority_distribution': priority_dist,
                'category_distribution': category_dist,
                'region_performance': region_perf,
                'sla_breaches': sla_breaches,
                'avg_resolution_time_hours': round(avg_resolution_time, 1)
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get('/admin/officer-performance')
async def admin_officer_performance(limit: int = Query(20)):
    """Officer ranking leaderboard with performance metrics"""
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        # Officer performance aggregation
        officer_stats = list(complaints_collection.aggregate([
            {
                '$match': {'assigned_officer': {'$ne': None}}
            },
            {
                '$group': {
                    '_id': '$assigned_officer',
                    'total_assigned': {'$sum': 1},
                    'resolved': {
                        '$sum': {'$cond': [{'$in': ['$status', ['resolved', 'closed']]}, 1, 0]}
                    },
                    'avg_rating': {'$avg': '$feedback.rating'}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'officer': '$_id',
                    'total_assigned': 1,
                    'resolved': 1,
                    'resolution_rate': {
                        '$round': [{'$multiply': [
                            {'$divide': ['$resolved', '$total_assigned']}, 100
                        ]}, 1]
                    },
                    'avg_rating': {'$round': ['$avg_rating', 1]},
                    'efficiency_score': {
                        '$round': [
                            {'$add': [
                                {'$multiply': [
                                    {'$divide': ['$resolved', '$total_assigned']}, 60
                                ]},
                                {'$multiply': [
                                    {'$divide': [{'$ifNull': ['$avg_rating', 3.5]}, 5]}, 40
                                ]}
                            ]}, 1
                        ]
                    }
                }
            },
            {'$sort': {'efficiency_score': -1}},
            {'$limit': limit}
        ]))
        
        return {
            'success': True,
            'data': officer_stats
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get('/admin/trends')
async def admin_trends(period: str = Query('daily'), days: int = Query(30)):
    """Daily/Weekly/Monthly trend analysis"""
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        if period == 'daily':
            group_format = '%Y-%m-%d'
        elif period == 'weekly':
            group_format = '%Y-W%V'
        else:  # monthly
            group_format = '%Y-%m'
        
        trends = list(complaints_collection.aggregate([
            {
                '$match': {
                    'createdAt': {'$gte': datetime.now() - timedelta(days=days)}
                }
            },
            {
                '$group': {
                    '_id': {'$dateToString': {'format': group_format, 'date': '$createdAt'}},
                    'total': {'$sum': 1},
                    'resolved': {
                        '$sum': {'$cond': [{'$in': ['$status', ['resolved', 'closed']]}, 1, 0]}
                    },
                    'by_priority': {
                        '$push': {
                            'priority': '$priority',
                            'count': 1
                        }
                    }
                }
            },
            {'$sort': {'_id': 1}}
        ]))
        
        return {
            'success': True,
            'data': trends
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ════════════════════════════════════════════════════════════════
# OFFICER ANALYTICS
# ════════════════════════════════════════════════════════════════

@router.get('/officer/{officer_id}/performance')
async def officer_performance(officer_id: str):
    """Personal performance metrics for officers"""
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        # Get officer's complaints
        total_assigned = complaints_collection.count_documents({'assigned_officer': officer_id})
        resolved = complaints_collection.count_documents({
            'assigned_officer': officer_id,
            'status': {'$in': ['resolved', 'closed']}
        })
        
        pending = total_assigned - resolved
        
        # Calculate stats
        stats = {
            'total_assigned': total_assigned,
            'resolved': resolved,
            'pending': pending,
            'resolution_rate': round((resolved / total_assigned * 100) if total_assigned > 0 else 0, 1),
            'avg_resolution_time': 0,
            'avg_rating': 0,
            'avg_response_time': 0
        }
        
        # Get officer's documents for detailed stats
        officer_docs = list(complaints_collection.find({'assigned_officer': officer_id}))
        
        if officer_docs:
            ratings = []
            total_hours = 0
            resolved_count = 0
            response_times = []
            
            for doc in officer_docs:
                if doc.get('status') in ['resolved', 'closed'] and doc.get('updatedAt') and doc.get('createdAt'):
                    try:
                        delta = doc['updatedAt'] - doc['createdAt']
                        total_hours += delta.total_seconds() / 3600
                        resolved_count += 1
                    except:
                        pass
                
                if doc.get('feedback', {}).get('rating'):
                    ratings.append(doc['feedback']['rating'])
            
            stats['avg_resolution_time'] = total_hours / resolved_count if resolved_count > 0 else 0
            stats['avg_rating'] = sum(ratings) / len(ratings) if ratings else 0
        
        return {
            'success': True,
            'data': {
                'officer_id': officer_id,
                'total_assigned': total_assigned,
                'resolved': resolved,
                'resolution_rate': round((resolved / total_assigned * 100) if total_assigned > 0 else 0, 1),
                'avg_resolution_time_hours': round(stats.get('avg_resolution_time', 0), 1),
                'avg_rating': round(stats.get('avg_rating', 0), 1),
                'efficiency_score': round(
                    ((resolved / total_assigned) * 60 if total_assigned > 0 else 0) +
                    ((stats.get('avg_rating', 0) / 5) * 40),
                    1
                )
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get('/officer/{officer_id}/queue')
async def officer_queue(officer_id: str):
    """Priority queue and SLA status for officer"""
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        # Get pending complaints
        pending = list(complaints_collection.find({
            'assigned_officer': officer_id,
            'status': {'$nin': ['resolved', 'closed']}
        }).sort('priority', -1).limit(20))
        
        # Add SLA status
        for complaint in pending:
            complaint['sla'] = calculate_sla_status(
                complaint.get('createdAt'),
                complaint.get('status'),
                complaint.get('priority', 'low')
            )
            complaint['_id'] = str(complaint.get('_id', ''))
        
        return {
            'success': True,
            'data': pending
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ════════════════════════════════════════════════════════════════
# SHARED ANALYTICS
# ════════════════════════════════════════════════════════════════

@router.post('/filtered')
async def filtered_analytics(filter_req: FilterRequest):
    """
    Get analytics based on custom filters
    """
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        filters = filter_req.dict(exclude_none=True)
        mongo_filter = {}
        
        # Date range
        if 'date_range' in filters and filters['date_range']:
            mongo_filter['createdAt'] = {
                '$gte': datetime.fromisoformat(filters['date_range'].get('start')),
                '$lte': datetime.fromisoformat(filters['date_range'].get('end'))
            }
        
        # Category
        if filters.get('category'):
            mongo_filter['category'] = {'$in': filters['category']}
        
        # Priority
        if filters.get('priority'):
            mongo_filter['priority'] = {'$in': filters['priority']}
        
        # Region
        if filters.get('region'):
            mongo_filter['region'] = {'$in': filters['region']}
        
        # Status
        if filters.get('status'):
            mongo_filter['status'] = {'$in': filters['status']}
        
        # Get statistics
        total = complaints_collection.count_documents(mongo_filter)
        resolved = complaints_collection.count_documents({**mongo_filter, 'status': {'$in': ['resolved', 'closed']}})
        
        # Category breakdown
        categories = list(complaints_collection.aggregate([
            {'$match': mongo_filter},
            {
                '$group': {
                    '_id': '$category',
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}}
        ]))
        
        return {
            'success': True,
            'data': {
                'total': total,
                'resolved': resolved,
                'resolution_rate': round((resolved / total * 100) if total > 0 else 0, 1),
                'category_breakdown': categories
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.post('/export')
async def export_analytics(export_req: ExportRequest):
    """Export analytics data as CSV/JSON"""
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        import csv
        from io import StringIO
        
        # Get data
        data = list(complaints_collection.find({}))
        
        if export_req.format == 'csv':
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=['id', 'category', 'priority', 'status', 'region', 'createdAt'])
            writer.writeheader()
            
            for complaint in data:
                writer.writerow({
                    'id': str(complaint.get('_id', '')),
                    'category': complaint.get('category', ''),
                    'priority': complaint.get('priority', ''),
                    'status': complaint.get('status', ''),
                    'region': complaint.get('region', ''),
                    'createdAt': str(complaint.get('createdAt', ''))
                })
            
            return {'content': output.getvalue(), 'format': 'csv'}
        else:
            # Convert ObjectId to string
            for item in data:
                item['_id'] = str(item.get('_id', ''))
                if isinstance(item.get('createdAt'), datetime):
                    item['createdAt'] = item['createdAt'].isoformat()
            
            return {'success': True, 'data': data}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get('/admin/ngo-contribution')
async def admin_ngo_contribution():
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        pipeline = [
            { '$match': { 'assigned_ngo': { '$ne': None } } },
            {
                '$group': {
                    '_id': '$assigned_ngo',
                    'total_assigned': { '$sum': 1 },
                    'resolved': {
                        '$sum': { '$cond': [{ '$in': ['$status', ['resolved', 'closed']] }, 1, 0] }
                    }
                }
            },
            {
                '$project': {
                    'ngo_id': '$_id',
                    'total_assigned': 1,
                    'resolved': 1,
                    'success_rate': {
                        '$round': [
                            { '$multiply': [{ '$divide': ['$resolved', '$total_assigned'] }, 100] },
                            1
                        ]
                    }
                }
            },
            { '$sort': { 'success_rate': -1 } }
        ]
        
        ngo_stats = list(complaints_collection.aggregate(pipeline))
        return {'success': True, 'data': ngo_stats}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get('/admin/escalation-advanced')
async def admin_escalation_advanced():
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        # Get count of escalating complaints and reason
        escalated = list(complaints_collection.find({ 'escalation_level': { '$gte': 1 } }))
        total_escalated = len(escalated)
        unresolved_sla_breaches = len([c for c in escalated if c.get('status') not in ['resolved', 'closed']])
        
        return {
            'success': True,
            'data': {
                'total_escalated': total_escalated,
                'unresolved_sla_breaches': unresolved_sla_breaches,
                'escalation_list': [
                    {
                        'id': str(c.get('_id')),
                        'grievanceID': c.get('grievanceID', c.get('id')),
                        'category': c.get('category'),
                        'escalation_level': c.get('escalation_level'),
                        'status': c.get('status')
                    } for c in escalated[:50]
                ]
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.get('/admin/peak-times')
async def admin_peak_times():
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        # Basic prediction: Group by hour of day
        pipeline = [
            {
                '$project': {
                    'hour': { '$hour': { 'date': '$createdAt', 'timezone': 'UTC' } } # MongoDB 5.0+ feature
                }
            },
            {
                '$group': {
                    '_id': '$hour',
                    'count': { '$sum': 1 }
                }
            },
            { '$sort': { 'count': -1 } }
        ]
        
        # We'll use python if '$hour' aggregation string fails due to simple schema dates
        data = list(complaints_collection.find({}, {'createdAt': 1}))
        hour_counts = {}
        for d in data:
            if isinstance(d.get('createdAt'), datetime):
                h = d['createdAt'].hour
                hour_counts[h] = hour_counts.get(h, 0) + 1
                
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [{'hour': f"{h:02d}:00", 'count': c} for h, c in sorted_hours[:5]]
        
        return {
            'success': True,
            'data': {
                'peak_hours': peak_hours,
                'prediction': f"High activity detected around {peak_hours[0]['hour'] if peak_hours else 'N/A'}"
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ════════════════════════════════════════════════════════════════
# ADVANCED INTELLIGENCE & RECOMMENDATIONS
# ════════════════════════════════════════════════════════════════

@router.get('/admin/high-risk-zones')
async def admin_high_risk_zones():
    """Detect high-risk zones with frequent complaints"""
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        # Group complaints by region/zone
        zone_data = list(complaints_collection.aggregate([
            {
                '$group': {
                    '_id': '$region',
                    'total_complaints': {'$sum': 1},
                    'pending': {
                        '$sum': {'$cond': [{'$nin': ['$status', ['resolved', 'closed']]}, 1, 0]}
                    },
                    'avg_resolution_time': {'$avg': 1},
                    'emergency_count': {
                        '$sum': {'$cond': [{'$eq': ['$priority', 'emergency']}, 1, 0]}
                    }
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'zone': '$_id',
                    'total_complaints': 1,
                    'pending': 1,
                    'emergency_count': 1,
                    'risk_score': {
                        '$round': [
                            {'$add': [
                                {'$multiply': [{'$divide': ['$emergency_count', {'$max': [1, '$total_complaints']}]}, 40]},
                                {'$multiply': [{'$divide': ['$pending', {'$max': [1, '$total_complaints']}]}, 60]}
                            ]}, 1
                        ]
                    }
                }
            },
            {'$sort': {'risk_score': -1}},
            {'$limit': 10}
        ]))
        
        return {'success': True, 'data': zone_data}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get('/admin/underperforming-officers')
async def admin_underperforming_officers(threshold: float = Query(50.0)):
    """Identify underperforming officers based on resolution rate"""
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        # Get all officers with their stats
        officers = list(complaints_collection.aggregate([
            {'$match': {'assigned_officer': {'$ne': None}}},
            {
                '$group': {
                    '_id': '$assigned_officer',
                    'total_assigned': {'$sum': 1},
                    'resolved': {
                        '$sum': {'$cond': [{'$in': ['$status', ['resolved', 'closed']]}, 1, 0]}
                    },
                    'avg_rating': {'$avg': '$feedback.rating'},
                    'sla_breaches': {
                        '$sum': {'$cond': [
                            {'$and': [
                                {'$nin': ['$status', ['resolved', 'closed']]},
                                {'$lt': [{'$subtract': [datetime.now(), '$createdAt']}, 72 * 3600000]}
                            ]}, 1, 0
                        ]}
                    }
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'officer': '$_id',
                    'total_assigned': 1,
                    'resolved': 1,
                    'resolution_rate': {'$round': [{'$multiply': [{'$divide': ['$resolved', '$total_assigned']}, 100]}, 1]},
                    'avg_rating': {'$round': ['$avg_rating', 1]},
                    'sla_breaches': 1
                }
            },
            {'$match': {'resolution_rate': {'$lt': threshold}}},
            {'$sort': {'resolution_rate': 1}}
        ]))
        
        return {'success': True, 'data': officers, 'threshold': threshold}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get('/admin/resource-recommendations')
async def admin_resource_recommendations():
    """Recommend resource allocation based on demand"""
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        # Get category demand
        categories = list(complaints_collection.aggregate([
            {
                '$group': {
                    '_id': '$category',
                    'total': {'$sum': 1},
                    'pending': {
                        '$sum': {'$cond': [{'$nin': ['$status', ['resolved', 'closed']]}, 1, 0]}
                    },
                    'avg_time': {'$avg': 1}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'category': '$_id',
                    'total': 1,
                    'pending': 1,
                    'avg_time': 1,
                    'allocation_priority': {
                        '$round': [
                            {'$multiply': [
                                {'$divide': ['$pending', {'$max': [1, '$total']}]}, 100
                            ]}, 1
                        ]
                    }
                }
            },
            {'$sort': {'allocation_priority': -1}}
        ]))
        
        recommendations = []
        for cat in categories[:5]:
            if cat['allocation_priority'] > 30:
                recommendations.append({
                    'category': cat['category'],
                    'action': 'INCREASE',
                    'reason': f"High pending rate ({cat['allocation_priority']}%)",
                    'priority': 'HIGH'
                })
            elif cat['allocation_priority'] > 15:
                recommendations.append({
                    'category': cat['category'],
                    'action': 'MAINTAIN',
                    'reason': f"Moderate activity ({cat['allocation_priority']}%)",
                    'priority': 'MEDIUM'
                })
        
        return {'success': True, 'data': recommendations, 'categories': categories}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get('/admin/satisfaction-analysis')
async def admin_satisfaction_analysis():
    """Analyze citizen satisfaction feedback"""
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        # Get satisfaction feedback
        feedback = list(complaints_collection.find(
            {'feedback.rating': {'$exists': True}},
            {'feedback.rating': 1, 'feedback.satisfaction': 1, 'category': 1}
        ))
        
        if not feedback:
            return {'success': True, 'data': {'average_rating': 0, 'satisfaction_breakdown': {}}}
        
        ratings = [f.get('feedback', {}).get('rating', 0) for f in feedback if f.get('feedback', {}).get('rating')]
        
        satisfaction_counts = {}
        for f in feedback:
            satisfaction = f.get('feedback', {}).get('satisfaction', 'Neutral')
            satisfaction_counts[satisfaction] = satisfaction_counts.get(satisfaction, 0) + 1
        
        return {
            'success': True,
            'data': {
                'average_rating': round(sum(ratings) / len(ratings), 2) if ratings else 0,
                'total_feedback': len(feedback),
                'satisfaction_breakdown': satisfaction_counts,
                'ratings_distribution': {
                    '5-stars': len([r for r in ratings if r >= 4.5]),
                    '4-stars': len([r for r in ratings if 3.5 <= r < 4.5]),
                    '3-stars': len([r for r in ratings if 2.5 <= r < 3.5]),
                    '2-stars': len([r for r in ratings if 1.5 <= r < 2.5]),
                    '1-star': len([r for r in ratings if r < 1.5])
                }
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get('/admin/department-performance')
async def admin_department_performance():
    """Compare performance across departments"""
    try:
        from db import db
        complaints_collection = db.get_collection('complaints')
        
        # Assuming category represents department
        dept_perf = list(complaints_collection.aggregate([
            {
                '$group': {
                    '_id': '$category',
                    'total_filed': {'$sum': 1},
                    'resolved': {
                        '$sum': {'$cond': [{'$in': ['$status', ['resolved', 'closed']]}, 1, 0]}
                    },
                    'pending': {
                        '$sum': {'$cond': [{'$nin': ['$status', ['resolved', 'closed']]}, 1, 0]}
                    },
                    'avg_rating': {'$avg': '$feedback.rating'},
                    'emergency_count': {
                        '$sum': {'$cond': [{'$eq': ['$priority', 'emergency']}, 1, 0]}
                    }
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'department': '$_id',
                    'total_filed': 1,
                    'resolved': 1,
                    'pending': 1,
                    'resolution_rate': {'$round': [{'$multiply': [{'$divide': ['$resolved', '$total_filed']}, 100]}, 1]},
                    'avg_rating': {'$round': ['$avg_rating', 1]},
                    'emergency_count': 1,
                    'performance_score': {
                        '$round': [
                            {'$add': [
                                {'$multiply': [{'$divide': ['$resolved', '$total_filed']}, 70]},
                                {'$multiply': [{'$divide': [{'$ifNull': ['$avg_rating', 3.5]}, 5]}, 30]}
                            ]}, 1
                        ]
                    }
                }
            },
            {'$sort': {'performance_score': -1}}
        ]))
        
        return {'success': True, 'data': dept_perf}
    except Exception as e:
        return {'success': False, 'error': str(e)}
