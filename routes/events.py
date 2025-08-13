from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.event import Event
from models.user import User
from app import db
from utils.validators import validate_event_data
from utils.helpers import allowed_file
import os
from werkzeug.utils import secure_filename
from datetime import datetime

events_bp = Blueprint('events', __name__)

@events_bp.route('', methods=['GET'])
def get_events():
    """Get all events with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)  # 增加默认每页数量以显示更多事件
        keyword = request.args.get('keyword', '')
        filter_type = request.args.get('filter', 'all')
        
        query = Event.query
        
        # Apply keyword search
        if keyword:
            query = query.filter(
                Event.title.contains(keyword) | 
                Event.description.contains(keyword) |
                Event.location.contains(keyword)
            )
        
        # Apply filters
        if filter_type == 'upcoming':
            query = query.filter(Event.date > datetime.utcnow())
        elif filter_type == 'past':
            query = query.filter(Event.date < datetime.utcnow())
        
        # Order by date
        query = query.order_by(Event.date.desc())
        
        # Paginate
        events = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'events': [event.to_dict() for event in events.items],
            'total': events.total,
            'pages': events.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_bp.route('', methods=['POST', 'OPTIONS'])
def create_event():
    if request.method == 'OPTIONS':
        return '', 200
    
    """Create a new event"""
    # JWT is required for POST requests
    from flask_jwt_extended import verify_jwt_in_request
    verify_jwt_in_request()
    
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # 处理前端发送的数据格式
        datetime_str = data.get('datetime')
        if datetime_str:
            # 解析前端的datetime格式 "YYYY-MM-DD HH:MM"
            try:
                event_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                date_part = event_datetime.date()
                time_part = event_datetime.strftime('%H:%M')
            except ValueError:
                return jsonify({'error': 'Invalid datetime format. Expected: YYYY-MM-DD HH:MM'}), 400
        else:
            return jsonify({'error': 'datetime field is required'}), 400
        
        # Create new event
        event = Event(
            title=data.get('title', ''),
            description=data.get('description', ''),
            category=data.get('category', ''),
            date=date_part,
            time=time_part,
            location=data.get('location', ''),
            max_participants=data.get('max_participants', 10),
            budget_per_person=data.get('budget', 0.0),
            image=data.get('image_url', ''),
            creator_id=current_user_id
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'message': 'Event created successfully',
            'id': event.id,
            'title': event.title,
            'category': event.category,
            'location': event.location,
            'datetime': datetime_str,
            'budget': event.budget_per_person,
            'max_participants': event.max_participants,
            'description': event.description,
            'image_url': event.image
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<string:event_id>', methods=['GET'])
def get_event(event_id):
    """Get a specific event by ID"""
    try:
        event = Event.query.get_or_404(event_id)
        return jsonify({'event': event.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<string:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    """Update an event (only creator can update)"""
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get_or_404(event_id)
        
        # Check if user is the creator
        if event.creator_id != current_user_id:
            return jsonify({'error': 'Only the event creator can update this event'}), 403
        
        data = request.get_json()
        
        # Validate event data
        validation_error = validate_event_data(data)
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        # Update event fields
        event.title = data.get('title', event.title)
        event.description = data.get('description', event.description)
        if 'date_time' in data:
            event.date_time = datetime.fromisoformat(data['date_time'].replace('Z', '+00:00'))
        event.location = data.get('location', event.location)
        event.max_participants = data.get('max_participants', event.max_participants)
        event.image_url = data.get('image_url', event.image_url)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Event updated successfully',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<string:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    """Delete an event (only creator can delete)"""
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get_or_404(event_id)
        
        # Check if user is the creator
        if event.creator_id != current_user_id:
            return jsonify({'error': 'Only the event creator can delete this event'}), 403
        
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({'message': 'Event deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<string:event_id>/join', methods=['POST', 'OPTIONS'])
@jwt_required(optional=True)
def join_event(event_id):
    """Join an event"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # For POST requests, verify JWT is required
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request()
        
        current_user_id = get_jwt_identity()
        event = Event.query.get_or_404(event_id)
        user = User.query.get(current_user_id)
        
        # Check if user is the creator
        if event.creator_id == current_user_id:
            return jsonify({'error': 'You cannot join your own event. You are already the creator.'}), 400
        
        # Check if event is full
        if len(event.participants) >= event.max_participants:
            return jsonify({'error': 'Event is full'}), 400
        
        # Check if user already joined
        if user in event.participants:
            return jsonify({'error': 'You have already joined this event'}), 400
        
        # Add user to event participants
        event.participants.append(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Successfully joined the event',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<string:event_id>/leave', methods=['DELETE'])
@jwt_required()
def leave_event(event_id):
    """Leave an event"""
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get_or_404(event_id)
        user = User.query.get(current_user_id)
        
        # Check if user is in the event
        if user not in event.participants:
            return jsonify({'error': 'You are not a participant of this event'}), 400
        
        # Remove user from event participants
        event.participants.remove(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Successfully left the event',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/my-events', methods=['GET'])
@jwt_required()
def get_my_events():
    """Get events created by current user"""
    try:
        current_user_id = get_jwt_identity()
        events = Event.query.filter_by(creator_id=current_user_id).order_by(Event.date_time.desc()).all()
        
        return jsonify({
            'events': [event.to_dict() for event in events]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_bp.route('/joined', methods=['GET'])
@jwt_required()
def get_joined_events():
    """Get events joined by current user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        return jsonify({
            'events': [event.to_dict() for event in user.joined_events]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<string:event_id>/save', methods=['POST'])
@jwt_required()
def save_event(event_id):
    """Save an event to user's saved list"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        event = Event.query.get_or_404(event_id)
        
        # Check if event is already saved
        if event in user.saved_events:
            return jsonify({'error': 'Event is already saved'}), 400
        
        # Add event to saved list
        user.saved_events.append(event)
        db.session.commit()
        
        return jsonify({
            'message': 'Event saved successfully',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<string:event_id>/unsave', methods=['DELETE'])
@jwt_required()
def unsave_event(event_id):
    """Remove an event from user's saved list"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        event = Event.query.get_or_404(event_id)
        
        # Check if event is in saved list
        if event not in user.saved_events:
            return jsonify({'error': 'Event is not in saved list'}), 400
        
        # Remove event from saved list
        user.saved_events.remove(event)
        db.session.commit()
        
        return jsonify({
            'message': 'Event removed from saved list',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/saved', methods=['GET'])
@jwt_required()
def get_saved_events():
    """Get events saved by current user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        return jsonify({
            'events': [event.to_dict() for event in user.saved_events]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500