from database import db
from datetime import datetime
import uuid

class ChatMessage(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, image, system
    sender_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.String(36), db.ForeignKey('event.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Note: Relationships are defined in User and Event models
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'message_type': self.message_type,
            'sender_id': self.sender_id,
            'sender': self.sender.to_dict() if self.sender else None,
            'event_id': self.event_id,
            'created_at': self.created_at.isoformat()
        }