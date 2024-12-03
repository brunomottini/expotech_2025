from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from collections import OrderedDict
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

# from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


from chromadb_store import genereate_chroma_retriever

from langchain.memory import ConversationBufferWindowMemory
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain.tools.retriever import create_retriever_tool


import pandas as pd
from datetime import datetime
import openai
import os
from dotenv import load_dotenv, find_dotenv


from chromadb_store import genereate_chroma_retriever

# from langchain_community.document_loaders import WebBaseLoader
import requests
import re

# from bs4 import BeautifulSoup


from typing import Optional

# from langchain_google_community import GmailToolkit


# Varibles de ambiente
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ["OPENAI_API_KEY"]


######################### MEMORIA ####################
class CircularDict(OrderedDict):
    def __init__(self, max_size):
        super().__init__()
        self.max_size = max_size

    def __setitem__(self, key, value):
        if len(self) >= self.max_size:
            self.popitem(
                last=False
            )  # Elimina el elemento más antiguo (el primero en ser insertado)
        super().__setitem__(key, value)


# -----------------------------------------------------        TOOL         ---------------------------
# source = "./documentos/RAG_information.pdf"
persist_directory = "./chroma_docs/expotech_2025/"

retriever = genereate_chroma_retriever(persist_directory)


retriever_tool = create_retriever_tool(
    retriever,
    "Expotech_panama_2025",
    "Search for information specifically about Expotech Panama 2025. For any questions related to the event, exhibitors, schedules, speakers, venues, or any details about Expotech Panama 2025, you must use this tool.",
)

tools = [retriever_tool]

functions = [format_tool_to_openai_function(f) for f in tools]


# Prompt
# from langchain_core.messages import HumanMessage

prompt_expotech = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate(
            prompt=PromptTemplate(
                input_variables=["fecha_actual", "fecha_actual_texto"],
                template="""
                You are a highly capable AI assistant designed to assist with all inquiries related to the Expotech Panama 2025 event. Your primary objective is to provide accurate, relevant, and timely responses to both participating companies and attendees. 

                ### Context:
                - The current date is: {fecha_actual} ({fecha_actual_texto}).
                - The expo includes a wide range of activities such as exhibitor presentations, business meetings, networking sessions, and registration processes.                

                ### Handling Out-of-Scope Requests:
                - If the user asks about something unrelated to Expotech Panama 2025, respond politely and inform them that your purpose is to assist exclusively with the expo. For example:
                - "I'm here to assist with any questions related to Expotech Panama 2025. How can I help you with that?"

                ### Examples:
                1. **User**: "Can I schedule a meeting with Company X on the first day of the expo?"
                - **Agent**: "The current date is {fecha_actual}. Let me check the availability of Company X for that date. Could you confirm your preferred time?"
                2. **User**: "Quiero registrarme para el evento."
                - **Agent**: "¡Claro! Permíteme guiarte en el proceso de inscripción para Expotech Panama 2025."
                3. **User**: "What's the agenda for the main speakers?"
                - **Agent**: "The main speakers will present on various topics including AI, fintech, and innovation. Would you like the full schedule?"

                Always keep the conversation focused on helping the user with tasks related to Expotech Panama 2025, leveraging your knowledge base effectively.
                Always respond in the same languaje as the user. 
                """,
            )
        ),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        HumanMessagePromptTemplate(
            prompt=PromptTemplate(input_variables=["input"], template="{input}")
        ),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


# MEMORIA
memorias_usuarios = CircularDict(max_size=4)


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in memorias_usuarios:
        memorias_usuarios[session_id] = ChatMessageHistory()
    return memorias_usuarios[session_id]


# RUNNABLE
def create_agent():

    # MODELO
    lm_general = "gpt-4o-mini"
    # lm_general = "gpt-4o"
    model = ChatOpenAI(temperature=0, model_name=lm_general).bind(functions=functions)

    # AGENTE
    agent = create_tool_calling_agent(model, tools, prompt_expotech)

    # EXECUTOR
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    return agent_with_chat_history
