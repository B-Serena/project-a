# db uploading with text-embedding-ada-002 as a sentence embedding model

import os
import json
import re
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

# Load environment variables
load_dotenv()

def load_crawled_data(file_path='crawled_data.json'):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def preprocess_text(text):
    text = re.sub(r'[^\w\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def clean_key(key):
    return re.sub(r'[^a-z0-9-]', '', key.lower().replace(' ', '-'))

def get_openai_embedding(text):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.embeddings.create(input=[text], model="text-embedding-ada-002")
    return response.data[0].embedding

def upload_to_pinecone(data):
    # Get Pinecone settings from environment variables
    api_key = os.getenv('PINECONE_API_KEY')
    cloud = os.getenv('PINECONE_CLOUD', 'aws')
    region = os.getenv('PINECONE_REGION')
    
    if not api_key or not region:
        raise ValueError("Pinecone API key or region not set. Check your environment variables.")

    # Initialize Pinecone
    pc = Pinecone(api_key=api_key)
    
    # Set index name
    index_name = "kurlyproducts-openai"
    
    # Create index if it doesn't exist
    try:
        if index_name not in pc.list_indexes().names():
            pc.create_index(
                name=index_name,
                dimension=1536,  # OpenAI's text-embedding-ada-002 dimension
                metric='cosine',
                spec=ServerlessSpec(cloud=cloud, region=region)
            )
        print(f"Index '{index_name}' created or connected successfully")
        
        # Connect to the index
        index = pc.Index(index_name)
        print("Index connected")
        
        print("Starting data upload")
        
        # Upload data to Pinecone
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            ids = [clean_key(str(item["id"])) for item in batch]
            texts = [preprocess_text(item.get('all_text', '')) for item in batch]
            embeddings = [get_openai_embedding(text) for text in texts]
            metadata = [{
                clean_key(k): v for k, v in {
                    "category": item.get("category", ""),
                    "url": item.get("url", "")
                }.items() if v
            } for item in batch]
            
            to_upsert = list(zip(ids, embeddings, metadata))
            index.upsert(vectors=to_upsert)
            print(f"Uploaded {i+len(batch)} product information to Pinecone.")
        
        print(f"Successfully uploaded a total of {len(data)} product information to Pinecone.")
    
    except Exception as e:
        print(f"Error during Pinecone operation: {e}")
        if hasattr(e, 'response'):
            print(f"Response status code: {e.response.status_code}")
            print(f"Response content: {e.response.text}")

if __name__ == "__main__":
    try:
        # Load crawled data
        crawled_data = load_crawled_data()
        
        # Upload data to Pinecone
        upload_to_pinecone(crawled_data)
    
    except Exception as e:
        print(f"Error during the entire process: {e}")