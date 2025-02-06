import os
import json
import time
import pickle
import requests
import numpy as np
from typing import List, Tuple, Dict
from docx import Document
from dotenv import load_dotenv
from datetime import datetime

def log_message(message: str):
    """Write message to both console and file"""
    print(message)
    with open('docx_search.log', 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f'[{timestamp}] {message}\n')
        f.flush()

# Clear log file at start
with open('docx_search.log', 'w', encoding='utf-8') as f:
    f.write('')

class DocumentSearch:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.cache_file = 'embeddings_cache.pkl'
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def load_cache(self) -> Dict[str, List[float]]:
        """Load embeddings cache if it exists"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}

    def save_cache(self, cache: Dict[str, List[float]]):
        """Save embeddings cache"""
        with open(self.cache_file, 'wb') as f:
            pickle.dump(cache, f)

    def get_single_embedding(self, text: str, cache: Dict[str, List[float]], retries: int = 3) -> List[float]:
        """Get embedding for a single text with caching and retries"""
        # Check cache first
        if text in cache:
            return cache[text]

        for attempt in range(retries):
            try:
                response = requests.post(
                    'https://api.openai.com/v1/embeddings',
                    headers=self.headers,
                    json={
                        'model': 'text-embedding-ada-002',
                        'input': text
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    embedding = response.json()['data'][0]['embedding']
                    cache[text] = embedding  # Add to cache
                    self.save_cache(cache)  # Save cache
                    return embedding
                elif response.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * 5  # Exponential backoff
                    log_message(f"Rate limit hit, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    log_message(f"Error: Status {response.status_code}")
                    time.sleep(2)

            except Exception as e:
                log_message(f"Error in attempt {attempt + 1}: {str(e)}")
                time.sleep(2)

        return []

    def find_relevant_content(self, query: str, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """Find paragraphs relevant to the query"""
        try:
            log_message(f"\nSearching for: {query}")
            
            # Load cache
            log_message("Loading embeddings cache...")
            cache = self.load_cache()
            
            # Read document
            log_message("Reading document...")
            doc = Document(self.file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            total_paragraphs = len(paragraphs)
            log_message(f"Found {total_paragraphs} paragraphs in document")

            # Get query embedding
            log_message("\nGetting embedding for search query...")
            query_embedding = self.get_single_embedding(query, cache)
            if not query_embedding:
                log_message("Failed to get query embedding")
                return []

            # Process paragraphs
            log_message("\nProcessing paragraphs...")
            relevant_paragraphs = []
            
            for i, para in enumerate(paragraphs, 1):
                log_message(f"\nProcessing paragraph {i}/{total_paragraphs} ({(i/total_paragraphs)*100:.1f}%)")
                
                # Get embedding for paragraph
                para_embedding = self.get_single_embedding(para, cache)
                if not para_embedding:
                    log_message("Failed to get paragraph embedding, skipping...")
                    continue
                
                # Calculate similarity
                similarity = np.dot(para_embedding, query_embedding) / (
                    np.linalg.norm(para_embedding) * np.linalg.norm(query_embedding)
                )
                
                # If similarity is above threshold, add to results
                if similarity >= threshold:
                    relevant_paragraphs.append((para, similarity))
                    log_message(f"Found relevant match (similarity: {similarity:.4f}):")
                    log_message("-" * 80)
                    log_message(para)
                    log_message("-" * 80)

                # Small delay between paragraphs if not cached
                if para not in cache:
                    time.sleep(0.5)

            # Sort by similarity
            relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
            
            log_message(f"\nFound {len(relevant_paragraphs)} relevant paragraphs")
            log_message("\nTop matches:")
            for i, (para, sim) in enumerate(relevant_paragraphs[:5], 1):
                log_message(f"\n{i}. Similarity: {sim:.4f}")
                log_message("-" * 80)
                log_message(para)
                log_message("-" * 80)
            
            return relevant_paragraphs

        except Exception as e:
            log_message(f"Error in find_relevant_content: {str(e)}")
            return []

    def generate_response(self, relevant_paragraphs: List[Tuple[str, float]], query: str) -> str:
        """Generate response using OpenAI GPT-4"""
        try:
            if not relevant_paragraphs:
                return "No relevant content found to generate a response."

            log_message("\nGenerating response with GPT-4...")
            
            # Extract just the text content from the relevant paragraphs
            content_list = [para for para, _ in relevant_paragraphs]
            
            system_prompt = """You are a helpful assistant specialized in finding relevant database and system information. 
            When provided with documentation content, focus on identifying:
            1. Relevant table names and their purposes
            2. Database relationships
            3. Key fields and their meanings
            4. Common queries and their use cases
            
            Format your response in a clear, structured way."""

            data = {
                'model': 'gpt-4',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Based on the following documentation, {query}\n\nContent:\n{' '.join(content_list)}"}
                ]
            }

            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=self.headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                log_message(f"Error generating response. Status: {response.status_code}")
                return "Error generating response. Please check the logs for details."

        except Exception as e:
            log_message(f"Error in generate_response: {str(e)}")
            return f"Error generating response: {str(e)}"

def main():
    try:
        log_message("=== Starting Document Search ===")
        
        # Load environment variables
        load_dotenv()
        
        # Get document path
        doc_path = os.getenv('DOCX_FILE_PATH')
        if not doc_path:
            log_message("Error: DOCX_FILE_PATH environment variable not set")
            return
        
        if not os.path.exists(doc_path):
            log_message(f"Error: Document not found at {doc_path}")
            return

        log_message(f"Document path: {doc_path}")
        
        # Initialize search
        doc_search = DocumentSearch(doc_path)
        
        # Search query
        query = "Help me with what table I should check to solve account score related queries"
        log_message(f"\nProcessing query: {query}")
        
        # Find relevant content
        relevant_paragraphs = doc_search.find_relevant_content(query)
        
        if relevant_paragraphs:
            log_message("\nGenerating detailed response...")
            response = doc_search.generate_response(relevant_paragraphs, query)
            log_message("\nFinal Analysis:")
            log_message("=" * 80)
            log_message(response)
            log_message("=" * 80)
        else:
            log_message("\nNo relevant content found in the document.")
            log_message("Suggestions:")
            log_message("1. Check if the document contains the information you're looking for")
            log_message("2. Try a different search query")
            log_message("3. Verify the document path is correct")

    except Exception as e:
        log_message(f"Error in main execution: {str(e)}")
        import traceback
        log_message(f"\nFull traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
