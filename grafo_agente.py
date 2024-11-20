# Notebooks Inicial
from langchain_openai import ChatOpenAI
from langchain.tools import tool

from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.prebuilt import create_react_agent

# from IPython.display import Image, display

from langgraph.checkpoint.memory import MemorySaver


from datetime import datetime, timedelta

from typing import Literal, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

import openai
import os
from dotenv import load_dotenv, find_dotenv


# Resto
from langchain.tools.retriever import create_retriever_tool
from chromadb_store import genereate_chroma_retriever


# Varibles de ambiente
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ["OPENAI_API_KEY"]

#######################                    TOOLS                     ##############################
persist_directory = "./chroma_docs/expotech_2025/"

retriever = genereate_chroma_retriever(persist_directory)


retriever_tool = create_retriever_tool(
    retriever,
    "Expotech_panama_2025",
    "Search for information specifically about Expotech Panama 2025. For any questions related to the event, exhibitors, schedules, speakers, venues, or any details about Expotech Panama 2025, you must use this tool.",
)

tools = [retriever_tool]


######################                      LLMs                    ##################################
lm_general = "gpt-4o-mini"
llm_with_tools = ChatOpenAI(temperature=0, model_name=lm_general).bind_tools(tools)


######################                      Memory                  ###################################
memory = MemorySaver()


#####################                       State                   ###################################
class fluxy_state(TypedDict):
    session_id: str
    messages: Annotated[list, add_messages]


####################                        System Prompt           ##################################
sys_msg = """You are a highly capable AI assistant designed to assist with all inquiries related to the Expotech Panama 2025 event. Your primary objective is to provide accurate, relevant, and timely responses to both participating companies and attendees. 

                         

                ### Handling Out-of-Scope Requests:
                - If the user asks about something unrelated to Expotech Panama 2025, respond politely and inform them that your purpose is to assist exclusively with the expo. For example:
                - "I'm here to assist with any questions related to Expotech Panama 2025. How can I help you with that?"

                ### Examples:                
                2. **User**: "Quiero registrarme para el evento."
                - **Agent**: "¡Claro! Permíteme guiarte en el proceso de inscripción para Expotech Panama 2025."
                3. **User**: "What's the agenda for the main speakers?"
                - **Agent**: "The main speakers will present on various topics including AI, fintech, and innovation. Would you like the full schedule?"

                Always keep the conversation focused on helping the user with tasks related to Expotech Panama 2025, leveraging your knowledge base effectively.
                Always respond in the same languaje as the user. 
                """


####################                        Funciones Nodos                   ######################################
# Nodo Original
def assistant(state: fluxy_state):
    # session_id = state["session_id"]
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    fecha_actual_texto = datetime.now().strftime("%A, %B %d, %Y")

    current_date = f"- The current date is: {fecha_actual} ({fecha_actual_texto})."

    return {
        "messages": [llm_with_tools.invoke([sys_msg, current_date] + state["messages"])]
    }


##########################                  Grafo                           ##############################


def create_graph():
    # State
    builder = StateGraph(fluxy_state)

    # Nodos
    # Define nodes: these do the work
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))

    # Conexiones
    builder.add_edge(START, "assistant")

    builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )

    # Tools a agentes
    builder.add_edge("tools", "assistant")

    react_graph = builder.compile(checkpointer=memory)

    return react_graph
