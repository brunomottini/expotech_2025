import openai
import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Variables
_ = load_dotenv(find_dotenv())
load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]


# persist_directory = "./chroma_docs/expotech_2025/"


# Generar retriever
def genereate_chroma_retriever(persist_directory):
    # Levanto BD
    # compressor_chat = LLMChainExtractor.from_llm(llm_chat)
    embedding = OpenAIEmbeddings(openai_api_key=openai.api_key)
    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)

    # Genero Retriver
    retriever = vectordb.as_retriever(
        # search_type="similarity",
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 6},
    )

    return retriever
