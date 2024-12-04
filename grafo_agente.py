# Importaciones de Librerías Estándar
from datetime import datetime, timedelta
from ast import literal_eval
from typing import Annotated
from typing_extensions import TypedDict
import os
import openai

# Importaciones de Librerías de Terceros
from dotenv import load_dotenv, find_dotenv
import pyodbc

# Importaciones de Paquetes de LangChain
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages


# Importaciones de Scripts Internos
from chromadb_store import genereate_chroma_retriever
from azure_database import connect_db
from send_mail import enviar_mail_confirmacion
from azure_ai_search import create_azure_ai_search_vs

# Comentadas (Pendientes de Revisión o Eliminación)
# from langgraph.graph import MessagesState
# from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
# from langchain.tools.render import format_tool_to_openai_function


# from langchain_google_community import GmailToolkit
# from langchain_google_community.gmail.utils import (
#     build_resource_service,
#     get_gmail_credentials,
# )


# Varibles de ambiente
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ["OPENAI_API_KEY"]


#####################                      ESTADO                        ##############################


class expo_state(TypedDict):
    session_id: str
    messages: Annotated[list, add_messages]
    empresas: list


#######################                    TOOLS                     ##############################


#  -    -   -   -   -   -   -   -    AZURE AI SEARCH    -   -   -   -   -   -   -   -   -   -   -


@tool("retriever_azure_search", return_direct=True)
def retriever_azure_search(query: str, k: int = 4, score_threshold: float = 0.8):
    """
    Search for information specifically about Expotech Panama 2025. For any questions related to the event, exhibitors, schedules, speakers, venues, or any details about Expotech Panama 2025, you must use this tool.
    """
    try:
        # Instancia de la base de datos vectorial
        index_name = "expotech25_v1"
        vector_store = create_azure_ai_search_vs(index_name)

        # Realizar la búsqueda de similitud con relevancia
        docs_and_scores = vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=k,
            score_threshold=score_threshold,
        )

        # Validar si se encontraron documentos
        if not docs_and_scores:
            return {
                "error": "No se encontraron documentos relevantes para la consulta proporcionada."
            }

        # Formatear la respuesta con documentos y metadatos
        result = []
        for doc, score in docs_and_scores:
            result.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": score,
                }
            )

        return {"query": query, "results": result}

    except Exception as e:
        # Manejo de errores
        return {"error": f"Ocurrió un error al realizar la búsqueda: {str(e)}"}


#   -   -   -   -   -   -   -   -    CHROMA DB RETRIEVER    -   -   -   -   -   -   -   -   -   -


persist_directory = "./chroma_docs/expotech_2025/"

retriever = genereate_chroma_retriever(persist_directory)


retriever_tool = create_retriever_tool(
    retriever,
    "Expotech_panama_2025",
    "Search for information specifically about Expotech Panama 2025. For any questions related to the event, exhibitors, schedules, speakers, venues, or any details about Expotech Panama 2025, you must use this tool.",
)


