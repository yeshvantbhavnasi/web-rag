import asyncio
import yaml
from dotenv import load_dotenv

from src.crawler.crawler import WebCrawler
from src.rag.pipeline import RAGPipeline

from fastapi import FastAPI

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Load environment variables
    print("Loading environment variables")
    load_dotenv()
    print("Environment variables loaded")
    
    # Load configuration
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize crawler
    crawler = WebCrawler(config['crawler'])
    
    # Start crawling
    start_url = "https://www.irs.gov/filing"  # Replace with your start URL
    print(f"Starting crawler with URL: {start_url}")
    await crawler.crawl(start_url)
    print("Crawling completed")

    # Initialize RAG pipeline
    global rag
    rag = RAGPipeline(config)

@app.get("/ask")
async def query_api(query: str):
    result = await rag.process_query(query)
    return {
        "answer": result['answer'],
        "sources": [{"title": source['title'], "url": source['url']} for source in result['sources']]
    }

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}