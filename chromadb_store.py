import openai
import os
from dotenv import load_dotenv, find_dotenv


from langchain_community.document_loaders import PyPDFLoader

from langchain.text_splitter import RecursiveCharacterTextSplitter, NLTKTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma


# Variables
_ = load_dotenv(find_dotenv())  # read local .env file
load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]


# Variables de las funciones
# Chroma
sources = [
    "./retriever_documents/informacion_general_11_24.pdf",
]
persist_directory = "./chroma_docs/expotech_2025/"

# LLMS
llm_name = "gpt-4o-mini"
llm_chat = ChatOpenAI(model_name=llm_name, temperature=0)


def load_pdf(sources):
    docs = []

    for source in sources:
        loaders = [PyPDFLoader(source)]
        for loader in loaders:
            docs.extend(loader.load())

    return docs


#### MJOERAR COMO SE CORTAN LOS DOCUMENTOS  - - - - UNSTRUCTED - - - - - -


def RecursiveCharacterTextSplitter_text_splitter(docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )

    splits = text_splitter.split_documents(docs)

    return splits


def NLTKTextSplitter_text_splitter(docs):
    text_splitter = NLTKTextSplitter(chunk_size=1000)

    splits = text_splitter.split_documents(docs)

    return splits


def generate_vectordb_from_pdf_store(text_splitter, source, persist_directory):

    docs = load_pdf(source)
    splits = text_splitter(docs)

    embedding = OpenAIEmbeddings(openai_api_key=openai.api_key)
    vectordb = Chroma.from_documents(
        documents=splits, embedding=embedding, persist_directory=persist_directory
    )

    return vectordb


######## OPTIMIZAR LA CANTIDAD QUE SE EXTRAEN Y SE PASAN POR EL FLUJO - - - - -


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
        search_kwargs={"k": 3, "fetch_k": 6},
    )
    # Genero Compression Retriever NUEVO
    # compression_retiever = ContextualCompressionRetriever(
    #    base_compressor=compressor_chat, base_retriever=retriever
    # )

    return retriever


# # Genero los documentos
# docs = load_pdf(sources)
# splits = RecursiveCharacterTextSplitter_text_splitter(docs)
# print(splits)
# generate_vectordb_from_pdf_store(
#     RecursiveCharacterTextSplitter_text_splitter, sources, persist_directory
# )
