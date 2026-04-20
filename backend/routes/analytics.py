"""
Advanced Analytics Module for JanSamadhan
Provides comprehensive data-driven insights for Officers and Admins
"""

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from functools import lru_cache
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
        from ..db import complaints_collection, users_collection
        
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
        
        # SLA breaches
        sla_breaches = complaints_collection.count_documents({
            'status': {'$nin': ['resolved', 'closed']},
            'createdAt': {'$lt': datetime.now() - timedelta(hours=72)}
        })
        
        # Average resolution time
        resolved_complaints = list(complaints_collection.aggregate([
            {'$match': {'status': {'$in': ['resolved', 'closed']}}},
            {
                '$group': {
                    '_id': None,
                    'avg_resolution_hours': {
                        '$avg': {
                            '$divide': [
                                {'$subtract': ['$updatedAt', '$createdAt']},
                                3600000  # Convert ms to hours
                            ]
                        }
                    }
                }
            }
        ]))
        
        avg_resolution_time = resolved_complaints[0]['avg_resolution_hours'] if resolved_complaints else 0
        
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
        from ..db import complaints_collection, users_collection
        
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
        from ..db import complaints_collection
        
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
        from ..db import complaints_collection
        
        # Get officer's complaints
        total_assigned = complaints_collection.count_documents({'assigned_officer': officer_id})
        resolved = complaints_collection.count_documents({
            'assigned_officer': officer_id,
            'status': {'$in': ['resolved', 'closed']}
        })
        
        # Calculate stats
        stats = list(complaints_collection.aggregate([
            {'$match': {'assigned_officer': officer_id}},
            {
                '$group': {
                    '_id': None,
                    'avg_resolution_time': {
                        '$avg': {
                            '$cond': [
                                {'$in': ['$status', ['resolved', 'closed']]},
                                {'$divide': [{'$subtract': ['$updatedAt', '$createdAt']}, 3600000]},
                                None
                            ]
                        }
                    },
                    'avg_rating': {'$avg': '$feedback.rating'},
                    'total': {'$sum': 1},
                    'pending': {
                        '$sum': {'$cond': [{'$nin': ['$status', ['resolved', 'closed']]}, 1, 0]}
                    }
                }
            }
        ]))
        
        data = stats[0] if stats else {
            'avg_resolution_time': 0,
            'avg_rating': 0,
            'total': 0,
            'pending': 0
        }
        
        return {
            'success': True,
            'data': {
                'officer_id': officer_id,
                'total_assigned': total_assigned,
                'resolved': resolved,
                'resolution_rate': round((resolved / total_assigned * 100) if total_assigned > 0 else 0, 1),
                'avg_resolution_time_hours': round(data.get('avg_resolution_time', 0), 1),
                'avg_rating': round(data.get('avg_rating', 0), 1),
                'efficiency_score': round(
                    ((resolved / total_assigned) * 60 if total_assigned > 0 else 0) +
                    ((data.get('avg_rating', 0) / 5) * 40),
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
        from ..db import complaints_collection
        
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
        from ..db import complaints_collection
        
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
        from ..db import complaints_collection
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
                    'createdAt': complaint.get('createdAt', '')
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
