# text_processor.py
from bs4 import BeautifulSoup
import re

class TextProcessor:
    def __init__(self):
        pass

    def extract_text_from_html(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    
    def clean_text(self, text: str) -> str:
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def process(self, text: str) -> str:
        extracted_text = self.extract_text_from_html(text)
        cleaned_text = self.clean_text(extracted_text)
        return cleaned_text
    


