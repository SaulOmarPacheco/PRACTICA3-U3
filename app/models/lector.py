from app import db


class Lector(db.Model):
    __tablename__ = "lectores"

    id_lector = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True, nullable=False)
