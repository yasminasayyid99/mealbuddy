import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

from config import Config
from database import db

# ---- Extensions ----
jwt = JWTManager()
# IMPORTANT: eventlet async mode so websockets work in Azure with Gunicorn -k eventlet
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)   # attaches Socket.IO to this app
    migrate.init_app(app, db)
    CORS(app)

    # ---- Blueprints ----
    from routes.auth import auth_bp
    from routes.events import events_bp
    from routes.chat import chat_bp
    from routes.ai import ai_bp
    from routes.upload import upload_bp
    from routes.users import users_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(upload_bp, url_prefix="/api/upload")
    app.register_blueprint(users_bp, url_prefix="/api/users")

    # ---- Instance/Uploads dir ----
    upload_dir = os.path.join(app.instance_path, app.config.get("UPLOAD_FOLDER", "uploads"))
    os.makedirs(upload_dir, exist_ok=True)

    # ---- DB bootstrap (okay for your project; migrations still supported) ----
    with app.app_context():
        db.create_all()

    # ---- Health check ----
    @app.get("/api/health")
    def health_check():
        return {"status": "healthy", "message": "MealBuddy Flask API is running"}, 200

    return app


# Expose the WSGI app for Gunicorn: app:app
app = create_app()

# Local/dev run (Gunicorn won't execute this block)
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=False)
