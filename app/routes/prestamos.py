from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.libro import Libro
from app.models.lector import Lector
from app.models.prestamo import Prestamo

prestamos_bp = Blueprint(
    "prestamos", __name__, url_prefix="/prestamos"
)


# READ - Listar préstamos
@prestamos_bp.route("/")
def index():
    prestamos = Prestamo.query.order_by(
        Prestamo.id_prestamo.desc()
    ).all()

    libros = Libro.query.filter_by(disponible=True).all()
    lectores = Lector.query.filter_by(activo=True).all()

    return render_template(
        "prestamos/index.html",
        prestamos=prestamos,
        libros=libros,
        lectores=lectores
    )


# CREATE - Registrar préstamo
@prestamos_bp.post("/registrar")
def registrar():
    try:
        id_libro = int(request.form["id_libro"])
        id_lector = int(request.form["id_lector"])
    except (ValueError, KeyError):
        return "Datos inválidos", 400

    lector = db.session.get(Lector, id_lector)

    if not lector or not lector.activo:
        return "Lector no disponible", 400

    resultado = db.session.execute(
        update(Libro)
        .where(
            Libro.id_libro == id_libro,
            Libro.disponible.is_(True)
        )
        .values(disponible=False)
    )

    if resultado.rowcount != 1:
        db.session.rollback()
        return "Libro no disponible", 409

    prestamo = Prestamo(
        id_libro=id_libro,
        id_lector=id_lector
    )

    db.session.add(prestamo)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return "Error al registrar préstamo", 409

    return redirect(url_for("prestamos.index"))


# UPDATE - Editar préstamo
@prestamos_bp.route(
    "/editar/<int:id_prestamo>",
    methods=["GET", "POST"]
)
def editar(id_prestamo):
    prestamo = db.get_or_404(Prestamo, id_prestamo)

    # No editar préstamos ya devueltos
    if prestamo.fecha_devolucion is not None:
        return "No se puede editar un préstamo finalizado", 400

    if request.method == "POST":
        try:
            nuevo_libro = int(request.form["id_libro"])
            nuevo_lector = int(request.form["id_lector"])
        except (ValueError, KeyError):
            return "Datos inválidos", 400

        lector = db.session.get(Lector, nuevo_lector)

        if not lector or not lector.activo:
            return "Lector no disponible", 400

        if nuevo_libro != prestamo.id_libro:
            resultado = db.session.execute(
                update(Libro)
                .where(
                    Libro.id_libro == nuevo_libro,
                    Libro.disponible.is_(True)
                )
                .values(disponible=False)
            )

            if resultado.rowcount != 1:
                db.session.rollback()
                return "El nuevo libro no está disponible", 409

            libro_anterior = db.session.get(
                Libro, prestamo.id_libro
            )

            if libro_anterior:
                libro_anterior.disponible = True

            prestamo.id_libro = nuevo_libro

        prestamo.id_lector = nuevo_lector

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return "Error al editar préstamo", 409

        return redirect(url_for("prestamos.index"))

    libros = Libro.query.filter(
        (Libro.disponible.is_(True)) |
        (Libro.id_libro == prestamo.id_libro)
    ).all()

    lectores = Lector.query.filter(
        (Lector.activo.is_(True)) |
        (Lector.id_lector == prestamo.id_lector)
    ).all()

    return render_template(
        "prestamos/editar.html",
        prestamo=prestamo,
        libros=libros,
        lectores=lectores
    )


# Registrar devolución
@prestamos_bp.post("/devolver/<int:id_prestamo>")
def devolver(id_prestamo):
    prestamo = db.get_or_404(Prestamo, id_prestamo)

    if prestamo.fecha_devolucion is None:
        prestamo.fecha_devolucion = (
            datetime.now(timezone.utc).replace(tzinfo=None)
        )

        libro = db.session.get(Libro, prestamo.id_libro)

        if libro:
            libro.disponible = True

        db.session.commit()

    return redirect(url_for("prestamos.index"))


# DELETE - Eliminar préstamo
@prestamos_bp.post("/eliminar/<int:id_prestamo>")
def eliminar(id_prestamo):
    prestamo = db.get_or_404(Prestamo, id_prestamo)

    # Liberar el libro solo si el préstamo sigue activo
    if prestamo.fecha_devolucion is None:
        libro = db.session.get(Libro, prestamo.id_libro)

        if libro:
            libro.disponible = True

    db.session.delete(prestamo)
    db.session.commit()

    return redirect(url_for("prestamos.index"))