from database import db
from datetime import datetime
import uuid

# Association table for event participants
event_participants = db.Table('event_participants',
    db.Column('user_id', db.String(36), db.ForeignKey('user.id'), primary_key=True),
    db.Column('event_id', db.String(36), db.ForeignKey('event.id'), primary_key=True)
)

class Event(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    time = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    max_participants = db.Column(db.Integer, default=10)
    budget_per_person = db.Column(db.Float, default=0.0)
    image = db.Column(db.String(255), default='')
    status = db.Column(db.String(20), default='active')  # active, cancelled, completed
    creator_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participants = db.relationship('User', secondary=event_participants, back_populates='joined_events')
    chat_messages = db.relationship('ChatMessage', backref='event', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        # 组合日期和时间为前端期望的datetime格式
        datetime_str = f"{self.date.strftime('%Y-%m-%d')} {self.time}"
        
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'cate': self.category,  # 前端期望的字段别名
            'date': self.date.isoformat(),
            'time': self.time,
            'datetime': datetime_str,  # 前端期望的组合字段
            'location': self.location,
            'place': self.location,  # 前端期望的字段别名
            'max_participants': self.max_participants,
            'cap': self.max_participants,  # 前端期望的字段别名
            'budget_per_person': self.budget_per_person,
            'budget': self.budget_per_person,  # 前端期望的字段别名
            'image': self.image,
            'img': self.image,  # 前端期望的字段别名
            'image_url': self.image,  # API返回字段
            'status': self.status,
            'creator_id': self.creator_id,
            'creator': self.creator.to_dict() if self.creator else None,
            'participants_count': len(self.participants),
            'joined': len(self.participants),  # 前端期望的字段别名
            'participants': [p.to_dict() for p in self.participants],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'desc': self.description  # 前端期望的字段别名
        }