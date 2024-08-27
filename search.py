import os
import regex as re
import json
from dotenv import load_dotenv
from pinecone import Pinecone
import cohere
from langchain_community.tools import TavilySearchResults
import sqlite3
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

load_dotenv()

LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
pinecone_api_key = os.getenv("pinecone_api_key")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index("slay-vector-db")

co = cohere.Client(api_key=COHERE_API_KEY)
connection = sqlite3.connect('fashion_data.db', check_same_thread=False)
cursor = connection.cursor()


def get_products(query: str):
    
    response = co.embed(
            model='embed-multilingual-v3.0',
            texts=[query],
            input_type='classification',
            embedding_types=['float']
        )

    query_embedding = response.embeddings.float

    init_filter = index.query(
    vector=query_embedding,
    top_k=1000,
    include_values=True,
    include_metadata=True
    )

    match_ids = [item['id'] for item in init_filter['matches']]

    products = []
    for id in match_ids:
        cursor.execute(f'SELECT product_name, image, brand, discounted_price  FROM fashion_sql WHERE uniq_id = "{id}"')
        product = cursor.fetchall()
        products.append(product)

    return products

