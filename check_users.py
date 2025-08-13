#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.user import User

def check_users():
    app = create_app()
    with app.app_context():
        users = User.query.all()
        print(f"数据库中共有 {len(users)} 个用户:")
        print("-" * 50)
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"username: {user.username}")
            print(f"email: {user.email}")
            print(f"create time: {user.created_at}")
            print(f"photo: {user.avatar or '未设置'}")
            print(f"profile: {user.bio or '未设置'}")
            print(f"location: {user.location or '未设置'}")
            print(f"password_hash: {user.password_hash or '未设置'}")
            print("-" * 50)

if __name__ == '__main__':
    check_users()