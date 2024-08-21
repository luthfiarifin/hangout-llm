import os
from dotenv import load_dotenv 
import json
from llama_cloud import ChatMessage
from sqlalchemy import URL
from llama_index.core.chat_engine.types import ChatMode
from llama_index.core import Document, StorageContext, VectorStoreIndex, Settings
from llama_index.vector_stores.tidbvector import TiDBVectorStore
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.groq import Groq
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
)

from enums.country import Country
from models.chat_message import ChatMessages

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
       You are a travel itinerary planner. Create a memorable and engaging sightseeing itinerary for visitors to {address} on {day}. The itinerary should cover the time range from {startTime} to {endTime}. Ensure that the itinerary is well-paced, with time allocated for each activity, including travel time between locations. The itinerary should cater to a leisurely and enjoyable experience, including suggestions for dining, leisure, and unique sightseeing spots. Please ensure that the venues are open during the specified time range and that the itinerary is feasible. Do not include any locations, activities, or suggestions that are not present in the provided data. The itinerary must include at least three distinct destinations.
    """)
    metadata_ids = [value["id"] for key, value in response.metadata.items()]
    source_node_ids = [node.node.metadata["id"] for node in response.source_nodes]
    
    print(metadata_ids)
    print(source_node_ids)
    
    return {
        "response": response.response,
        "metadata": get_data_from_cids(list(set(metadata_ids + source_node_ids))),
    }

def chat_query(
    messages: ChatMessages,
    query: str,
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
    
    histories = [ChatMessage(
        content=message.content, 
        role=message.role,
        additional_kwargs={}
    ) for message in messages.histories]
    
    histories.insert(0, ChatMessage(
        content="You are a travel itinerary planner. Create a memorable and engaging sightseeing itinerary for visitors to {address} on {day}. The itinerary should cover the time range from {startTime} to {endTime}. Ensure that the itinerary is well-paced, with time allocated for each activity, including travel time between locations. The itinerary should cater to a leisurely and enjoyable experience, including suggestions for dining, leisure, and unique sightseeing spots. Please ensure that the venues are open during the specified time range and that the itinerary is feasible. Do not include any locations, activities, or suggestions that are not present in the provided data. The itinerary must include at least three distinct destinations.",
        role="system",
        additional_kwargs={}
    ))
    
    histories.append(ChatMessage(
        content=query,
        role="user",
        additional_kwargs={}
    ))
    
    query_engine = index.as_chat_engine(
        filters=filters,
        chat_mode=ChatMode.CONTEXT, 
        llm=Settings.llm, 
        verbose=True,
    )
    response = query_engine.chat(query, chat_history=histories)
    source_node_ids = [node.node.metadata["id"] for node in response.source_nodes]

    print(source_node_ids)
   
    return {
        "response": response.response,
        "metadata": get_data_from_cids(source_node_ids),
    }