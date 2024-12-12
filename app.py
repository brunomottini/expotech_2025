import os
from dotenv import load_dotenv, find_dotenv
import openai

from datetime import datetime
import pandas as pd

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    session,
    url_for,
    stream_with_context,
    Response,
)

import markdown2
import uuid
import re
from agent import create_agent
from grafo_agente import create_graph
from azure_database import load_table_to_dataframe, connect_db

# Varibles de ambiente
_ = load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.environ["OPENAI_API_KEY"]

# LANGSMITH
LANGCHAIN_TRACING_V2 = True
LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
LANGCHAIN_API_KEY = os.environ["LANGCHAIN_API_KEY"]
LANGCHAIN_PROJECT = "Expotech25"


# ---------------------------------------------------------------------    ARQUITECTURA DE LA WEB   ---------------------------------

app = Flask(__name__)
app.secret_key = "expotech_2025"


@app.route("/")
def login():
    session["session"] = session.get("id", str(uuid.uuid4()))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def log_in():
    # Info form
    name = request.form.get("name")
    password = request.form.get("password")
    session["session"] = session.get("id", str(uuid.uuid4()))

    # Info csv
    ds = pd.read_csv("tablas/login.csv", sep=",")
    # chequeo usuario
    if len(ds[(ds.name == name) & (ds.password == password)]) == 1:
        return redirect("/home")
    else:
        return redirect("/")


@app.route("/home")
def home():

    df_espacios = load_table_to_dataframe("expo25_espacios")
    if df_espacios is None or df_espacios.empty:
        print("Tabla de espacios vacia")
        espacios_lista = []
    else:
        espacios_lista = df_espacios.values.tolist()

    # Obtener el parámetro 'success' del request
    success = request.args.get("success", None)

    # Renderizar la plantilla HTML y pasar los datos de usuarios al frontend
    return render_template("home.html", espacios=espacios_lista, success=success)


@app.route("/agregar_espacio", methods=["POST"])
def agregar_espacio():
    # Obtener datos del formulario
    print("Se recivio mensaje del front")

    id_espacio = request.form.get("id_espacio")
    id_ocupado = request.form.get("id_ocupado", None)
    id_empresa = request.form.get("id_empresa", None)
    nombre_empresa = request.form.get("nombre_empresa", None)

    try:
        # Conectar a la base de datos
        conn = connect_db()
        cursor = conn.cursor()

        # Verificar si el ID de espacio ya existe
        cursor.execute(
            "SELECT COUNT(*) FROM expo25_espacios WHERE id_espacio = ?", (id_espacio,)
        )
        existe = cursor.fetchone()[0] > 0

        if existe:
            # Actualizar los campos si se proporcionaron
            query = """
            UPDATE expo25_espacios
            SET ocupado = COALESCE(?, ocupado),
                id_empresa = COALESCE(?, id_empresa),
                nombre_empresa = COALESCE(?, nombre_empresa)
            WHERE id_espacio = ?
            """
            cursor.execute(query, (id_ocupado, id_empresa, nombre_empresa, id_espacio))
        else:
            # Insertar nuevo registro con valores por defecto si faltan campos
            query = """
            INSERT INTO expo25_espacios (id_espacio, ocupado, id_empresa, nombre_empresa)
            VALUES (?, ?, ?, ?)
            """
            cursor.execute(
                query,
                (
                    id_espacio,
                    (
                        id_ocupado if id_ocupado else "No"
                    ),  # Valor por defecto para ocupado
                    id_empresa,  # Puede ser NULL
                    nombre_empresa,  # Puede ser NULL
                ),
            )

        # Guardar cambios y cerrar conexión
        conn.commit()
        conn.close()

        # Redirigir a /home con mensaje de éxito
        return redirect(url_for("home", success="True"))
    except Exception as e:
        print(f"Error al insertar/actualizar datos: {e}")
        return redirect(url_for("home", success="False"))


@app.route("/chat")
def muestra_chat():
    return render_template("chat.html")


@app.route("/respuesta", methods=["GET", "POST"])
def chat():
    # Sesion
    # session["session"] = session.get("id", str(uuid.uuid4()))
    session_id = session.get("session")
    print(session_id)

    # Mensaje de entrada
    msg = request.form["msg"]
    input = msg

    # GRAFO AGENTE
    config = {"configurable": {"thread_id": session_id}}
    grafo = create_graph()

    # Respuesta invoke
    estado_final = grafo.invoke(
        {
            "messages": input,
        },
        config,
    )
    print("Estado final:", estado_final)

    # Respuesta Texto
    last_answer = estado_final["messages"][-1].content
    respuesta_texto = markdown2.markdown(last_answer)

    # Logica fotos respuesta
    empresas_totales = estado_final["empresas"]
    # Definir una expresión regular que coincida con diferentes variaciones de "visnai"

    keywords = ["VisnAI", "Visn AI", "Visn ai", "Visnai"]
    # Verificar si alguno de los elementos de `keywords` está en `total_empresas`
    if any(keyword in empresas_totales for keyword in keywords):
        empresas = ["visnai_logo.png"]
    else:
        empresas = None

    # Logica links
    links = estado_final["links"]
    # print(links)

    return [respuesta_texto, empresas, None]

    # # AGENTE AI
    # # Fecha
    # fecha_actual = datetime.now().strftime("%d/%m/%Y")
    # fecha_actual_texto = datetime.now().strftime("%A, %B %d, %Y")

    # agente = create_agent()
    # answer = agente.invoke(
    #     {
    #         "input": input,
    #         "fecha_actual": fecha_actual,
    #         "fecha_actual_texto": fecha_actual_texto,
    #     },
    #     config={"configurable": {"session_id": session_id}},
    # )
    # respuesta_markdown = answer["output"]
    # respuesta_texto = markdown2.markdown(respuesta_markdown)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
