import PyPDF2
import pdfplumber
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import os
import re

class PDFProcessor:
    """Handles PDF text extraction and conversion to images"""
    
    def __init__(self):
        self.dpi = 200  # DPI for PDF to image conversion
        self.text_density_threshold = 100  # Minimum characters per page to consider text-based
        self.word_ratio_threshold = 0.7  # Minimum ratio of actual words to total characters
    
    def extract_text(self, pdf_path):
        """Extract text from PDF using both PyPDF2 and pdfplumber"""
        text_content = ""
        
        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n--- Page {i+1} ---\n{page_text}\n"
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for i, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text_content += f"\n--- Page {i+1} ---\n{page_text}\n"
            except Exception as e:
                print(f"PyPDF2 extraction also failed: {e}")
                text_content = "Error: Could not extract text from PDF"
        
        return text_content
    
    def convert_to_images(self, pdf_path):
        """Convert PDF pages to images for OCR processing"""
        try:
            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                fmt='RGB',
                thread_count=2  # Limit thread count for large files
            )
            
            return images
            
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            return []
    
    def get_pdf_info(self, pdf_path):
        """Get basic information about the PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Try to get metadata
                metadata = pdf_reader.metadata
                info = {
                    'num_pages': num_pages,
                    'title': metadata.get('/Title', 'Unknown') if metadata else 'Unknown',
                    'author': metadata.get('/Author', 'Unknown') if metadata else 'Unknown',
                    'subject': metadata.get('/Subject', 'Unknown') if metadata else 'Unknown'
                }
                
                return info
                
        except Exception as e:
            print(f"Error getting PDF info: {e}")
            return {'num_pages': 0, 'title': 'Unknown', 'author': 'Unknown', 'subject': 'Unknown'}
    
    def extract_text_from_page(self, pdf_path, page_number):
        """Extract text from a specific page"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_number < len(pdf.pages):
                    page = pdf.pages[page_number]
                    return page.extract_text() or ""
                else:
                    return ""
        except Exception as e:
            print(f"Error extracting text from page {page_number}: {e}")
            return ""
    
    def convert_page_to_image(self, pdf_path, page_number):
        """Convert a specific PDF page to image"""
        try:
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=page_number + 1,
                last_page=page_number + 1,
                fmt='RGB'
            )
            
            if images:
                return images[0]
            else:
                return None
                
        except Exception as e:
            print(f"Error converting page {page_number} to image: {e}")
            return None
    
    def detect_pdf_type(self, pdf_path):
        """
        Detect whether PDF is text-based or image-based/scanned
        Returns: 'text', 'image', or 'mixed'
        """
        try:
            text_pages = 0
            image_pages = 0
            total_pages = 0
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                # Sample first 5 pages or all pages if less than 5
                sample_pages = min(5, total_pages)
                
                for i in range(sample_pages):
                    page = pdf.pages[i]
                    page_text = page.extract_text() or ""
                    
                    # Clean and analyze text
                    clean_text = re.sub(r'\s+', ' ', page_text.strip())
                    
                    if self._is_text_based_page(clean_text):
                        text_pages += 1
                    else:
                        image_pages += 1
            
            # Determine PDF type based on analysis
            text_ratio = text_pages / sample_pages if sample_pages > 0 else 0
            
            if text_ratio >= 0.8:
                return {
                    'type': 'text',
                    'confidence': text_ratio,
                    'description': 'Text-based PDF with extractable content',
                    'recommended_method': 'text_extraction'
                }
            elif text_ratio <= 0.2:
                return {
                    'type': 'image',
                    'confidence': 1 - text_ratio,
                    'description': 'Scanned/image-based PDF requiring OCR',
                    'recommended_method': 'ocr_only'
                }
            else:
                return {
                    'type': 'mixed',
                    'confidence': 0.5,
                    'description': 'Mixed content PDF with both text and images',
                    'recommended_method': 'hybrid'
                }
                
        except Exception as e:
            print(f"Error detecting PDF type: {e}")
            return {
                'type': 'unknown',
                'confidence': 0.0,
                'description': 'Unable to determine PDF type',
                'recommended_method': 'hybrid'
            }
    
    def _is_text_based_page(self, text):
        """Determine if a page contains meaningful extractable text"""
        if not text or len(text.strip()) < 20:
            return False
        
        # Check text density
        if len(text) < self.text_density_threshold:
            return False
        
        # Check for meaningful words (not just random characters)
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
        if not words:
            return False
        
        # Calculate ratio of actual words to total characters
        word_chars = sum(len(word) for word in words)
        word_ratio = word_chars / len(text) if len(text) > 0 else 0
        
        return word_ratio >= self.word_ratio_threshold
    
    def extract_text_intelligent(self, pdf_path):
        """
        Intelligently extract text based on PDF type detection
        """
        # First, detect PDF type
        pdf_info = self.detect_pdf_type(pdf_path)
        extraction_method = pdf_info['recommended_method']
        
        result = {
            'pdf_type': pdf_info,
            'text_content': "",
            'extraction_method': extraction_method,
            'pages_processed': 0
        }
        
        try:
            if extraction_method == 'text_extraction':
                # Use standard text extraction
                result['text_content'] = self.extract_text(pdf_path)
                result['pages_processed'] = self._count_pages(pdf_path)
                
            elif extraction_method == 'ocr_only':
                # Use OCR only - will be handled by calling function
                result['text_content'] = ""  # OCR will be done separately
                result['pages_processed'] = 0
                
            else:  # hybrid or unknown
                # Use both methods
                text_content = self.extract_text(pdf_path)
                result['text_content'] = text_content
                result['pages_processed'] = self._count_pages(pdf_path)
                
        except Exception as e:
            print(f"Error in intelligent extraction: {e}")
            result['text_content'] = ""
            
        return result
    
    def _count_pages(self, pdf_path):
        """Count total pages in PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except:
            return 0
    
    def analyze_pdf_content(self, pdf_path):
        """
        Comprehensive PDF analysis including type detection and content preview
        """
        try:
            # Get basic info
            pdf_info = self.get_pdf_info(pdf_path)
            
            # Detect type
            type_info = self.detect_pdf_type(pdf_path)
            
            # Sample text from first page
            sample_text = ""
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    if pdf.pages:
                        first_page_text = pdf.pages[0].extract_text() or ""
                        sample_text = first_page_text[:300] + "..." if len(first_page_text) > 300 else first_page_text
            except:
                sample_text = "Unable to extract sample text"
            
            return {
                'basic_info': pdf_info,
                'type_detection': type_info,
                'sample_text': sample_text,
                'file_size': os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
            }
            
        except Exception as e:
            print(f"Error analyzing PDF content: {e}")
            return {
                'basic_info': {'num_pages': 0, 'title': 'Unknown', 'author': 'Unknown'},
                'type_detection': {'type': 'unknown', 'confidence': 0.0, 'description': 'Analysis failed'},
                'sample_text': 'Unable to analyze',
                'file_size': 0
            }
