from flask import Blueprint, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.libro import Libro


libros_bp = Blueprint("libros", __name__, url_prefix="/libros")


def _libro_formulario(libro=None):
    if request.method == "POST":
        return {
            "titulo": request.form.get("titulo", "").strip(),
            "autor": request.form.get("autor", "").strip(),
            "isbn": request.form.get("isbn", "").strip(),
            "disponible": request.form.get("disponible", "true"),
        }

    return {
        "titulo": libro.titulo if libro else "",
        "autor": libro.autor if libro else "",
        "isbn": libro.isbn or "" if libro else "",
        "disponible": str(libro.disponible).lower() if libro else "true",
    }


def _listar_libros(formulario=None, status=200, mensaje=None, categoria="danger"):
    return (
        render_template(
            "libros/index.html",
            libros=Libro.query.order_by(Libro.titulo.asc()).all(),
            formulario=formulario or _libro_formulario(),
            mensaje=mensaje,
            categoria=categoria,
            abrir_modal=status >= 400 and formulario is not None,
        ),
        status,
    )


def _editar_libro(libro, formulario, status=200, mensaje=None, categoria="danger"):
    return (
        render_template(
            "libros/editar.html",
            libro=libro,
            formulario=formulario,
            mensaje=mensaje,
            categoria=categoria,
        ),
        status,
    )


@libros_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        mensajes = {
            "agregado": "El libro se agregó correctamente.",
            "actualizado": "El libro se actualizó correctamente.",
            "eliminado": "El libro se eliminó correctamente.",
        }
        estado = request.args.get("estado")
        return _listar_libros(
            mensaje=mensajes.get(estado),
            categoria="success",
        )

    formulario = _libro_formulario()
    if not formulario["titulo"] or not formulario["autor"]:
        return _listar_libros(
            formulario,
            400,
            "El título y el autor son obligatorios.",
        )

    isbn = formulario["isbn"] or None
    if isbn and Libro.query.filter_by(isbn=isbn).first():
        return _listar_libros(
            formulario,
            409,
            "Ya existe un libro registrado con ese ISBN.",
        )

    db.session.add(
        Libro(
            titulo=formulario["titulo"],
            autor=formulario["autor"],
            isbn=isbn,
        )
    )
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _listar_libros(
            formulario,
            409,
            "Ya existe un libro registrado con ese ISBN.",
        )

    return redirect(url_for("libros.index", estado="agregado"))


@libros_bp.route("/<int:id_libro>/editar", methods=["GET", "POST"])
def editar(id_libro):
    libro = db.get_or_404(Libro, id_libro)
    formulario = _libro_formulario(libro)

    if request.method == "GET":
        return _editar_libro(libro, formulario)

    formulario = _libro_formulario()
    if not formulario["titulo"] or not formulario["autor"]:
        return _editar_libro(
            libro,
            formulario,
            400,
            "El título y el autor son obligatorios.",
        )

    if formulario["disponible"] not in ("true", "false"):
        return _editar_libro(
            libro,
            formulario,
            400,
            "Selecciona un estado de disponibilidad válido.",
        )

    isbn = formulario["isbn"] or None
    if isbn and Libro.query.filter(
        Libro.isbn == isbn,
        Libro.id_libro != libro.id_libro,
    ).first():
        return _editar_libro(
            libro,
            formulario,
            409,
            "Ya existe otro libro registrado con ese ISBN.",
        )

    libro.titulo = formulario["titulo"]
    libro.autor = formulario["autor"]
    libro.isbn = isbn
    libro.disponible = formulario["disponible"] == "true"

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _editar_libro(
            libro,
            formulario,
            409,
            "Ya existe otro libro registrado con ese ISBN.",
        )

    return redirect(url_for("libros.index", estado="actualizado"))


@libros_bp.post("/<int:id_libro>/eliminar")
def eliminar(id_libro):
    libro = db.get_or_404(Libro, id_libro)
    db.session.delete(libro)
    db.session.commit()
    return redirect(url_for("libros.index", estado="eliminado"))
