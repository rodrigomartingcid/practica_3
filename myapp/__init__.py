# myapp/__init__.py
from flask import Flask, send_from_directory
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from pathlib import Path
from flask_cors import CORS
from .db import db
from .config import Config

migrate = None

def create_app():
    load_dotenv()
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config.from_object(Config) 

    # --- UPLOADS: ruta absoluta y asegurarse de que existe ---
    raw_upload = getattr(Config, "UPLOAD_FOLDER", "uploads")
    upload_dir = Path(raw_upload)
    if not upload_dir.is_absolute():
        upload_dir = Path(app.root_path).parent / "uploads"  # garantizamos que apunta a backend-flask/uploads
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_dir)

    # Mostrar ruta de uploads en consola para depuración
    print("UPLOAD_FOLDER =>", app.config["UPLOAD_FOLDER"])

    # --- CORS (solo para API) ---
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    print("ENV DATABASE_URL:", os.getenv("DATABASE_URL"))
    print("ENV SQLALCHEMY_DATABASE_URI:", os.getenv("SQLALCHEMY_DATABASE_URI"))
    print("CFG SQLALCHEMY_DATABASE_URI BEFORE INIT:", app.config.get("SQLALCHEMY_DATABASE_URI"))

    
    # --- Inicialización de DB y migraciones ---
    db.init_app(app)
    global migrate
    migrate = Migrate(app, db)

    # Cargar modelos
    with app.app_context():
        from myapp import models  # noqa

    # --- Registrar blueprints ---
    from myapp.routes import auth, games, users
    app.register_blueprint(auth.bp,  url_prefix="/api" + auth.bp.url_prefix)
    app.register_blueprint(games.bp, url_prefix="/api" + games.bp.url_prefix)
    app.register_blueprint(users.bp, url_prefix="/api" + users.bp.url_prefix)

    # --- Endpoints auxiliares ---
    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/uploads/<path:subpath>")
    def uploaded_file(subpath):
        """Sirve archivos desde UPLOAD_FOLDER."""
        return send_from_directory(app.config["UPLOAD_FOLDER"], subpath, as_attachment=False)

    @app.get("/uploads-debug")
    def uploads_debug():
        """Muestra información de depuración sobre los ficheros subidos."""
        base = Path(app.config["UPLOAD_FOLDER"])
        covers = base / "covers"
        return {
            "UPLOAD_FOLDER": str(base),
            "covers_exists": covers.exists(),
            "covers_count": len(list(covers.glob('*'))) if covers.exists() else 0,
            "covers_sample": [p.name for p in list(covers.glob('*'))[:5]],
        }

    # --- Servir el frontend (build de Vue) ---
    @app.get("/")
    def index():
        try:
            return send_from_directory(app.static_folder, "index.html")
        except Exception:
            return {
                "message": "Backend vivo. Sube el build del frontend a /myapp/static."
            }, 200

    return app






