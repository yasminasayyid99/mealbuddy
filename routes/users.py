from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from app import db

users_bp = Blueprint('users', __name__)

@users_bp.route('/users/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get current user's profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/users/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """Update current user's profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        data = request.get_json()
        
        # 更新用户信息
        if 'username' in data:
            # 检查用户名是否已存在
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != current_user_id:
                return jsonify({'error': 'Username already exists'}), 400
            user.username = data['username']
        
        if 'email' in data:
            # 检查邮箱是否已存在
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != current_user_id:
                return jsonify({'error': 'Email already exists'}), 400
            user.email = data['email']
        
        if 'avatar' in data:
            user.avatar = data['avatar']
        
        if 'bio' in data:
            user.bio = data['bio']
        
        if 'dietary_preferences' in data:
            user.dietary_preferences = data['dietary_preferences']
        
        if 'location' in data:
            user.location = data['location']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500