# myapp/models.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from myapp import db

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.Index("ix_users_username", "username", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Game(db.Model):
    __tablename__ = "games"
    __table_args__ = (db.Index("ix_games_name", "name", unique=True),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    genre = db.Column(db.String(80))
    url = db.Column(db.String(255))  
    image_url = db.Column(db.String(255))  
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "genre": self.genre,
            "url": self.url,  
            "description": self.description,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat(),
        }


