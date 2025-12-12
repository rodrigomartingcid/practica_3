# myapp/routes/users.py
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError
from myapp.db import db
from myapp.models import User

bp = Blueprint("users", __name__, url_prefix="/users")

def _validate_username(u: str | None):
    if not u or not isinstance(u, str) or not u.strip():
        return "El nombre de usuario es obligatorio."
    if len(u.strip()) > 80:
        return "El nombre de usuario no puede superar 80 caracteres."
    return None

@bp.get("")
def list_users():
    # ?limit=&offset=&q=
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return {"msg": "limit/offset deben ser enteros."}, 400

    q_text = (request.args.get("q") or "").strip()
    query = User.query
    if q_text:
        query = query.filter(User.username.ilike(f"%{q_text}%"))

    rows = query.order_by(User.id).offset(offset).limit(limit).all()
    total = query.count()
    return {
        "items": [{"id": u.id, "username": u.username, "created_at": u.created_at.isoformat()} for u in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@bp.post("")
def create_user():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    err = _validate_username(username)
    if err:
        return {"msg": err}, 400
    if not password or not isinstance(password, str) or not password.strip():
        return {"msg": "La contraseña es obligatoria."}, 400

    u = User(username=username.strip())
    u.set_password(password.strip())
    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"msg": "Ya existe un usuario con ese nombre."}, 409

    return {"id": u.id, "username": u.username, "created_at": u.created_at.isoformat()}, 201

@bp.patch("/<int:user_id>")
def update_user(user_id: int):
    u = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}

    if "username" in data:
        err = _validate_username(data.get("username"))
        if err:
            return {"msg": err}, 400
        u.username = data["username"].strip()

    if "password" in data:
        pwd = data.get("password")
        if not pwd or not isinstance(pwd, str) or not pwd.strip():
            return {"msg": "La contraseña no puede ser vacía."}, 400
        u.set_password(pwd.strip())

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"msg": "Ya existe un usuario con ese nombre."}, 409

    return {"id": u.id, "username": u.username, "created_at": u.created_at.isoformat()}

@bp.delete("/<int:user_id>")
def delete_user(user_id: int):
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    return {"deleted": user_id}
