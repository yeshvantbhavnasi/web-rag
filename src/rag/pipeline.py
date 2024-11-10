from typing import Dict, List
import os
from openai import AsyncOpenAI
from src.database.vector_store import VectorStore

class RAGPipeline:
    def __init__(self, config: Dict):
        self.config = config
        self.vector_store = VectorStore()
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _create_prompt(self, query: str, contexts: List[Dict]) -> str:
        """Create a prompt for the LLM using the query and context"""
        context_str = "\n\n".join([
            f"Context from {ctx['metadata']['url']}:\n{ctx['text']}"
            for ctx in contexts
        ])
        
        return f"""Please answer the question based on the provided context. If the context doesn't contain enough information to answer the question, please say so.

Context:
{context_str}

Question: {query}

Answer: """

    async def process_query(self, query: str) -> Dict:
        """Process a query through the RAG pipeline"""
        # Search for relevant documents
        relevant_docs = await self.vector_store.search(query)
        
        # Create the prompt
        prompt = self._create_prompt(query, relevant_docs)
        
        # Get response from LLM
        response = await self.client.chat.completions.create(
            model=self.config['openai']['model'],
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config['openai']['temperature'],
            max_tokens=self.config['openai']['max_tokens']
        )
        
        # Extract the answer
        answer = response.choices[0].message.content
        
        # Return answer and sources
        return {
            'answer': answer,
            'sources': [
                {
                    'url': doc['metadata']['url'],
                    'title': doc['metadata']['title']
                }
                for doc in relevant_docs
            ]
        }