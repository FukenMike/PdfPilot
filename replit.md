# Legal Document Analysis System

## Overview

This is a specialized Streamlit-based legal document processing application designed for court cases, custody disputes, CPS cases, and DHR documents. The system combines intelligent PDF text extraction, OCR capabilities, and AI-powered legal analysis to identify procedural violations, due process issues, and judicial malpractice indicators. Built for family court cases, child custody disputes, CPS investigations, and related legal proceedings, it automatically detects document types and applies specialized analysis for each case type.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

- **Frontend**: Streamlit web interface for user interaction
- **Backend**: Python-based processing modules for PDF handling, OCR, image processing, and AI chat
- **AI Integration**: OpenAI GPT-4o for intelligent document analysis and Q&A
- **Image Processing**: PIL and OpenCV for image enhancement and OCR optimization

## Key Components

### 1. Main Application (app.py)
- **Purpose**: Central orchestrator and UI controller
- **Technology**: Streamlit framework
- **Responsibilities**: 
  - Session state management
  - User interface rendering
  - Component coordination
- **Design Decision**: Uses Streamlit's caching mechanism for processor initialization to improve performance

### 2. PDF Processor (pdf_processor.py)
- **Purpose**: Intelligent PDF analysis, text extraction, and image conversion
- **Technologies**: PyPDF2, pdfplumber, pdf2image, PIL, regex analysis
- **Architecture**: Intelligent type detection with optimized extraction strategy
- **Features**:
  - Automatic PDF type detection (text-based, image-based, mixed)
  - Content analysis with confidence scoring
  - Intelligent extraction method selection
  - Text density and word ratio analysis
  - Comprehensive PDF content analysis
- **Rationale**: Automatically determines optimal processing method to improve speed and accuracy while reducing unnecessary OCR processing

### 3. OCR Handler (ocr_handler.py)
- **Purpose**: Extract text from images using OCR technology
- **Technologies**: Tesseract OCR, OpenCV, PIL
- **Features**: 
  - Image preprocessing for better OCR accuracy
  - Configurable OCR settings for different text types
  - Support for both printed and handwritten text
- **Design Decision**: Implements comprehensive image preprocessing pipeline to maximize OCR accuracy

### 4. Image Processor (image_processor.py)
- **Purpose**: Enhance images for better viewing and OCR performance
- **Technologies**: PIL, OpenCV, NumPy
- **Capabilities**:
  - Contrast and brightness adjustment
  - Image enhancement for readability
  - Histogram equalization and sharpening
- **Rationale**: Separate module for image processing allows for specialized optimization without affecting other components

### 5. Chat Handler (chat_handler.py)
- **Purpose**: Provide AI-powered document analysis and Q&A
- **Technology**: OpenAI GPT-4o API, tiktoken for token estimation
- **Features**:
  - Document-specific question answering with vector-based context
  - Content summarization
  - Contextual analysis
  - Development mode with placeholder responses
  - Token usage estimation and cost calculation
  - Support for relevant chunk-based responses
- **Design Decision**: Uses GPT-4o (latest model) for optimal performance and accuracy

### 6. Memory Handler (memory_handler.py)
- **Purpose**: Manage PDF caching and vector-based document retrieval
- **Technology**: LangChain, FAISS vector store, OpenAI embeddings
- **Features**:
  - PDF content caching with hash-based identification
  - Vector store creation for semantic search
  - Document persistence across sessions
  - Cache management and cleanup utilities
  - Intelligent content retrieval using embeddings
- **Design Decision**: Implements local caching to avoid re-processing documents and enables semantic search capabilities

### 7. Legal Document Analyzer (legal_analyzer.py) - ENHANCED
- **Purpose**: Foundation legal document analysis for court cases and child welfare proceedings
- **Technology**: OpenAI GPT-4o, regex pattern matching, legal entity recognition
- **Features**: Document classification, entity extraction, basic violation detection
- **Integration**: Works with advanced violation detector and case management system

### 8. Case Management System (case_manager.py) - NEW
- **Purpose**: Complete case session management with multi-document tracking
- **Technology**: JSON persistence, hash-based document identification, timeline analysis
- **Features**: Case creation/loading, document integration, timeline generation, contradiction detection, actor tracking
- **Architecture**: Centralized case data with automatic cross-document analysis

### 9. Advanced Violation Detector (violation_detector.py) - NEW  
- **Purpose**: Comprehensive legal violation detection with severity assessment
- **Technology**: Advanced regex patterns, GPT-4o AI analysis, severity scoring algorithms
- **Features**: Constitutional violation detection, CPS-specific patterns, timeline analysis, violation heatmaps
- **Scope**: Covers due process, procedural errors, judicial misconduct, custody violations

### 10. Global Search Engine (global_search.py) - NEW
- **Purpose**: Advanced search across all case documents with multiple search modes
- **Technology**: Text search, regex patterns, GPT-4o semantic analysis
- **Features**: Multi-modal search, relevance scoring, search suggestions, result deduplication
- **Capabilities**: Comprehensive, text-only, pattern-based, and semantic search types

### 11. Report Generation System (report_generator.py) - NEW
- **Purpose**: Professional legal report generation and case analysis
- **Technology**: GPT-4o powered analysis, structured report templates, export capabilities
- **Features**: Case summaries, violation briefings, legal brief templates, data export
- **Output**: Markdown reports, JSON data export, downloadable professional documents

## Data Flow

1. **PDF Upload**: User uploads PDF through Streamlit interface (up to 150MB)
2. **Cache Check**: System calculates PDF hash and checks if document is already processed
3. **PDF Analysis**: If not cached, system analyzes PDF content to detect document type
4. **Type Detection**: Determines if PDF is text-based, image-based/scanned, or mixed content
5. **Intelligent Processing**: Selects optimal extraction method based on detection results
   - Text-based PDFs: Use fast text extraction only
   - Image-based PDFs: Apply OCR processing
   - Mixed PDFs: Use hybrid approach with both methods
