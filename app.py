import os
from dotenv import load_dotenv, find_dotenv
import openai

from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    session,
    url_for,
)

import markdown2

from agent import create_agent


# Varibles de ambiente
_ = load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.environ["OPENAI_API_KEY"]


# ---------------------------------------------------------------------    ARQUITECTURA DE LA WEB   ---------------------------------

app = Flask(__name__)
app.secret_key = "expotech_2025"


@app.route("/")
def login():
    return render_template("chat.html")


@app.route("/respuesta", methods=["GET", "POST"])
def chat():
    # Sesion
    session_id = 1988

    # Mensaje de entrada
    msg = request.form["msg"]
    input = msg

    # FECHAS
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    fecha_actual_texto = datetime.now().strftime("%A, %B %d, %Y")

    # AGENTE AI
    agente = create_agent()
    answer = agente.invoke(
        {
            "input": input,
            "fecha_actual": fecha_actual,
            "fecha_actual_texto": fecha_actual_texto,
        },
        config={"configurable": {"session_id": session_id}},
    )
    respuesta_markdown = answer["output"]

    respuesta_texto = markdown2.markdown(respuesta_markdown)

    return [respuesta_texto, None]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
