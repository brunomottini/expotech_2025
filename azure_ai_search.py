import os
from dotenv import load_dotenv


from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import OpenAIEmbeddings

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


load_dotenv()


# Settings
vector_store_address = os.environ.get("YOUR_AZURE_SEARCH_ENDPOINT")
vector_store_password = os.environ.get("YOUR_AZURE_SEARCH_ADMIN_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")

# Option 1: Use OpenAIEmbeddings with OpenAI account for  embeddings
model: str = "text-embedding-ada-002"

embeddings: OpenAIEmbeddings = OpenAIEmbeddings(
    openai_api_key=openai_api_key, model=model
)


# vector store instances
index_name: str = "expotech25_v1"


def create_azure_ai_search_vs(index_name):

    vector_store: AzureSearch = AzureSearch(
        azure_search_endpoint=vector_store_address,
        azure_search_key=vector_store_password,
        index_name=index_name,
        embedding_function=embeddings.embed_query,
    )

    return vector_store