#
#
#
#
#
#   -   -   -   -   -   -   -   -   CONTACTO PERSONA SQL + MAIL     -   -   -   -   -   -   -   -   -
@tool
def contacto_personal(
    nombre_contacto: str,
    nombre_empresa: str,
    mail_contacto: str,
    numero_contacto: str,
    motivo_contacto: str,
) -> str:
    """
    Use this tool when the user indicates they wish to be contacted by a person, either via email or phone.
    Collect all the necessary contact information as well as provide a brief summary of the conversation,including the reason for the contact, based on the ongoing conversation and historical context.


    Parameters:
    - nombre_contacto (str): The name of the user requesting contact.
    - nombre_empresa (str): The name of the user company or businnes of the user.
    - mail_contacto (str): The email address provided by the user for contact.
    - numero_contacto (str): The phone number provided by the user for contact.
    - motivo_contacto (str): A brief summary of the reason for contact or the main topic discussed during the conversation, generated by the agent based on the conversation and historical context.
    """

    # Control de faltantes
    if nombre_empresa is None or nombre_empresa.strip() == "":
        nombre_empresa = "sin determinar"
    if numero_contacto is None or numero_contacto.strip() == "":
        numero_contacto = "sin determinar"
    if mail_contacto is None or mail_contacto.strip() == "":
        mail_contacto = "sin determinar"

    # Conectar a la base de datos
    conn = connect_db()
    if conn is None:
        return "Error connecting to the database."

    try:
        # Crear cursor
        cursor = conn.cursor()

        # Insertar el nuevo usuario en la tabla
        cursor.execute(
            """
            INSERT INTO expo25_contacto_persona (nombre_contacto, nombre_empresa, mail_contacto, numero_contacto, motivo_contacto)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                nombre_contacto,
                nombre_empresa,
                mail_contacto,
                numero_contacto,
                motivo_contacto,
            ),
        )

        # Confirmar transacción
        conn.commit()
        enviar_mail_confirmacion(mail_contacto)
        return (
            f"The user {nombre_contacto} has been successfully scheduled to be contacted "
            f"at the email {mail_contacto} or the phone number {numero_contacto} "
            f"for the following reason: {motivo_contacto}"
        )

    except pyodbc.Error as e:
        # Revertir transacción en caso de error
        conn.rollback()
        return f"An error occurred while registering the user: {e}"

    except Exception as e:
        # Manejar otros errores inesperados
        return f"An unexpected error occurred: {e}"

    finally:
        # Cerrar conexión
        conn.close()


# tools = [retriever_tool, contacto_personal]
tools = [retriever_azure_search, contacto_personal]


#
#
#
#
#
#
#
#
#
######################                      AGENTE PRINCIPAL                    ##################################

#   -   -   -   -   -   -   -   -   -   - SYSTEM PROMPT -   -   -   -   -   -   -   -   -   -   -
sys_msg = """
                You are ExpoVisn, a chatbot created by Dsinergia Corp., also known as Dsinergia, to assist with ExpoTech 2025 in Panama City, Panamá.
                Your primary purpose is to provide information about the expo, including details on past participants, services offered, costs, and registration.
                You should communicate in a friendly, professional, and tech-savvy manner, ensuring accessibility and engagement for all users. Always prioritize clarity, accuracy, and user satisfaction.
                Additionally, you are equipped with tools to escalate user queries when needed, ensuring seamless user support.

                ### General Rules:
                1. **Scope of Assistance**:
                - Respond only to questions related to Expotech Panama. If the user asks something outside this scope, politely redirect the conversation. Example:
                    - **User**: "What are the best restaurants in Panama?"
                    - **Agent**: "I only can assist you with information related to Expotech Panama 2025. How can I help you with that?"

                2. **Tools Available**:
                - If the user requests to be contacted by a person or if you cannot answer a question, use the `contacto_personal` tool to gather the necessary contact information.                
                - With retriever_tool or retriever_azure_search toosl, search for information specifically about Expotech Panama 2025. For any questions related to the event, exhibitors, schedules, speakers, venues, and more details about Expotech Panama 2025.

                4. **Language Consistency**:
                - Always respond in the same language the user is using.

                ### Tools Information:
                #### **Tool: contacto_personal**
                - Use this tool when the user requests to be contacted by a person. Gather the following:
                - User's name.
                - User's company or business name (if applicable).
                - User's email.
                - User's phone number.
                - Contact reason: A brief summary of the user's query, generated based on the ongoing conversation.

               

                ### Chain of Thought (CoT) for Tool Usage:
                1. Evaluate the user's request
                2. usea available tools to gather information
                2. Generate a clear, professional summary of the contact reason based on the conversation.
                3. Use `contacto_personal` when the user indicates they wish to be contacted by a person.
                """

#   -   -   -   -   -   -   -   -   -   - LLM + TOOLS   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -
lm_general = "gpt-4o-mini"
llm_with_tools = ChatOpenAI(temperature=0, model_name=lm_general).bind_tools(tools)


# Nodo Original
def assistant(state: expo_state):

    # session_id = state["session_id"]
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    fecha_actual_texto = datetime.now().strftime("%A, %B %d, %Y")

    current_date = f"- The current date is: {fecha_actual} ({fecha_actual_texto})."

    return {
        "messages": [llm_with_tools.invoke([sys_msg, current_date] + state["messages"])]
    }


#
#
#
#
#
#
#
#
######################                      AGENTE EXTRACTOR   (prompt + llm + stroutpuparser)                ##################################

#   -   -   -   -   -   -   -   -   -   - LLM   -   -   -   -   -   -   -   -   -   -   -   -

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

#   -   -   -   -   -   -   -   -   -   - SYSTEM PROMPT -   -   -   -   -   -   -   -   -   -   -

system = """
You are an information extraction expert. Your task is to extract company names from the given message.

Please return the company names in a list format, where each company name is a separate element in the list.
For example: ["Company A", "Company B"]
"""

extraction_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "Here is the response from which to extract the information:\n\n{question}\n",
        ),
    ]
)

#   -   -   -   -   -   -   -   -   -   - LLM + TOOLS   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -

extraction_agent = extraction_prompt | llm | StrOutputParser()


# Nodo Original
def extractor(state: expo_state):
    question = state["messages"][-1]

    empresas = extraction_agent.invoke({"question": question})
    for empresa in literal_eval(empresas):
        print(empresa)

    return {
        "empresas": empresas,
    }


#
#
#
#
#
#
#
#
#
#
##########################                 G R A F O                           ##############################

# - -   -   -   -   -   -   -   -   -   CHECKPOINTER    -   -   -   -   -   -   -   -   -
memory = MemorySaver()


def create_graph():
    # State
    builder = StateGraph(expo_state)

    # Nodos
    # Define nodes: these do the work
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    builder.add_node("extractor", extractor)

    # Conexiones
    builder.add_edge(START, "assistant")

    builder.add_conditional_edges(
        "assistant", tools_condition, {"tools": "tools", "__end__": "extractor"}
    )

    # Tools a agentes
    builder.add_edge("tools", "assistant")
    builder.add_edge("extractor", END)

    react_graph = builder.compile(checkpointer=memory)

    return react_graph
