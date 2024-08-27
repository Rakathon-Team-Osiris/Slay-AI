import os
import regex as re
import json
from dotenv import load_dotenv
from pinecone import Pinecone
import cohere
from langchain_openai import ChatOpenAI
from langchain_community.tools import TavilySearchResults
import sqlite3
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")
pinecone_api_key = os.getenv("pinecone_api_key")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index("slay-vector-db")

co = cohere.Client(api_key=COHERE_API_KEY)

model = ChatOpenAI(model="gpt-4o")

tool = TavilySearchResults(
    max_results=1,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=True,
)

prompt = "you are a fashion designer and an advisor. while using 'get_products()' function to retrieve products and show them, make sure you provide output in json format."
connection = sqlite3.connect('fashion_data.db', check_same_thread=False)
cursor = connection.cursor()

def extract_json_from_aimessage(ai_message):
    # The ai_message is already a string, so we work with it directly.
    
    # Find the start and end of the JSON block
    start_index = ai_message.find('```json')
    end_index = ai_message.find('```', start_index + 7)

    # Extract the JSON string
    if start_index != -1 and end_index != -1:
        json_str = ai_message[start_index + 7:end_index].strip()

        # Optionally, parse the JSON string to a Python object
        try:
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError:
            return None  # Return None if the JSON is invalid
    else:
        return None  # Return None if JSON block is not found

    
def remove_markdown(text):
    # Remove headers (e.g., ### Header)
    text = re.sub(r'#\s*', '', text)
    
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Remove inline links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove unordered list markers (e.g., - or *)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    
    # Remove excess newlines
    text = re.sub(r'\n+', '\n', text).strip()

    # Remove list numbers (e.g., 1. 2. 3.)
    text = re.sub(r'\d+\.\s+', '', text)
    
    # Remove excess newlines
    text = re.sub(r'\n+', ' ', text).strip()
    
    return text


def get_trends(query):
    """Use this to get fashion relatated information from the web"""
    answer = tool.invoke({'query': query})
    return answer

def get_products(query: str):
    """Use this to retrieve relevant products when asked"""
    
    response = co.embed(
            model='embed-multilingual-v3.0',
            texts=[query],
            input_type='classification',
            embedding_types=['float']
        )

    embedding = response.embeddings.float

    result = index.query(
    vector=embedding,
    top_k=5,
    include_values=True,
    include_metadata=True
)

    ids = []
    for i in range(len(result['matches'])):
        match = result['matches'][i]
        id = match['id']
        ids.append(id)
    
    products = []
    for id in ids:
        cursor.execute(f'SELECT product_name, image, brand, discounted_price  FROM fashion_sql WHERE uniq_id = "{id}"')
        product = cursor.fetchall()
        products.append(product)

    return products

tools = [get_trends, get_products]

graph = create_react_agent(model, tools=tools, state_modifier = prompt)

def get_answer(query: str):
    def get_stream(stream):
        last_message = None  

        for s in stream:
            message = s["messages"][-1]
            last_message = message 
        
        return last_message

    inputs = {"messages": [("user", query)]}
    ai_message = get_stream(graph.stream(inputs, stream_mode="values")).content


    # Check if the string contains "json"
    if re.search(r'\bjson\b', ai_message):
        # If "json" is found
        ai_message = extract_json_from_aimessage(ai_message=ai_message)
    else:
        # If "json" is not found
        ai_message = remove_markdown(ai_message)

    return ai_message



print(get_answer("Ganesh puja is around the corner, show me some kurtas fit for men"))