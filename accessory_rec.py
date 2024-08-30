import base64
import requests
import json
from dotenv import load_dotenv
import os
from pinecone import Pinecone
import cohere
import sqlite3
from langchain_openai import ChatOpenAI
import time


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")
pinecone_api_key = os.getenv("pinecone_api_key")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index("slay-vector-db")

print('200: pinecone badhiya')

connection = sqlite3.connect('fashion_data.db', check_same_thread=False)
cursor = connection.cursor()

print('200: db badhiya')

co = cohere.Client(api_key=COHERE_API_KEY)

print('200: embedding badhiya')

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_accessories(image_path):
    # Define the prompt for the API
    prompt = '''You are a expert in fashion with stylising outfits with accessories like jewellery, belts, wallets, footwear and bags. I want you to suggest what will look good with the provided image.'''

    # Get the base64 string of the image
    base64_image = encode_image(image_path)

    # Prepare the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }

    # Send the request to the API
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        response_json = response.json()
        content = response_json['choices'][0]['message']['content']
        print('200: sab badhiya')
    else:
        print(f"Request failed with status code {response.status_code}")
        return None

    response = co.embed(
            model='embed-multilingual-v3.0',
            texts=[content],
            input_type='classification',
            embedding_types=['float']
        )
    
    print('200: embedding badhiya')

    embedding = response.embeddings.float

    result = index.query(
        vector=embedding,
        top_k=3,
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
        while True:
            try:
                cursor.execute(f'SELECT product_name, image, brand, discounted_price FROM fashion_sql WHERE uniq_id = "{id}"')
                product_data = cursor.fetchone()
                if product_data:
                    product = {
                        "product_name": product_data[0],
                        "image": product_data[1],
                        "brand": product_data[2],
                        "discounted_price": product_data[3]
                    }
                    products.append(product)
                break  # Exit the loop if successful
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    time.sleep(delay)  # Wait before retrying
                    delay *= 2  # Exponential backoff
                else:
                    raise  # Re-raise the exception if it's not a 429 error
    return json.dumps(products)


result = get_accessories(r'C:\Users\Dell\Desktop\Slay-AI\blue pants.jpg')

print(result)