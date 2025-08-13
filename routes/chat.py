from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.chat import ChatMessage
from models.event import Event
from models.user import User
from app import db
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/<string:event_id>', methods=['GET'])
@jwt_required()
def get_chat_messages(event_id):
    """Get chat messages for an event"""
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get_or_404(event_id)
        user = User.query.get(current_user_id)
        
        # Check if user is participant or creator
        if user not in event.participants and event.creator_id != current_user_id:
            return jsonify({'error': 'You must be a participant to view chat messages'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # 修复：Chat -> ChatMessage
        messages = ChatMessage.query.filter_by(event_id=event_id)\
                            .order_by(ChatMessage.created_at.desc())\
                            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'messages': [message.to_dict() for message in reversed(messages.items)],
            'total': messages.total,
            'pages': messages.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/<string:event_id>', methods=['POST'])
@jwt_required()
def send_message(event_id):
    """Send a message to event chat"""
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get_or_404(event_id)
        user = User.query.get(current_user_id)
        
        # Check if user is participant or creator
        if user not in event.participants and event.creator_id != current_user_id:
            return jsonify({'error': 'You must be a participant to send messages'}), 403
        
        data = request.get_json()
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return jsonify({'error': 'Message content cannot be empty'}), 400
        
        if len(message_content) > 1000:
            return jsonify({'error': 'Message is too long (max 1000 characters)'}), 400
        
        # 修复：Chat -> ChatMessage，并且字段名也需要修改
        message = ChatMessage(
            event_id=event_id,
            sender_id=current_user_id,  # 修复：user_id -> sender_id
            content=message_content,    # 修复：message -> content
            created_at=datetime.utcnow()  # 修复：timestamp -> created_at
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'message': 'Message sent successfully',
            'chat_message': message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get all conversations (events with messages) for current user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Get all events where user is participant or creator
        user_events = list(user.joined_events)
        created_events = Event.query.filter_by(creator_id=current_user_id).all()
        
        # Combine and deduplicate
        all_events = list(set(user_events + created_events))
        
        conversations = []
        for event in all_events:
            # 修复：Chat -> ChatMessage，timestamp -> created_at
            latest_message = ChatMessage.query.filter_by(event_id=event.id)\
                                     .order_by(ChatMessage.created_at.desc())\
                                     .first()
            
            # Get unread message count (assuming we track read status)
            unread_count = ChatMessage.query.filter_by(event_id=event.id)\
                                   .filter(ChatMessage.created_at > user.last_seen.get(str(event.id), datetime.min))\
                                   .count() if hasattr(user, 'last_seen') else 0
            
            conversation = {
                'event': event.to_dict(),
                'latest_message': latest_message.to_dict() if latest_message else None,
                'unread_count': unread_count
            }
            conversations.append(conversation)
        
        # Sort by latest message timestamp
        conversations.sort(
            key=lambda x: x['latest_message']['created_at'] if x['latest_message'] else datetime.min,  # 修复：timestamp -> created_at
            reverse=True
        )
        
        return jsonify({'conversations': conversations}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/<string:event_id>/history', methods=['GET'])
@jwt_required()
def get_chat_history(event_id):
    """Get complete chat history for an event"""
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get_or_404(event_id)
        user = User.query.get(current_user_id)
        
        # Check if user is participant or creator
        if user not in event.participants and event.creator_id != current_user_id:
            return jsonify({'error': 'You must be a participant to view chat history'}), 403
        
        # 修复：Chat -> ChatMessage，timestamp -> created_at
        messages = ChatMessage.query.filter_by(event_id=event_id)\
                            .order_by(ChatMessage.created_at.asc())\
                            .all()
        
        return jsonify({
            'event': event.to_dict(),
            'messages': [message.to_dict() for message in messages],
            'total_messages': len(messages)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/<int:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    """Delete a chat message (only sender can delete)"""
    try:
        current_user_id = get_jwt_identity()
        # 修复：Chat -> ChatMessage
        message = ChatMessage.query.get_or_404(message_id)
        
        # 修复：user_id -> sender_id
        if message.sender_id != current_user_id:
            return jsonify({'error': 'You can only delete your own messages'}), 403
        
        # 修复：timestamp -> created_at
        time_diff = datetime.utcnow() - message.created_at
        if time_diff.total_seconds() > 86400:  # 24 hours
            return jsonify({'error': 'Cannot delete messages older than 24 hours'}), 400
        
        db.session.delete(message)
        db.session.commit()
        
        return jsonify({'message': 'Message deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500