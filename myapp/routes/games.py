from flask import Blueprint, request, current_app as app, url_for
from urllib.parse import urlparse
from myapp.db import db
from myapp.models import Game
import os
import uuid
from werkzeug.utils import secure_filename

bp = Blueprint("games", __name__, url_prefix="/games")


def _validate_name(name):
    if not name or not isinstance(name, str) or not name.strip():
        return "El nombre es obligatorio."
    if len(name.strip()) > 120:
        return "El nombre no puede superar 120 caracteres."
    return None


def _normalize_url(u):
    if not u:
        return None
    u = u.strip()
    p = urlparse(u)
    if not p.scheme:
        # si el usuario pone "wikipedia.org/..." añadimos https://
        u = "https://" + u
    return u


def _allowed_file(filename: str):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "webp"})


def _save_image(file_storage, subdir="covers"):
    original = secure_filename(file_storage.filename)
    ext = (original.rsplit(".", 1)[-1].lower() if "." in original else "jpg")
    filename = f"{uuid.uuid4().hex}.{ext}"

    root = app.config["UPLOAD_FOLDER"]
    folder = os.path.join(root, subdir)
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, filename)
    file_storage.save(path)

    return url_for("uploaded_file", subpath=f"{subdir}/{filename}", _external=True)


@bp.get("")
def list_games():
    # paginación básica
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return {"msg": "limit/offset deben ser enteros."}, 400

    q = Game.query.order_by(Game.id).offset(offset).limit(limit).all()
    total = db.session.query(db.func.count(Game.id)).scalar()

    return {
        "items": [g.to_dict() for g in q],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@bp.get("/<int:game_id>")
def get_game(game_id: int):
    g = Game.query.get_or_404(game_id)
    return g.to_dict()


@bp.post("")
def create_game():
    # Detecta tipo de contenido
    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    if is_multipart:
        data = request.form or {}
        file = request.files.get("image")
    else:
        data = request.get_json(silent=True) or {}
        file = None

    name = data.get("name")
    genre = data.get("genre")
    url = _normalize_url(data.get("url"))
    image_url = data.get("image_url")

    err = _validate_name(name)
    if err:
        return {"msg": err}, 400

    if file and file.filename:
        if not _allowed_file(file.filename):
            return {"msg": "Extensión no permitida"}, 400
        image_url = _save_image(file, subdir="covers")

    g = Game(
        name=name.strip(),
        genre=(genre or None),
        url=url,
        image_url=image_url,
    )

    db.session.add(g)
    db.session.commit()

    return g.to_dict(), 201


@bp.patch("/<int:game_id>")
def update_game(game_id: int):
    g = Game.query.get_or_404(game_id)

    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    if is_multipart:
        data = request.form or {}
        file = request.files.get("image")
    else:
        data = request.get_json(silent=True) or {}
        file = None

    if "name" in data:
        err = _validate_name(data["name"])
        if err:
            return {"msg": err}, 400
        g.name = data["name"].strip() if data["name"] else g.name

    if "genre" in data:
        g.genre = data["genre"] or None

    if "url" in data:
        g.url = _normalize_url(data["url"])

    if "image_url" in data:
        g.image_url = data["image_url"] or None

    if file and file.filename:
        if not _allowed_file(file.filename):
            return {"msg": "Extensión no permitida"}, 400
        g.image_url = _save_image(file, subdir="covers")

    db.session.commit()
    return g.to_dict()


@bp.delete("/<int:game_id>")
def delete_game(game_id: int):
    g = Game.query.get_or_404(game_id)
    db.session.delete(g)
    db.session.commit()
    return {"deleted": game_id}


@bp.post("/upload")
def upload_image():
    if "image" not in request.files:
        return {"msg": "Falta campo 'image' (multipart/form-data)"}, 400

    file = request.files["image"]

    if not file.filename:
        return {"msg": "Nombre de archivo vacío"}, 400

    if not _allowed_file(file.filename):
        return {"msg": "Extensión no permitida"}, 400

    url = _save_image(file, subdir="covers")
    return {"url": url}, 201
