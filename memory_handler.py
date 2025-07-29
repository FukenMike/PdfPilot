import os
import json
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
import pickle
from pathlib import Path

class MemoryHandler:
    """Handles memory persistence and vector storage for PDF content"""
    
    def __init__(self):
        self.cache_dir = Path("pdf_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )
        
        # Initialize embeddings (will be created when needed)
        self.embeddings = None
        self.vector_store = None
        
    def _get_embeddings(self):
        """Get OpenAI embeddings instance"""
        if self.embeddings is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        return self.embeddings
    
    def _get_cache_paths(self, pdf_hash):
        """Get cache file paths for a given PDF hash"""
        return {
            'metadata': self.cache_dir / f"{pdf_hash}_metadata.json",
            'text': self.cache_dir / f"{pdf_hash}_text.txt",
            'images': self.cache_dir / f"{pdf_hash}_images.pkl",
            'vector_store': self.cache_dir / f"{pdf_hash}_vectorstore"
        }
    
    def is_cached(self, pdf_hash):
        """Check if PDF data is already cached"""
        paths = self._get_cache_paths(pdf_hash)
        return all(path.exists() for path in [paths['metadata'], paths['text']])
    
    def save_pdf_data(self, pdf_hash, pdf_text, pdf_images, metadata=None):
        """Save PDF data to cache"""
        try:
            paths = self._get_cache_paths(pdf_hash)
            
            # Save metadata
            cache_metadata = {
                'pdf_hash': pdf_hash,
                'text_length': len(pdf_text),
                'num_pages': len(pdf_images),
                'metadata': metadata or {},
                'cached_at': str(Path().resolve())
            }
            
            with open(paths['metadata'], 'w') as f:
                json.dump(cache_metadata, f, indent=2)
            
            # Save text content
            with open(paths['text'], 'w', encoding='utf-8') as f:
                f.write(pdf_text)
            
            # Save images as pickle
            with open(paths['images'], 'wb') as f:
                pickle.dump(pdf_images, f)
            
            # Create vector store if embeddings are available
            embeddings = self._get_embeddings()
            if embeddings:
                self._create_vector_store(pdf_text, pdf_hash)
            
            return True
            
        except Exception as e:
            print(f"Error saving PDF data to cache: {e}")
            return False
    
    def load_pdf_data(self, pdf_hash):
        """Load PDF data from cache"""
        try:
            paths = self._get_cache_paths(pdf_hash)
            
            if not self.is_cached(pdf_hash):
                return None
            
            # Load metadata
            with open(paths['metadata'], 'r') as f:
                metadata = json.load(f)
            
            # Load text
            with open(paths['text'], 'r', encoding='utf-8') as f:
                pdf_text = f.read()
            
            # Load images
            with open(paths['images'], 'rb') as f:
                pdf_images = pickle.load(f)
            
            # Load vector store if it exists
            vector_store = None
            if paths['vector_store'].exists():
                embeddings = self._get_embeddings()
                if embeddings:
                    vector_store = FAISS.load_local(
                        str(paths['vector_store']), 
                        embeddings,
                        allow_dangerous_deserialization=True
                    )
            
            return {
                'pdf_text': pdf_text,
                'pdf_images': pdf_images,
                'metadata': metadata,
                'vector_store': vector_store
            }
            
        except Exception as e:
            print(f"Error loading PDF data from cache: {e}")
            return None
    
    def _create_vector_store(self, pdf_text, pdf_hash):
        """Create and save vector store for the PDF content"""
        try:
            embeddings = self._get_embeddings()
            if not embeddings:
                return None
            
            # Split text into chunks
            texts = self.text_splitter.split_text(pdf_text)
            
            # Create documents
            documents = [Document(page_content=text, metadata={"source": f"pdf_{pdf_hash}"}) 
                        for text in texts]
            
            # Create vector store
            vector_store = FAISS.from_documents(documents, embeddings)
            
            # Save vector store
            paths = self._get_cache_paths(pdf_hash)
            vector_store.save_local(str(paths['vector_store']))
            
            return vector_store
            
        except Exception as e:
            print(f"Error creating vector store: {e}")
            return None
    
    def search_similar_content(self, pdf_hash, query, k=5):
        """Search for similar content in the cached vector store"""
        try:
            paths = self._get_cache_paths(pdf_hash)
            
            if not paths['vector_store'].exists():
                return []
            
            embeddings = self._get_embeddings()
            if not embeddings:
                return []
            
            # Load vector store
            vector_store = FAISS.load_local(
                str(paths['vector_store']), 
                embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Search for similar documents
            docs = vector_store.similarity_search(query, k=k)
            
            return [doc.page_content for doc in docs]
            
        except Exception as e:
            print(f"Error searching similar content: {e}")
            return []
    
    def get_cached_files(self):
        """Get list of all cached PDF files"""
        try:
            cached_files = []
            
            for metadata_file in self.cache_dir.glob("*_metadata.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    cached_files.append({
                        'hash': metadata['pdf_hash'],
                        'pages': metadata['num_pages'],
                        'text_length': metadata['text_length'],
                        'cached_at': metadata.get('cached_at', 'Unknown')
                    })
                except:
                    continue
            
            return cached_files
            
        except Exception as e:
            print(f"Error getting cached files: {e}")
            return []
    
    def clear_cache(self, pdf_hash=None):
        """Clear cache for specific PDF or all cache"""
        try:
            if pdf_hash:
                # Clear specific PDF cache
                paths = self._get_cache_paths(pdf_hash)
                for path in paths.values():
                    if path.exists():
                        if path.is_dir():
                            import shutil
                            shutil.rmtree(path)
                        else:
                            path.unlink()
            else:
                # Clear all cache
                import shutil
                if self.cache_dir.exists():
                    shutil.rmtree(self.cache_dir)
                    self.cache_dir.mkdir(exist_ok=True)
            
            return True
            
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def get_cache_size(self):
        """Get total cache size in MB"""
        try:
            total_size = 0
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            print(f"Error calculating cache size: {e}")
            return 0