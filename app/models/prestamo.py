from datetime import datetime, timezone

from app import db


class Prestamo(db.Model):
    __tablename__ = "prestamos"

    id_prestamo = db.Column(db.Integer, primary_key=True)
    id_libro = db.Column(
        db.Integer,
        db.ForeignKey("libros.id_libro"),
        nullable=False,
    )
    id_lector = db.Column(
        db.Integer,
        db.ForeignKey("lectores.id_lector"),
        nullable=False,
    )
    fecha_prestamo = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    fecha_devolucion = db.Column(db.DateTime)

    libro = db.relationship("Libro", backref="prestamos")
    lector = db.relationship("Lector", backref="prestamos")
