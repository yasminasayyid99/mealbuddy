from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.ai_service import ai_service
from models.user import User

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def ai_chat():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get user context for better recommendations
        context_parts = []
        if user.dietary_preferences:
            context_parts.append(f"User dietary preferences: {', '.join(user.dietary_preferences)}")
        if user.location:
            context_parts.append(f"User location: {user.location}")
        
        context = "; ".join(context_parts) if context_parts else None
        
        # Get AI response
        result = ai_service.chat_completion(message, context)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'usage': result.get('usage', {})
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/recommendations', methods=['POST'])
@jwt_required()
def get_recommendations():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        location = data.get('location') or user.location
        budget = data.get('budget')
        preferences = data.get('preferences') or user.dietary_preferences
        
        result = ai_service.get_food_recommendation(preferences, location, budget)
        
        if result['success']:
            return jsonify({
                'recommendations': result['message'],
                'usage': result.get('usage', {})
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/event-suggestions', methods=['POST'])
@jwt_required()
def get_event_suggestions():
    try:
        data = request.get_json()
        category = data.get('category', '')
        participants_count = data.get('participants_count')
        
        if not category:
            return jsonify({'error': 'Category is required'}), 400
        
        result = ai_service.get_event_suggestions(category, participants_count)
        
        if result['success']:
            return jsonify({
                'suggestions': result['message'],
                'usage': result.get('usage', {})
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500