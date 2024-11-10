from typing import Dict, List
import chromadb
import os
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter

class VectorStore:
    def __init__(self):
        self.client = chromadb.Client()
        
        try:
            self.collection = self.client.get_collection("web_content")
        except ValueError:
            # If ValueError is raised, it means the collection does not exist
            # Ensure that the embedding function matches the expected dimensions
            self.collection = self.client.create_collection(
                name="web_content",
                embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model_name="text-embedding-ada-002"  # Example model producing 1536-dim embeddings
                )
            )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )


    async def add_document(self, content: Dict):
        """Add a document to the vector store"""
        # Split text into chunks
        # if url is already in the collection, skip
        existing_entries = self.collection.get(
            where={"url": content['url']},
            include=["documents"]  # Only include IDs to minimize data retrieval
        )
        
        if len(existing_entries['documents']) > 0:
            return
        
        chunks = self.text_splitter.split_text(content['text'])
        
        # Generate unique IDs for each chunk
        ids = [f"{content['url']}_{i}" for i in range(len(chunks))]
        
        # Create metadata for each chunk
        metadatas = [{
            'url': content['url'],
            'title': content['title'],
            'chunk_index': i
        } for i in range(len(chunks))]
        
        # Add to collection
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

    async def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar documents using query embeddings"""
        # Generate the query embedding
        embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-ada-002"
        )
        query_embedding = embedding_function([query]) 
        
        # Perform the search using the query embedding
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        return [{
            'text': doc,
            'metadata': meta
        } for doc, meta in zip(results['documents'][0], results['metadatas'][0])]