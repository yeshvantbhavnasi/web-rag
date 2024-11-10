import asyncio
from typing import Set, List, Dict
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from src.database.vector_store import VectorStore
from src.utils.text_processor import TextProcessor
from src.utils.logger import setup_logger

class WebCrawler:
    def __init__(self, config: Dict):
        self.config = config
        self.visited_urls: Set[str] = set()
        self.url_queue: asyncio.Queue = asyncio.Queue()
        self.vector_store = VectorStore()
        self.text_processor = TextProcessor()
        self.logger = setup_logger(__name__)

    def is_valid_url(self, url: str) -> bool:
        """Validate URL based on configuration rules"""
        parsed = urlparse(url)
        return (
            bool(parsed.netloc) and
            bool(parsed.scheme) and
            parsed.scheme in {'http', 'https'} and
            not any(url.lower().endswith(ext) for ext in self.config['ignored_extensions'])
        )

    async def extract_content(self, html: str, url: str) -> Dict:
        """Extract and process content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else ''
        
        # Remove script and style elements
        for element in soup(['script', 'style']):
            element.decompose()
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Process text
        processed_text = self.text_processor.process(text)
        print(processed_text)
        
        # Extract links
        links = set()
        for anchor in soup.find_all('a', href=True):
            link = urljoin(url, anchor['href'])
            if self.is_valid_url(link):
                links.add(link)
        #print(f"Extracted links: {links}")
        #print(f"Processed text: {processed_text}")
        #print(f"Title: {title}")
        #print(f"URL: {url}")
        return {
            'url': url,
            'title': title,
            'text': processed_text,
            'links': list(links)
        }

    async def crawl_page(self, url: str, depth: int):
        """Crawl a single page"""
        #print(f"Crawling page: {url} at depth: {depth}")
        if depth > self.config['max_depth'] or url in self.visited_urls:
            return

        #print(f"Adding URL to visited set: {url}")
        self.visited_urls.add(url)
        
        try:
            async with aiohttp.ClientSession() as session:
                #print(f"Fetching URL: {url}")
                response = await session.get(url)
                data = await response.text()
                #print('{} : {}...({} bytes)'.format(url, data[:10], len(data)))
                async with session.get(
                    url, 
                    headers={'User-Agent': self.config['user_agent']}
                ) as response:
                    #print(f"Response status: {response.status}")
                    if response.status != 200:
                        self.logger.warning(f"Failed to fetch {url}: {response.status}")
                        return
                    
                    if 'text/html' not in response.headers.get('content-type', ''):
                        return
                    #print(f"Response headers: {response.headers}")
                    html = await response.text()
                    #print(f"HTML: {html}")
                    content = await self.extract_content(html, url)

                    #print(f"Extracted content from {url}")
                    #print(f"Content: {content}")
                    
                    # Store content in vector database
                    await self.vector_store.add_document(content)
                    
                    # Add new URLs to queue
                    for link in content['links']:
                        if link not in self.visited_urls:
                            await self.url_queue.put((link, depth + 1))

        except Exception as e:
            self.logger.error(f"Error crawling {url}: {e}")

        await asyncio.sleep(self.config['delay_between_requests'])

    async def crawl(self, start_url: str):
        """Main crawling function"""
        await self.url_queue.put((start_url, 0))

        workers = []
        for _ in range(5):  # Number of concurrent workers
            worker = asyncio.create_task(self.worker())
            workers.append(worker)

        await self.url_queue.join()
        for worker in workers:
            worker.cancel()

        await asyncio.gather(*workers, return_exceptions=True)

    async def worker(self):
        """Worker function for concurrent crawling"""
        while True:
            url, depth = await self.url_queue.get()
            try:
                await self.crawl_page(url, depth)
            finally:
                self.url_queue.task_done()