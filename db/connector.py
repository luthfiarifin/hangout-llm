import os
from dotenv import load_dotenv 
import json
from sqlalchemy import URL
from llama_index.core import Document, StorageContext, VectorStoreIndex, Settings
from llama_index.vector_stores.tidbvector import TiDBVectorStore
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.groq import Groq
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
)

from enums.country import Country

load_dotenv() 

tidb_connection_url = URL(
    "mysql+pymysql",
    username=os.environ['TIDB_USERNAME'],
    password=os.environ['TIDB_PASSWORD'],
    host=os.environ['TIDB_HOST'],
    port=4000,
    database="test",
    query={"ssl_verify_cert": False, "ssl_verify_identity": True},
)

tidbvec = TiDBVectorStore(
    connection_string=tidb_connection_url,
    table_name=os.getenv("VECTOR_TABLE_NAME"),
    distance_strategy="cosine",
    vector_dimension=768,
    drop_existing_table=False,
)

storage_context = StorageContext.from_defaults(vector_store=tidbvec)

# Preprocess data
def preprocess_data(path):
    documents = []
    data = json.load(open(path))
    for item in data:
        text = f"""
        Address: {item['address']}
        Title: {item['title']}
        Country: {item['complete_address']['country']}
        Categories: {', '.join(item['categories'] if item['categories'] else [])}
        Description: {item.get('description', 'No description')}
        Review Count: {item['review_count']}
        Review Rating: {item['review_rating']}
        Open Hours: {json.dumps(item['open_hours'])}
        Latitude: {item['latitude']}
        Longitude: {item['longtitude']}
        """
        metadata = {
            "id": item["cid"],
            "title": item["title"],
            "description": item["description"],
            "address": item["address"],
            "complete_address": item["complete_address"],
        }
        document = Document(text=text, metadata=metadata)
        documents.append(document)
    return documents

def init():
    documents = preprocess_data("./data/destinations.json")
    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, insert_batch_size=1000, show_progress=True
    )
    return index

def connect():
    index = VectorStoreIndex.from_vector_store(vector_store=tidbvec)
    return index


Settings.llm = Groq(model="llama3-70b-8192", api_key=os.getenv("GROQ_API_KEY"))
Settings.embed_model = GeminiEmbedding(
    api_key=os.getenv("GEMINI_API_KEY"),
)
    
index = connect()

def get_data_from_cids(cids):
    data = json.load(open("./data/destinations.json"))
    results = []
    for cid in cids:
        for item in data:
            if item["cid"] == cid:
                results.append(item)
    return results

def get_data_from_metadatas(metadatas):
    data = json.load(open("./data/destinations.json"))
    results = []
    for metadata in metadatas:
        for item in data:
            if item["cid"] == metadata["id"]:
                results.append(item)
    return results

def query(
    day: str,
    country: Country,
    startTime: str,
    endTime: str,
    address: str,
):
    filters = MetadataFilters(
        filters=[
                MetadataFilter(
                    key="complete_address.country",
                    value=[country.value],
                )
            ]
    )
    
    query_engine = index.as_query_engine(
        filters=filters,
        similarity_top_k=2,
    )
    response = query_engine.query(f"""
        You are a travel itinerary planner. Create a romantic and memorable dating itinerary for a couple visiting {address} on on {day}. The itinerary should cover the time range from {startTime} to {endTime}.
        Ensure that the itinerary is well-paced, with time allocated for each activity, including travel time between locations. The itinerary should cater to a romantic atmosphere, including suggestions for dining, leisure, and unique experiences. Please ensure that the venues are open during the specified time range and that the itinerary is feasible.
    """)
    metadata_ids = [value["id"] for key, value in response.metadata.items()]
    source_node_ids = [node.node.metadata["id"] for node in response.source_nodes]
    
    print(metadata_ids)
    print(source_node_ids)
    
    return {
        "response": response.response,
        "metadata": get_data_from_cids(list(set(metadata_ids + source_node_ids)))
    }