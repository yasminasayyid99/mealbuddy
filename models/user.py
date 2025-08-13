from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

# Association table for saved events
saved_events = db.Table('saved_events',
    db.Column('user_id', db.String(36), db.ForeignKey('user.id'), primary_key=True),
    db.Column('event_id', db.String(36), db.ForeignKey('event.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255), default='')
    bio = db.Column(db.Text, default='')
    dietary_preferences = db.Column(db.JSON, default=list)
    location = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_events = db.relationship('Event', backref='creator', lazy=True, foreign_keys='Event.creator_id')
    joined_events = db.relationship('Event', secondary='event_participants', back_populates='participants')
    saved_events = db.relationship('Event', secondary=saved_events, lazy='dynamic')
    chat_messages = db.relationship('ChatMessage', backref='sender', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'bio': self.bio,
            'dietary_preferences': self.dietary_preferences,
            'location': self.location,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }