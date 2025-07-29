import os
from openai import OpenAI
import tiktoken

class ChatHandler:
    """Handles AI-powered chat interactions about PDF content"""
    
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
        self.client = OpenAI(api_key=api_key)
        
        # System prompt for PDF analysis
        self.system_prompt = """You are an AI assistant that helps users understand and analyze PDF documents. 
        You have access to the full text content of a PDF document that has been extracted using both standard PDF text extraction and OCR.
        
        Your capabilities include:
        - Answering questions about the document content
        - Summarizing sections or the entire document
        - Finding specific information within the document
        - Explaining complex concepts mentioned in the document
        - Identifying key themes, topics, and important details
        - Helping with document analysis and interpretation
        
        Guidelines:
        - Base your responses solely on the provided document content
        - If information is not available in the document, clearly state that
        - Provide specific page references when possible
        - Be helpful, accurate, and concise
        - If the document contains forms or structured data, help interpret and explain them
        - For handwritten or OCR'd text that might have errors, be understanding of potential inaccuracies
        """
    
    def estimate_tokens(self, text):
        """Estimate token count for text"""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except:
            # Fallback estimation: roughly 4 characters per token
            return len(text) // 4
    
    def estimate_request_cost(self, messages, max_tokens=1000):
        """Estimate cost of API request"""
        try:
            # Calculate input tokens
            input_text = ""
            for message in messages:
                input_text += message["content"] + " "
            
            input_tokens = self.estimate_tokens(input_text)
            output_tokens = max_tokens
            
            # GPT-4o pricing (as of 2024): $0.005 per 1K input tokens, $0.015 per 1K output tokens
            input_cost = (input_tokens / 1000) * 0.005
            output_cost = (output_tokens / 1000) * 0.015
            total_cost = input_cost + output_cost
            
            return {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'estimated_cost': total_cost,
                'cost_breakdown': f"Input: ${input_cost:.4f} + Output: ${output_cost:.4f} = ${total_cost:.4f}"
            }
        except:
            return {
                'input_tokens': 0,
                'output_tokens': 0,
                'estimated_cost': 0.0,
                'cost_breakdown': "Unable to estimate cost"
            }
    
    def get_response(self, user_question, pdf_content, development_mode=False, relevant_chunks=None):
        """Get AI response based on user question and PDF content"""
        try:
            # Development mode - return placeholder response
            if development_mode:
                return f"[DEV MODE] This is a placeholder response for your question: '{user_question}'. In production mode, I would analyze the PDF content and provide a detailed answer based on the document."
            
            # Use relevant chunks if available (from vector search)
            content_to_use = pdf_content
            if relevant_chunks:
                content_to_use = "\n\n".join(relevant_chunks)
                content_to_use = f"Relevant document sections:\n{content_to_use}"
            
            # Prepare the conversation
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Document content:\n{content_to_use}\n\nUser question: {user_question}"}
            ]
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error getting AI response: {str(e)}. Please check your OpenAI API key."
    
    def summarize_document(self, pdf_content):
        """Generate a summary of the entire document"""
        try:
            prompt = """Please provide a comprehensive summary of this document. Include:
            - Main topics and themes
            - Key findings or important information
            - Document structure and organization
            - Any notable details or insights
            
            Document content:
            """ + pdf_content
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1500,
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def extract_key_information(self, pdf_content, information_type):
        """Extract specific types of information from the document"""
        try:
            prompt = f"""Please extract and list all {information_type} mentioned in this document. 
            Present the information in a clear, organized format.
            
            Document content:
            """ + pdf_content
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error extracting {information_type}: {str(e)}"
    
    def analyze_document_structure(self, pdf_content):
        """Analyze the structure and organization of the document"""
        try:
            prompt = """Please analyze the structure and organization of this document. Include:
            - Document type (report, form, letter, etc.)
            - Main sections and their purposes
            - Information hierarchy
            - Any forms, tables, or structured elements
            - Overall organization pattern
            
            Document content:
            """ + pdf_content
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.4
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing document structure: {str(e)}"
    
    def answer_specific_question(self, question, pdf_content, context=""):
        """Answer a specific question with additional context"""
        try:
            prompt = f"""Based on the document content provided, please answer this specific question: {question}
            
            Additional context: {context}
            
            Document content:
            """ + pdf_content
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=800,
                temperature=0.6
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error answering question: {str(e)}"
