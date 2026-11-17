from flask import Blueprint, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.lector import Lector


lectores_bp = Blueprint("lectores", __name__, url_prefix="/lectores")


def _lector_formulario(lector=None):
    if request.method == "POST":
        return {
            "nombre": request.form.get("nombre", "").strip(),
            "correo": request.form.get("correo", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
        }

    return {
        "nombre": lector.nombre if lector else "",
        "correo": lector.correo if lector else "",
        "telefono": lector.telefono or "" if lector else "",
    }


def _listar_lectores(formulario=None, status=200, mensaje=None, categoria="danger"):
    return (
        render_template(
            "lectores/index.html",
            lectores=Lector.query.order_by(Lector.nombre.asc()).all(),
            formulario=formulario or _lector_formulario(),
            mensaje=mensaje,
            categoria=categoria,
            abrir_modal=status >= 400 and formulario is not None,
        ),
        status,
    )


def _editar_lector(lector, formulario, status=200, mensaje=None, categoria="danger"):
    return (
        render_template(
            "lectores/editar.html",
            lector=lector,
            formulario=formulario,
            mensaje=mensaje,
            categoria=categoria,
        ),
        status,
    )


@lectores_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        mensajes = {
            "agregado": "El lector se agregó correctamente.",
            "actualizado": "El lector se actualizó correctamente.",
            "eliminado": "El lector se eliminó correctamente.",
            "estado": "El estado del lector se actualizó correctamente.",
        }
        estado = request.args.get("estado")
        return _listar_lectores(
            mensaje=mensajes.get(estado),
            categoria="success",
        )

    formulario = _lector_formulario()
    if not formulario["nombre"] or not formulario["correo"]:
        return _listar_lectores(
            formulario,
            400,
            "El nombre y el correo son obligatorios.",
        )

    if Lector.query.filter_by(correo=formulario["correo"]).first():
        return _listar_lectores(
            formulario,
            409,
            "Ya existe un lector registrado con ese correo.",
        )

    db.session.add(
        Lector(
            nombre=formulario["nombre"],
            correo=formulario["correo"],
            telefono=formulario["telefono"] or None,
            activo=True,
        )
    )
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _listar_lectores(
            formulario,
            409,
            "Ya existe un lector registrado con ese correo.",
        )

    return redirect(url_for("lectores.index", estado="agregado"))


@lectores_bp.route("/<int:id_lector>/editar", methods=["GET", "POST"])
def editar(id_lector):
    lector = db.get_or_404(Lector, id_lector)
    formulario = _lector_formulario(lector)

    if request.method == "GET":
        return _editar_lector(lector, formulario)

    formulario = _lector_formulario()
    if not formulario["nombre"] or not formulario["correo"]:
        return _editar_lector(
            lector,
            formulario,
            400,
            "El nombre y el correo son obligatorios.",
        )

    if Lector.query.filter(
        Lector.correo == formulario["correo"],
        Lector.id_lector != lector.id_lector,
    ).first():
        return _editar_lector(
            lector,
            formulario,
            409,
            "Ya existe otro lector registrado con ese correo.",
        )

    lector.nombre = formulario["nombre"]
    lector.correo = formulario["correo"]
    lector.telefono = formulario["telefono"] or None

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _editar_lector(
            lector,
            formulario,
            409,
            "Ya existe otro lector registrado con ese correo.",
        )

    return redirect(url_for("lectores.index", estado="actualizado"))


@lectores_bp.post("/<int:id_lector>/estado")
def cambiar_estado(id_lector):
    lector = db.get_or_404(Lector, id_lector)
    lector.activo = not lector.activo
    db.session.commit()
    return redirect(url_for("lectores.index", estado="estado"))


@lectores_bp.post("/<int:id_lector>/eliminar")
def eliminar(id_lector):
    lector = db.get_or_404(Lector, id_lector)
    db.session.delete(lector)
    db.session.commit()
    return redirect(url_for("lectores.index", estado="eliminado"))