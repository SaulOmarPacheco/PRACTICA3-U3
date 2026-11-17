import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

from dotenv import load_dotenv 

#Cargar las variables de entorno
load_dotenv()

#crear instancia
app =  Flask(__name__)

# Configuración de la base de datos PostgreSQL
from urllib.parse import quote

database_url = os.getenv("DATABASE_URL")

if os.getenv("DB_HOST"):
    with open(os.environ["DB_PASSWORD_FILE"]) as f:
        password = quote(f.read().strip(), safe="")

    database_url = (
        f"postgresql+psycopg://{os.getenv('DB_USER')}:{password}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}"
        f"/{os.getenv('DB_NAME')}"
    )

app.config['SQLALCHEMY_DATABASE_URI'] = database_url


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Registrar blueprints
from app.routes.home import home_bp
from app.routes.libros import libros_bp

app.register_blueprint(home_bp)
app.register_blueprint(libros_bp)

with app.app_context():
    try:
      from app.models import libro, lector, prestamo  # noqa: F401
    except ImportError:
      pass

    db.create_all()