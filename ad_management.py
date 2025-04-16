"""
Advertisement Management System for Snap Lotto
Provides comprehensive advertisement management, analytics, and optimization features
"""

import os
import json
import datetime
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_, or_
from werkzeug.utils import secure_filename

from models import Advertisement, Campaign, AdVariation, AdImpression, db

# Create blueprint
ad_management = Blueprint('ad_management', __name__)

def calculate_ctr(impressions: int, clicks: int) -> float:
    """Calculate click-through rate"""
    if impressions == 0:
        return 0
    return (clicks / impressions) * 100

def get_trend_percentage(current: float, previous: float) -> float:
    """Calculate percentage trend between two values"""
    if previous == 0:
        return 100 if current > 0 else 0
    return ((current - previous) / previous) * 100

def get_date_range_data(days: int = 30) -> Tuple[datetime, datetime]:
    """Get start and end dates for date range queries"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def format_currency(value: float) -> str:
    """Format a value as currency"""
    return f"${value:,.2f}"

def calculate_roi(revenue: float, cost: float) -> float:
    """Calculate ROI percentage"""
    if cost == 0:
        return 0
    return ((revenue - cost) / cost) * 100

@ad_management.route('/admin/ads', methods=['GET'])
@login_required
def manage_ads(placement=None):
    """Display advertisement management dashboard"""
    placement_filter = request.args.get('placement')
    status_filter = request.args.get('status')
    
    # Base query
    query = Advertisement.query
    
    # Apply filters
    if placement_filter:
        query = query.filter(Advertisement.placement == placement_filter)
    
    if status_filter:
        is_active = status_filter == 'active'
        query = query.filter(Advertisement.active == is_active)
    
    # Get ads with total impressions and clicks
    ads = query.all()
    
    # Get counts for filter badges
    counts = {
        'total': Advertisement.query.count(),
        'active': Advertisement.query.filter_by(active=True).count(),
        'inactive': Advertisement.query.filter_by(active=False).count(),
        'scanner': Advertisement.query.filter_by(placement='scanner').count(),
        'results': Advertisement.query.filter_by(placement='results').count(),
        'header': Advertisement.query.filter_by(placement='header').count()
    }
    
    return render_template(
        'admin/manage_ads.html', 
        ads=ads,
        counts=counts,
        placement_filter=placement_filter,
        status_filter=status_filter
    )

@ad_management.route('/admin/ads/performance', methods=['GET'])
@login_required
def ad_performance():
    """Display advertisement performance analytics"""
    days = int(request.args.get('days', 30))
    start_date, end_date = get_date_range_data(days)
    
    # Get impressions over time
    impression_data = db.session.query(
        func.date(AdImpression.timestamp).label('date'),
        func.count(AdImpression.id).label('count')
    ).filter(
        AdImpression.timestamp.between(start_date, end_date)
    ).group_by(
        func.date(AdImpression.timestamp)
    ).order_by(
        func.date(AdImpression.timestamp)
    ).all()
    
    impression_dates = [str(data.date) for data in impression_data]
    impression_counts = [data.count for data in impression_data]
    
    # Get current period total impressions
    current_period_impressions = sum(impression_counts) if impression_counts else 0
    
    # Get previous period impressions for trend calculation
    previous_start_date = start_date - timedelta(days=days)
    previous_end_date = end_date - timedelta(days=days)
    
    previous_period_impressions = db.session.query(
        func.count(AdImpression.id)
    ).filter(
        AdImpression.timestamp.between(previous_start_date, previous_end_date)
    ).scalar() or 0
    
    # Calculate trend
    impression_trend = None
    if previous_period_impressions > 0:
        impression_trend = get_trend_percentage(current_period_impressions, previous_period_impressions)
    
    # Get top ads by CTR
    ads_with_metrics = db.session.query(
        Advertisement,
        func.count(AdImpression.id).label('impressions'),
        func.sum(AdImpression.was_clicked).label('clicks')
    ).join(
        AdImpression, Advertisement.id == AdImpression.ad_id
    ).filter(
        AdImpression.timestamp.between(start_date, end_date)
    ).group_by(
        Advertisement.id
    ).having(
        func.count(AdImpression.id) > 0
    ).all()
    
    # Convert to list of dictionaries for sorting
    ads_metrics = []
    for ad, impressions, clicks in ads_with_metrics:
        clicks = clicks or 0  # Handle None values
        ctr = calculate_ctr(impressions, clicks)
        ads_metrics.append({
            'id': ad.id,
            'name': ad.name,
            'impressions': impressions,
            'clicks': clicks,
            'ctr': ctr
        })
    
    # Sort for top performers
    top_ads_by_ctr = sorted(ads_metrics, key=lambda x: x['ctr'], reverse=True)[:5]
    top_ads_by_impressions = sorted(ads_metrics, key=lambda x: x['impressions'], reverse=True)[:5]
    
    # Get placement statistics
    placement_stats = db.session.query(
        Advertisement.placement,
        func.count(AdImpression.id).label('impressions'),
        func.sum(AdImpression.was_clicked).label('clicks')
    ).join(
        AdImpression, Advertisement.id == AdImpression.ad_id
    ).filter(
        AdImpression.timestamp.between(start_date, end_date)
    ).group_by(
        Advertisement.placement
    ).all()
    
    placement_stats_data = []
    for placement, impressions, clicks in placement_stats:
        clicks = clicks or 0  # Handle None values
        ctr = calculate_ctr(impressions, clicks)
        placement_stats_data.append({
            'placement': placement,
            'impressions': impressions,
            'clicks': clicks,
            'ctr': ctr
        })
    
    return render_template(
        'admin/ad_performance.html',
        days=days,
        impression_dates=impression_dates,
        impression_counts=impression_counts,
        current_period_impressions=current_period_impressions,
        impression_trend=impression_trend,
        top_ads_by_ctr=top_ads_by_ctr,
        top_ads_by_impressions=top_ads_by_impressions,
        placement_stats=placement_stats_data
    )

@ad_management.route('/admin/campaigns', methods=['GET'])
@login_required
def manage_campaigns():
    """Display campaign management dashboard"""
    campaigns = Campaign.query.all()
    
    # Enrich campaign data with metrics
    for campaign in campaigns:
        # Count associated ads
        campaign.ad_count = Advertisement.query.filter_by(campaign_id=campaign.id).count()
        
        # Get impression and click data
        impression_data = db.session.query(
            func.count(AdImpression.id).label('impressions'),
            func.sum(AdImpression.was_clicked).label('clicks')
        ).join(
            Advertisement, AdImpression.ad_id == Advertisement.id
        ).filter(
            Advertisement.campaign_id == campaign.id
        ).first()
        
        campaign.impressions = impression_data.impressions if impression_data else 0
        campaign.clicks = impression_data.clicks if impression_data and impression_data.clicks else 0
        
        # Calculate CTR
        campaign.ctr = calculate_ctr(campaign.impressions, campaign.clicks)
        
        # Calculate progress based on target impressions or dates
        if campaign.target_impressions and campaign.target_impressions > 0:
            campaign.progress = (campaign.impressions / campaign.target_impressions) * 100
        elif campaign.start_date and campaign.end_date:
            total_days = (campaign.end_date - campaign.start_date).days
            if total_days > 0:
                days_passed = (datetime.now().date() - campaign.start_date).days
                campaign.progress = min(100, max(0, (days_passed / total_days) * 100))
        else:
            campaign.progress = 0
    
    return render_template('admin/manage_campaigns.html', campaigns=campaigns)

@ad_management.route('/admin/campaigns/create', methods=['GET', 'POST'])
@login_required
def create_campaign():
    """Create a new campaign"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        budget = request.form.get('budget')
        active = 'active' in request.form
        target_impressions = request.form.get('target_impressions')
        target_ctr = request.form.get('target_ctr')
        priority = request.form.get('priority')
        tags = request.form.get('tags')
        
        # Validate required fields
        if not name:
            flash('Campaign name is required', 'danger')
            return redirect(url_for('ad_management.create_campaign'))
        
        # Parse dates
        start_date = None
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
        end_date = None
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
        # Create new campaign
        campaign = Campaign(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            budget=float(budget) if budget else None,
            status='active' if active else 'draft',
            created_by_id=current_user.id
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        flash(f'Campaign "{name}" created successfully', 'success')
        return redirect(url_for('ad_management.manage_campaigns'))
    
    return render_template('admin/create_campaign.html')

@ad_management.route('/admin/campaigns/<int:campaign_id>', methods=['GET'])
@login_required
def campaign_details(campaign_id):
    """View campaign details and performance"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Since campaign_id field is commented out in Advertisement model, 
    # we can't use this filter yet
    # ads = Advertisement.query.filter_by(campaign_id=campaign_id).all()
    ads = []
    
    # Get impression and click data
    # Since campaign_id field is commented out in Advertisement model, 
    # we need to use the AdImpression's campaign_id instead
    impression_data = db.session.query(
        func.date(AdImpression.timestamp).label('date'),
        func.count(AdImpression.id).label('impressions'),
        func.sum(AdImpression.was_clicked).label('clicks')
    ).filter(
        AdImpression.campaign_id == campaign_id
    ).group_by(
        func.date(AdImpression.timestamp)
    ).order_by(
        func.date(AdImpression.timestamp)
    ).all()
    
    # Format for charts
    dates = [str(data.date) for data in impression_data]
    impressions = [data.impressions for data in impression_data]
    clicks = [data.clicks or 0 for data in impression_data]
    
    # Calculate performance metrics
    total_impressions = sum(impressions) if impressions else 0
    total_clicks = sum(clicks) if clicks else 0
    ctr = calculate_ctr(total_impressions, total_clicks)
    
    return render_template(
        'admin/campaign_details.html',
        campaign=campaign,
        ads=ads,
        dates=dates,
        impressions=impressions,
        clicks=clicks,
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        ctr=ctr
    )

@ad_management.route('/admin/campaigns/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    """Edit an existing campaign"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if request.method == 'POST':
        campaign.name = request.form.get('name')
        campaign.description = request.form.get('description')
        
        start_date_str = request.form.get('start_date')
        if start_date_str:
            campaign.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            campaign.start_date = None
            
        end_date_str = request.form.get('end_date')
        if end_date_str:
            campaign.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            campaign.end_date = None
            
        budget = request.form.get('budget')
        campaign.budget = float(budget) if budget else None
        
        campaign.status = 'active' if 'active' in request.form else 'draft'
        
        target_impressions = request.form.get('target_impressions')
        campaign.target_impressions = int(target_impressions) if target_impressions else None
        
        target_ctr = request.form.get('target_ctr')
        campaign.target_ctr = float(target_ctr) if target_ctr else None
        
        priority = request.form.get('priority')
        campaign.priority = int(priority) if priority else 5
        
        campaign.tags = request.form.get('tags')
        
        db.session.commit()
        
        flash(f'Campaign "{campaign.name}" updated successfully', 'success')
        return redirect(url_for('ad_management.campaign_details', campaign_id=campaign.id))
    
    return render_template('admin/edit_campaign.html', campaign=campaign)

@ad_management.route('/admin/campaigns/delete', methods=['POST'])
@login_required
def delete_campaign():
    """Delete a campaign"""
    campaign_id = request.form.get('campaign_id')
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Since campaign_id field is commented out in Advertisement model,
    # we can't use this filter yet
    # ads = Advertisement.query.filter_by(campaign_id=campaign_id).all()
    # for ad in ads:
    #     ad.campaign_id = None
    
    # Delete campaign
    db.session.delete(campaign)
    db.session.commit()
    
    flash(f'Campaign "{campaign.name}" deleted successfully', 'success')
    return redirect(url_for('ad_management.manage_campaigns'))

@ad_management.route('/admin/ads/upload', methods=['GET', 'POST'])
@login_required
def upload_ad():
    """Display and process ad upload form"""
    campaigns = Campaign.query.filter_by(status='active').order_by(Campaign.name).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        placement = request.form.get('placement')
        duration = request.form.get('duration')
        campaign_id = request.form.get('campaign_id') or None
        
        # Handle file upload
        file = request.files.get('ad_file')
        file_path = None
        
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            # Set path relative to static directory
            relative_path = os.path.join('ads', filename)
            file_path = relative_path
            
            # Ensure directory exists
            os.makedirs(os.path.join(current_app.static_folder, 'ads'), exist_ok=True)
            
            # Save file
            file.save(os.path.join(current_app.static_folder, relative_path))
        
        # Create ad record
        ad = Advertisement(
            name=name,
            description=description,
            placement=placement,
            file_path=file_path,
            duration=int(duration) if duration else 15,
            # campaign_id is commented out in the Advertisement model
            # campaign_id=int(campaign_id) if campaign_id else None,
            active=True,
            created_by_id=current_user.id,
            created_at=datetime.now()
        )
        
        db.session.add(ad)
        db.session.commit()
        
        flash(f'Advertisement "{name}" uploaded successfully', 'success')
        return redirect(url_for('ad_management.manage_ads'))
    
    return render_template('admin/upload_ad.html', campaigns=campaigns)

@ad_management.route('/admin/ads/<int:ad_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ad(ad_id):
    """Edit an existing advertisement"""
    ad = Advertisement.query.get_or_404(ad_id)
    campaigns = Campaign.query.filter_by(status='active').order_by(Campaign.name).all()
    
    if request.method == 'POST':
        ad.name = request.form.get('name')
        ad.description = request.form.get('description')
        ad.placement = request.form.get('placement')
        ad.duration = int(request.form.get('duration')) if request.form.get('duration') else 15
        # campaign_id is commented out in the Advertisement model
        # ad.campaign_id = int(request.form.get('campaign_id')) if request.form.get('campaign_id') else None
        ad.active = 'active' in request.form
        
        # Handle file upload if new file provided
        file = request.files.get('ad_file')
        if file and file.filename:
            # Delete old file if it exists
            if ad.file_path:
                old_file_path = os.path.join(current_app.static_folder, ad.file_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            filename = secure_filename(file.filename)
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            # Set path relative to static directory
            relative_path = os.path.join('ads', filename)
            ad.file_path = relative_path
            
            # Ensure directory exists
            os.makedirs(os.path.join(current_app.static_folder, 'ads'), exist_ok=True)
            
            # Save file
            file.save(os.path.join(current_app.static_folder, relative_path))
        
        db.session.commit()
        
        flash(f'Advertisement "{ad.name}" updated successfully', 'success')
        return redirect(url_for('ad_management.manage_ads'))
    
    # Get impression and click data
    impression_data = db.session.query(
        func.count(AdImpression.id).label('impressions'),
        func.sum(AdImpression.was_clicked).label('clicks')
    ).filter(
        AdImpression.ad_id == ad_id
    ).first()
    
    impressions = impression_data.impressions if impression_data else 0
    clicks = impression_data.clicks if impression_data and impression_data.clicks else 0
    ctr = calculate_ctr(impressions, clicks)
    
    return render_template(
        'admin/edit_ad.html', 
        ad=ad, 
        campaigns=campaigns,
        impressions=impressions,
        clicks=clicks,
        ctr=ctr
    )

@ad_management.route('/admin/ads/<int:ad_id>/preview', methods=['GET'])
@login_required
def preview_ad(ad_id):
    """Preview an advertisement"""
    ad = Advertisement.query.get_or_404(ad_id)
    return render_template('admin/preview_ad.html', ad=ad)

@ad_management.route('/admin/ads/delete', methods=['POST'])
@login_required
def delete_ad():
    """Delete an advertisement"""
    ad_id = request.form.get('ad_id')
    ad = Advertisement.query.get_or_404(ad_id)
    
    # Delete file if exists
    if ad.file_path:
        file_path = os.path.join(current_app.static_folder, ad.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.session.delete(ad)
    db.session.commit()
    
    flash(f'Advertisement "{ad.name}" deleted successfully', 'success')
    return redirect(url_for('ad_management.manage_ads'))

@ad_management.route('/admin/ads/abtests', methods=['GET'])
@login_required
def manage_ab_tests():
    """Display A/B testing dashboard"""
    return render_template('admin/manage_ab_tests.html')

@ad_management.route('/admin/ads/audience', methods=['GET'])
@login_required
def audience_insights():
    """Display audience insights dashboard"""
    return render_template('admin/audience_insights.html')

@ad_management.route('/admin/ads/revenue', methods=['GET'])
@login_required
def ad_revenue():
    """Display revenue analytics dashboard"""
    return render_template('admin/ad_revenue.html')

def register_ad_routes(app):
    """Register all advertisement management routes with the app"""
    app.register_blueprint(ad_management)