6. **Image Conversion**: PDF pages converted to images for viewing and OCR (when needed)
7. **OCR Processing**: Tesseract OCR applied only when necessary based on document type
8. **Content Optimization**: Extracted content organized and optimized based on processing method
9. **Caching & Vector Storage**: Combined text saved to local cache and vector store created for semantic search
10. **AI Interaction**: User queries processed by GPT-4o using relevant chunks from vector search
11. **Response Generation**: AI generates responses with development mode toggle and token estimation

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework
- **PyPDF2 & pdfplumber**: PDF text extraction
- **pdf2image**: PDF to image conversion
- **PIL (Pillow)**: Image processing
- **OpenCV**: Advanced image processing
- **pytesseract**: OCR text extraction
- **OpenAI**: AI chat functionality
- **LangChain**: Document processing and vector operations
- **FAISS**: Vector similarity search
- **tiktoken**: Token counting and cost estimation

### System Dependencies
- **Tesseract OCR**: System-level OCR engine
- **Poppler**: PDF rendering utilities (required by pdf2image)

### API Dependencies
- **OpenAI API**: Requires valid API key for chat functionality

## Deployment Strategy

### Environment Setup
- Python environment with all required packages
- System-level installation of Tesseract OCR and Poppler
- OpenAI API key configuration through environment variables

### Configuration Management
- API keys managed through environment variables
- OCR settings configurable within the application
- Image processing parameters adjustable through UI

### Performance Considerations
- Streamlit caching for processor initialization
- Configurable DPI settings for PDF conversion
- Thread count limitations for large file processing
- Session state management for maintaining user context

### Scalability Notes
- Modular architecture allows for easy component replacement or enhancement
- Image processing pipeline can be optimized for different document types
- OCR configuration can be tuned for specific use cases (printed vs. handwritten text)

## Recent Changes - Major Platform Transformation (July 29, 2025)

### COMPLETE SYSTEM TRANSFORMATION - Legal Intelligence Platform:
1. **Advanced Case Management System**: Full multi-document case sessions with persistent storage and case tracking
2. **Comprehensive Violation Detection Engine**: Advanced pattern matching and AI-powered detection of constitutional violations, due process issues, and procedural errors with severity scoring
3. **Global Search Platform**: Multi-modal search across all case documents (text, pattern-based, and semantic AI search)
4. **Actor Tracking & Repeat Offender Detection**: Monitors judges, attorneys, caseworkers across documents with violation scoring and risk assessment
5. **Timeline Analysis & Contradiction Detection**: Chronological case analysis with gap detection and cross-document inconsistency identification
6. **Advanced Report Generation**: AI-powered legal brief templates, case summaries, violation briefings, and structured data export
7. **Risk Assessment Dashboard**: Violation heatmaps, severity scoring, and comprehensive case risk evaluation
8. **Tabbed Legal Intelligence Interface**: Professional 7-tab interface (Documents, Violations, Timeline, Search, Actor Tracking, Analysis, Reports)

### Previous Core Features (Maintained):
9. **Intelligent PDF Type Detection**: Automated system that analyzes PDF content and determines optimal processing method
10. **Memory Persistence System**: LangChain-based caching system with enhanced case integration
11. **Development Mode & Legal Analysis Mode**: Dual-mode system for testing and advanced AI analysis

### Technical Architecture Improvements:
- **Multi-Component Legal Analysis Pipeline**: 5 new specialized modules (CaseManager, ViolationDetector, GlobalSearch, ReportGenerator, enhanced LegalAnalyzer)
- **Advanced Violation Pattern Matching**: Comprehensive regex patterns for constitutional, procedural, and CPS-specific violations
- **Case Session Persistence**: JSON-based case storage with timeline, actor tracking, and contradiction detection
- **AI-Powered Legal Analysis**: GPT-4o integration for advanced legal reasoning, brief generation, and procedural analysis
- **Multi-Modal Search Architecture**: Text, pattern, and semantic search with relevance scoring and result deduplication
- **Actor Relationship Mapping**: Cross-document entity tracking with severity scoring and violation correlation
- **Timeline Analysis Engine**: Date parsing, chronological ordering, and delay detection algorithms
- **Professional Report Generation**: Markdown and JSON export capabilities with legal formatting standards

The application has been completely transformed into a comprehensive legal intelligence platform specifically designed for family court cases, child custody disputes, CPS investigations, and DHR proceedings. The system now provides:

**For Legal Professionals:**
- Complete case management with multi-document analysis
- Advanced violation detection with constitutional and procedural focus
- Professional report generation including legal briefs and case summaries
- Actor tracking for identifying repeat violators (judges, attorneys, caseworkers)
- Timeline analysis with gap detection and deadline monitoring

**For Parents and Advocates:**
- User-friendly interface that identifies legal issues without requiring legal expertise
- Automated detection of due process violations and procedural errors
- Risk assessment with clear severity indicators
- Global search capabilities to find patterns across all case documents
- Export capabilities for sharing with legal counsel

**System Capabilities:**
- Handles up to 150MB PDFs with intelligent text extraction and OCR
- Maintains persistent case sessions with full document history
- Provides both development and production modes for cost-conscious operation
- Integrates advanced AI analysis with traditional pattern matching
- Generates professional reports suitable for legal proceedings

The platform serves as "the watchdog system that courts fear" - designed to uncover procedural flaws, systemic abuse, and constitutional violations through comprehensive intelligent document analysis. Optimized for single-user deployment with enterprise-level analysis capabilities.