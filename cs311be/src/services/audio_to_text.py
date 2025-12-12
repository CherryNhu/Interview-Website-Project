from llama_index import Document 

import re
def preprocess_transcript(transcript_text, metadata): 

    # Clean up the transcript text 
    cleaned_text = clean_transcript(transcript_text) 
    # Split the transcript into chunks if it's too long 
    chunks = split_into_chunks(cleaned_text) 
    # Create a Document object for each chunk 
    documents = [Document(text=chunk, metadata=metadata) for chunk in chunks] 
    return documents 

def clean_transcript(text): 
    # Remove timestamps if they exist 
    text = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', text) 
    # Remove speaker labels if they exist 
    text = re.sub(r'Speaker \d+:', '', text) 
    # Remove extra whitespace 
    text = ' '.join(text.split()) 
    return text 

def split_into_chunks(text, chunk_size=1000): 
    words = text.split() 
    return [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)] 

# Example usage 

transcript = "Speaker 1: [00:00:00] Welcome to our podcast. Today we're discussing..." 
metadata = { 
    "title": "The Future of AI Podcast - Episode 42", 
    "host": "Jane Smith", 
    "guest": "Dr. John Doe", 
    "date": "2024-09-27", 
    "duration": "1:15:30" 

} 

processed_docs = preprocess_transcript(transcript, metadata)