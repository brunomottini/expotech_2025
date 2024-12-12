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
    stream_with_context,
    Response,
)

import markdown2
import uuid
import re
from agent import create_agent
from grafo_agente import create_graph

# Varibles de ambiente
_ = load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.environ["OPENAI_API_KEY"]

# LANGSMITH
LANGCHAIN_TRACING_V2 = True
LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
LANGCHAIN_API_KEY = "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"
LANGCHAIN_PROJECT = "Expotech25"


# ---------------------------------------------------------------------    ARQUITECTURA DE LA WEB   ---------------------------------

app = Flask(__name__)
app.secret_key = "expotech_2025"


@app.route("/")
def login():
    session["session"] = session.get("id", str(uuid.uuid4()))
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
