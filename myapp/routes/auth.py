from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.get("/ping")
def ping():
    return {"auth": "ok"}
