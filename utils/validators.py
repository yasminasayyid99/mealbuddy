import re
from email_validator import validate_email as email_validate, EmailNotValidError

def validate_email(email):
    """Validate email format"""
    try:
        # Allow test domains and disable deliverability check for development
        email_validate(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 6:
        return False
    return True

def validate_username(username):
    """Validate username format"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    # Allow letters, numbers, and underscores
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None

def validate_event_data(data):
    """Validate event creation data"""
    required_fields = ['title', 'category', 'date', 'time', 'location']
    
    for field in required_fields:
        if not data.get(field):
            return False, f'{field} is required'
    
    if len(data['title']) < 3:
        return False, 'Title must be at least 3 characters long'
    
    if data.get('max_participants', 0) < 1:
        return False, 'Max participants must be at least 1'
    
    return True, 'Valid'