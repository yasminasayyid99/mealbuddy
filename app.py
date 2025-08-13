import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

from config import Config
from database import db

jwt = JWTManager()
# Use eventlet so Socket.IO works with Gunicorn -k eventlet
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Safety net: fall back to SQLite if DB URL missing ---
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        os.makedirs(app.instance_path, exist_ok=True)
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{os.path.join(app.instance_path, 'mealbuddy.db')}"
        )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Blueprints
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

    # Uploads dir
    upload_dir = os.path.join(app.instance_path, app.config.get("UPLOAD_FOLDER", "uploads"))
    os.makedirs(upload_dir, exist_ok=True)

    # Create tables (wrapped so a DB hiccup doesn’t crash boot)
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        app.logger.warning("DB bootstrap skipped: %s", e)

    # Health & root
    @app.get("/")
    def root():
        return jsonify(ok=True)

    @app.get("/api/health")
    def health():
        return {"status": "healthy", "message": "MealBuddy Flask API is running"}, 200

    return app

# WSGI entrypoint for Gunicorn
app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=False)
