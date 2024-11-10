import asyncio
import yaml
from dotenv import load_dotenv

from src.crawler.crawler import WebCrawler
from src.rag.pipeline import RAGPipeline

async def main():
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
    start_url = "https://www.irs.gov/filing/irs-free-file-do-your-taxes-for-free"  # Replace with your start URL
    print(f"Starting crawler with URL: {start_url}")
    await crawler.crawl(start_url)
    print("Crawling completed")
    
    # Initialize RAG pipeline
    rag = RAGPipeline(config)
    
    # Example query
    query = "What is limit for free tax return preparation?"
    result = await rag.process_query(query)
    
    print("\nAnswer:", result['answer'])
    print("\nSources:")
    for source in result['sources']:
        print(f"- {source['title']} ({source['url']})")

if __name__ == "__main__":
    asyncio.run(main())