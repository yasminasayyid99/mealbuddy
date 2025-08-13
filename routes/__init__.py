from flask import Flask
from .auth import auth_bp
from .events import events_bp
from .chat import chat_bp
from .ai import ai_bp
from .upload import upload_bp
from .users import users_bp

def register_blueprints(app: Flask):
    """Register all blueprints with the Flask app"""
    
    # Authentication routes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Events routes
    app.register_blueprint(events_bp, url_prefix='/api')
    
    # Chat routes
    app.register_blueprint(chat_bp, url_prefix='/api')
    
    # AI routes
    app.register_blueprint(ai_bp, url_prefix='/api')
    
    # Upload routes
    app.register_blueprint(upload_bp, url_prefix='/api')
    
    # Users routes
    app.register_blueprint(users_bp, url_prefix='/api')
    
    print("All blueprints registered successfully")