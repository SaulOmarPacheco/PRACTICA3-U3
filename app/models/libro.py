from app import db


class Libro(db.Model):
    __tablename__ = "libros"

    id_libro = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    disponible = db.Column(db.Boolean, default=True, nullable=False)
