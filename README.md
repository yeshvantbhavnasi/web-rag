# Web Crawler and RAG Pipeline

## Web Crawler

1. Given a seed URL, the crawler will crawl the web and extract the text content of the page.
2. The crawler will then store the text content in a vector database.
3. Also crawler will extract the links from the page and store them in a queue. 
4. The crawler will then dequeue a URL from the queue and repeat the process.
5. The crawler will also store the metadata of the page such as the title, the text content, and the links.
6. The crawler will also store the URL of the page.


## RAG Pipeline

1. Given a query, the RAG pipeline will use the vector database to find the most similar pages to the query.
2. The RAG pipeline will then use the LLM to generate a response to the query.
3. The RAG pipeline will then return the response to the user. With the source pages that the LLM used to generate the response. 



