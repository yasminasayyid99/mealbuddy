#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.user import User
from models.event import Event
from models.chat import ChatMessage

def init_database():
    app = create_app()
    with app.app_context():
        print("正在创建数据库表...")
        db.create_all()
        print("数据库表创建完成！")
        
        # 检查表是否创建成功
        users = User.query.all()
        print(f"用户表已创建，当前用户数量: {len(users)}")

if __name__ == '__main__':
    init_database()