import streamlit as st
import os
import tempfile
import json
import hashlib
from pdf_processor import PDFProcessor
from ocr_handler import OCRHandler
from chat_handler import ChatHandler
from image_processor import ImageProcessor
from memory_handler import MemoryHandler
from legal_analyzer import LegalDocumentAnalyzer
from case_manager import CaseManager
from violation_detector import ViolationDetector
from global_search import GlobalSearch
from report_generator import ReportGenerator
import base64
from io import BytesIO
import tiktoken

# Page configuration
st.set_page_config(
    page_title="PDF Chatbot with OCR",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "pdf_images" not in st.session_state:
    st.session_state.pdf_images = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "processed_pdf" not in st.session_state:
    st.session_state.processed_pdf = False
if "contrast_adjustment" not in st.session_state:
    st.session_state.contrast_adjustment = 1.0
if "brightness_adjustment" not in st.session_state:
    st.session_state.brightness_adjustment = 1.0
if "development_mode" not in st.session_state:
    st.session_state.development_mode = False
if "pdf_hash" not in st.session_state:
    st.session_state.pdf_hash = ""
if "memory_loaded" not in st.session_state:
    st.session_state.memory_loaded = False
if "pdf_analysis" not in st.session_state:
    st.session_state.pdf_analysis = None
if "legal_analysis" not in st.session_state:
    st.session_state.legal_analysis = None
if "current_case" not in st.session_state:
    st.session_state.current_case = None
if "case_data" not in st.session_state:
    st.session_state.case_data = None
if "legal_analysis_mode" not in st.session_state:
    st.session_state.legal_analysis_mode = False

# Initialize processors
@st.cache_resource
def get_processors():
    pdf_processor = PDFProcessor()
    ocr_handler = OCRHandler()
    chat_handler = ChatHandler()
    image_processor = ImageProcessor()
    memory_handler = MemoryHandler()
    legal_analyzer = LegalDocumentAnalyzer()
    case_manager = CaseManager()
    violation_detector = ViolationDetector()
    global_search = GlobalSearch()
    report_generator = ReportGenerator()
    return pdf_processor, ocr_handler, chat_handler, image_processor, memory_handler, legal_analyzer, case_manager, violation_detector, global_search, report_generator

pdf_processor, ocr_handler, chat_handler, image_processor, memory_handler, legal_analyzer, case_manager, violation_detector, global_search, report_generator = get_processors()

def reset_session():
    """Reset all session state variables"""
    st.session_state.chat_history = []
    st.session_state.pdf_text = ""
    st.session_state.pdf_images = []
    st.session_state.current_page = 0
    st.session_state.processed_pdf = False
    st.session_state.contrast_adjustment = 1.0
    st.session_state.brightness_adjustment = 1.0
    st.session_state.pdf_hash = ""
    st.session_state.memory_loaded = False
    st.session_state.pdf_analysis = None
    st.session_state.legal_analysis = None

def calculate_pdf_hash(uploaded_file):
    """Calculate hash of uploaded PDF for caching"""
    uploaded_file.seek(0)
    content = uploaded_file.read()
    uploaded_file.seek(0)
    return hashlib.md5(content).hexdigest()

def estimate_tokens(text):
    """Estimate token count for GPT requests"""
    try:
        encoding = tiktoken.encoding_for_model("gpt-4o")
        return len(encoding.encode(text))
    except:
        # Fallback estimation: roughly 4 characters per token
        return len(text) // 4

def process_uploaded_pdf(uploaded_file):
    """Process the uploaded PDF file with intelligent type detection and caching support"""
    try:
        # Calculate PDF hash for caching
        pdf_hash = calculate_pdf_hash(uploaded_file)
        st.session_state.pdf_hash = pdf_hash
        
        # Check if PDF is already cached
        cached_data = memory_handler.load_pdf_data(pdf_hash)
        
        if cached_data:
            st.info("📦 Loading from cache (PDF already processed)")
            st.session_state.pdf_text = cached_data['pdf_text']
            st.session_state.pdf_images = cached_data['pdf_images']
            st.session_state.processed_pdf = True
            st.session_state.memory_loaded = True
            
            # Load cached analysis if available
            if 'metadata' in cached_data and cached_data['metadata']:
                st.session_state.pdf_analysis = cached_data['metadata']
                if 'legal_analysis' in cached_data['metadata']:
                    st.session_state.legal_analysis = cached_data['metadata']['legal_analysis']
                    
                    # Add to case if case is active and document not already added
                    if (st.session_state.case_data and 
                        pdf_hash not in st.session_state.case_data.get('documents', {})):
                        st.session_state.case_data = case_manager.add_document_to_case(
                            st.session_state.case_data,
                            pdf_hash,
                            cached_data['metadata'],
                            cached_data['metadata']['legal_analysis']
                        )
                        case_manager.save_case_session(st.session_state.current_case, st.session_state.case_data)
            
            st.success(f"PDF loaded from cache! {len(cached_data['pdf_images'])} pages available.")
            return
        
        # Create temporary file
        uploaded_file.seek(0)  # Reset file pointer
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        
        # Analyze PDF content and detect type
        with st.spinner("Analyzing PDF content..."):
            analysis = pdf_processor.analyze_pdf_content(tmp_file_path)
            pdf_type = analysis['type_detection']
            
            # Display analysis results
            st.info(f"📄 **PDF Analysis:** {pdf_type['description']}\n\n"
                   f"**Type:** {pdf_type['type'].title()} (Confidence: {pdf_type['confidence']:.1%})\n\n"
                   f"**Processing Method:** {pdf_type['recommended_method'].replace('_', ' ').title()}")
        
        # Process PDF based on detected type
        with st.spinner("Processing PDF using optimal method..."):
            extraction_result = pdf_processor.extract_text_intelligent(tmp_file_path)
            pdf_text = extraction_result['text_content']
            extraction_method = extraction_result['extraction_method']
            
            # Convert PDF to images (always needed for viewing)
            pdf_images = pdf_processor.convert_to_images(tmp_file_path)
            
            # Handle OCR based on detection results
            ocr_text = ""
            if extraction_method in ['ocr_only', 'hybrid'] or not pdf_text.strip():
                st.info("🔍 Applying OCR - this may take longer for image-based PDFs")
                progress_bar = st.progress(0)
                
                for i, image in enumerate(pdf_images):
                    progress_bar.progress((i + 1) / len(pdf_images))
                    page_ocr_text = ocr_handler.extract_text_from_image(image)
                    if page_ocr_text.strip():
                        ocr_text += f"\n--- Page {i+1} OCR ---\n{page_ocr_text}\n"
                
                progress_bar.empty()
            
            # Combine text based on what was extracted
            if extraction_method == 'text_extraction' and pdf_text.strip():
                combined_text = f"PDF Text (Extracted):\n{pdf_text}"
                processing_note = "Used text extraction (faster, more accurate)"
            elif extraction_method == 'ocr_only' or not pdf_text.strip():
                combined_text = f"OCR Text:\n{ocr_text}"
                processing_note = "Used OCR for scanned document"
            else:  # hybrid
                combined_text = f"PDF Text (Extracted):\n{pdf_text}\n\nOCR Text (Additional):\n{ocr_text}"
                processing_note = "Used hybrid approach (text extraction + OCR)"
            
            # Save processing metadata
            metadata = {
                'pdf_type': pdf_type,
                'extraction_method': extraction_method,
                'processing_note': processing_note,
                'analysis': analysis
            }
            
            # Perform comprehensive legal analysis
            st.info("⚖️ Performing comprehensive legal analysis...")
            legal_analysis = legal_analyzer.comprehensive_legal_analysis(
                combined_text, 
                development_mode=st.session_state.development_mode
            )
            
            # Advanced violation detection
            st.info("🔍 Detecting violations and procedural issues...")
            document_type = legal_analysis.get('document_type', {}).get('type', 'unknown')
            advanced_violations = violation_detector.detect_violations(combined_text, document_type)
            
            # Merge violations
            all_violations = legal_analysis.get('potential_violations', []) + advanced_violations
            legal_analysis['all_violations'] = all_violations
            legal_analysis['violation_summary'] = violation_detector.generate_violation_heatmap_data(all_violations)
            
            # Add advanced AI analysis if enabled
            if st.session_state.legal_analysis_mode and not st.session_state.development_mode:
                st.info("🧠 Performing advanced AI legal analysis...")
                ai_analysis = violation_detector.advanced_violation_analysis(combined_text, st.session_state.development_mode)
                legal_analysis['ai_analysis'] = ai_analysis
            
            # Add filename to metadata
            metadata['filename'] = uploaded_file.name
            metadata['legal_analysis'] = legal_analysis
            
            # Save to cache
            st.info("💾 Saving to cache for future use...")
            memory_handler.save_pdf_data(pdf_hash, combined_text, pdf_images, metadata)
            
            # Update session state
            st.session_state.pdf_text = combined_text
            st.session_state.pdf_images = pdf_images
            st.session_state.processed_pdf = True
            st.session_state.memory_loaded = True
            st.session_state.pdf_analysis = metadata
            st.session_state.legal_analysis = legal_analysis
            
            # Add document to case if case is active
            if st.session_state.case_data:
                st.info("📋 Adding document to active case...")
                st.session_state.case_data = case_manager.add_document_to_case(
                    st.session_state.case_data,
                    pdf_hash,
                    metadata,
                    legal_analysis
                )
                
                # Update case analysis
                case_manager.generate_timeline(st.session_state.case_data)
                case_manager.detect_contradictions(st.session_state.case_data)
                case_manager.track_repeat_actors(st.session_state.case_data)
                
                # Save updated case
                case_manager.save_case_session(st.session_state.current_case, st.session_state.case_data)
                
                st.success(f"✅ Document added to case: {st.session_state.case_data['case_name']}")
            
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        st.success(f"✅ PDF processed successfully using {processing_note.lower()}!\n\n"
                  f"Extracted content from {len(pdf_images)} pages.")
        
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")

def display_pdf_page(page_index):
    """Display a specific page of the PDF with adjustments"""
    if page_index < len(st.session_state.pdf_images):
        image = st.session_state.pdf_images[page_index]
        
        # Apply contrast and brightness adjustments
        adjusted_image = image_processor.adjust_contrast_brightness(
            image, 
            st.session_state.contrast_adjustment,
            st.session_state.brightness_adjustment
        )
        
        st.image(adjusted_image, caption=f"Page {page_index + 1}", use_column_width=True)

def search_in_pdf(query):
    """Search for text in the PDF content"""
    if not st.session_state.pdf_text:
        return []
    
    lines = st.session_state.pdf_text.split('\n')
    results = []
    
    for i, line in enumerate(lines):
        if query.lower() in line.lower():
            results.append(f"Line {i+1}: {line.strip()}")
    
    return results

# Main UI
st.title("⚖️ Legal Intelligence & Case Analysis Platform")
st.markdown("**Advanced AI-Powered Legal Audit Toolkit for Family Court, CPS & Child Custody Cases**")
st.markdown("Comprehensive document analysis • Violation detection • Timeline tracking • Actor monitoring • Case intelligence")

# Advanced Legal Case Management Sidebar
with st.sidebar:
    st.header("📋 Case Management")
    
    # Case selection/creation
    st.subheader("Active Case")
    
    # List existing cases
    available_cases = case_manager.list_case_sessions()
    case_options = ["Create New Case"] + [f"{case['case_name']} ({case['case_id']})" for case in available_cases]
    
    selected_case = st.selectbox(
        "Select or Create Case:",
        case_options,
        index=0 if not st.session_state.current_case else next(
            (i for i, opt in enumerate(case_options) if st.session_state.current_case in opt), 0
        )
    )
    
    # Handle case selection
    if selected_case == "Create New Case":
        case_name = st.text_input("New Case Name:", placeholder="Smith v. State CPS - 2025")
        if st.button("Create Case") and case_name:
            case_id, case_data_template = case_manager.create_case_session(case_name)
            st.session_state.current_case = case_id
            st.session_state.case_data = case_data_template
            st.success(f"Created case: {case_name}")
            st.rerun()
    else:
        # Load existing case
        case_id = selected_case.split("(")[-1].rstrip(")")
        if st.session_state.current_case != case_id:
            loaded_case = case_manager.load_case_session(case_id)
            if loaded_case:
                st.session_state.current_case = case_id
                st.session_state.case_data = loaded_case
                st.success(f"Loaded case: {loaded_case['case_name']}")
                st.rerun()
    
    # Display current case info
    if st.session_state.case_data:
        st.info(f"**Active:** {st.session_state.case_data['case_name']}")
        doc_count = len(st.session_state.case_data.get('documents', {}))
        violation_count = len(st.session_state.case_data.get('violations', []))
        high_violations = len([v for v in st.session_state.case_data.get('violations', []) if v.get('severity') == 'high'])
        st.write(f"📄 Documents: {doc_count}")
        st.write(f"⚠️ Total Violations: {violation_count}")
        if high_violations > 0:
            st.error(f"🚨 Critical Issues: {high_violations}")
    
    st.divider()
    
    # System settings
    st.header("⚙️ Analysis Settings")
    
    # Development mode toggle
    st.session_state.development_mode = st.toggle(
        "🔧 Development Mode", 
        value=st.session_state.development_mode,
        help="Disable GPT API calls to save tokens during testing"
    )
    
    # Legal Analysis Mode toggle
    st.session_state.legal_analysis_mode = st.toggle(
        "⚖️ Legal Analysis Mode",
        value=st.session_state.legal_analysis_mode,
        help="Enable advanced AI legal analysis and brief generation"
    )
    
    if st.session_state.development_mode:
        st.info("🔧 Dev mode - AI disabled")
    
    st.divider()
    
    # Document upload section
    st.header("📁 Add Document to Case")
    
    if not st.session_state.case_data:
        st.warning("Create or select a case first")
    else:
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Legal PDF (max 150MB)", 
            type=['pdf'],
            help="Court documents, CPS reports, motions, orders, etc."
        )
        
        if uploaded_file is not None:
            # Check file size
            file_size = len(uploaded_file.read())
            uploaded_file.seek(0)  # Reset file pointer
            
            if file_size > 150 * 1024 * 1024:  # 150MB in bytes
                st.error("File size exceeds 150MB limit!")
            else:
                st.info(f"File size: {file_size / (1024*1024):.2f} MB")
                
                if st.button("🔍 Analyze Document"):
                    process_uploaded_pdf(uploaded_file)
    
    # Cache Management
    st.header("💾 System Cache")
    cached_files = memory_handler.get_cached_files()
    cache_size = memory_handler.get_cache_size()
    
    if cached_files:
        st.write(f"📦 {len(cached_files)} files, {cache_size:.2f} MB")
        if st.button("Clear Cache"):
            memory_handler.clear_cache()
            st.success("Cache cleared!")
            st.rerun()
    else:
        st.write("No cached files")
    
    # PDF viewer controls
    if st.session_state.processed_pdf:
        st.header("PDF Viewer")
        
        # Page navigation
        total_pages = len(st.session_state.pdf_images)
        if total_pages > 0:
            page_num = st.number_input(
                "Page", 
                min_value=1, 
                max_value=total_pages, 
                value=st.session_state.current_page + 1
            )
            st.session_state.current_page = page_num - 1
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Previous") and st.session_state.current_page > 0:
                    st.session_state.current_page -= 1
                    st.rerun()
            with col2:
                if st.button("Next") and st.session_state.current_page < total_pages - 1:
                    st.session_state.current_page += 1
                    st.rerun()
        
        # Image adjustment controls
        st.header("Image Adjustments")
        
        contrast = st.slider(
            "Contrast", 
            min_value=0.5, 
            max_value=3.0, 
            value=st.session_state.contrast_adjustment,
            step=0.1
        )
        
        brightness = st.slider(
            "Brightness", 
            min_value=0.5, 
            max_value=2.0, 
            value=st.session_state.brightness_adjustment,
            step=0.1
        )
        
        if contrast != st.session_state.contrast_adjustment or brightness != st.session_state.brightness_adjustment:
            st.session_state.contrast_adjustment = contrast
            st.session_state.brightness_adjustment = brightness
            st.rerun()
        
        # Reset adjustments
        if st.button("Reset Adjustments"):
            st.session_state.contrast_adjustment = 1.0
            st.session_state.brightness_adjustment = 1.0
            st.rerun()
        
        # Search functionality
        st.header("🔍 Search in PDF")
        search_query = st.text_input("Search text:")
        
        col1, col2 = st.columns(2)
        with col1:
            if search_query and st.button("Text Search"):
                results = search_in_pdf(search_query)
                if results:
                    st.write(f"Found {len(results)} results:")
                    for result in results[:10]:  # Show first 10 results
                        st.write(f"• {result}")
                    if len(results) > 10:
                        st.write(f"... and {len(results) - 10} more results")
                else:
                    st.write("No results found.")
        
        with col2:
            if search_query and st.button("Smart Search") and st.session_state.memory_loaded:
                with st.spinner("Searching with AI..."):
                    similar_content = memory_handler.search_similar_content(
                        st.session_state.pdf_hash, 
                        search_query, 
                        k=5
                    )
                    if similar_content:
                        st.write(f"Found {len(similar_content)} relevant sections:")
                        for i, content in enumerate(similar_content, 1):
                            st.write(f"**Section {i}:** {content[:200]}...")
                    else:
                        st.write("No similar content found.")

# Advanced Legal Intelligence Interface
if st.session_state.case_data:
    # Case overview header
    st.header(f"📋 {st.session_state.case_data['case_name']}")
    
    # Case statistics
    docs = st.session_state.case_data.get('documents', {})
    violations = st.session_state.case_data.get('violations', [])
    high_violations = [v for v in violations if v.get('severity') == 'high']
    timeline_events = len(st.session_state.case_data.get('timeline', []))
    
    # Quick stats bar
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Documents", len(docs))
    with col2:
        st.metric("Total Violations", len(violations))
    with col3:
        st.metric("Critical Issues", len(high_violations), delta="High Priority" if len(high_violations) > 0 else None)
    with col4:
        st.metric("Timeline Events", timeline_events)
    with col5:
        risk_level = "Critical" if len(high_violations) >= 3 else "High" if len(high_violations) >= 1 else "Medium" if len(violations) >= 5 else "Low"
        st.metric("Risk Level", risk_level)
    
    # Main tabbed interface
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📄 Documents", "🚨 Violations", "📅 Timeline", "🔍 Global Search", 
        "👥 Actor Tracking", "📊 Analysis", "📋 Reports"
    ])
    
    with tab1:
        st.subheader("📄 Case Documents")
        
        if docs:
            for doc_hash, doc_info in docs.items():
                with st.expander(f"{doc_info.get('filename', 'Unknown Document')}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        doc_type = doc_info.get('legal_analysis', {}).get('document_type', {}).get('type', 'unknown')
                        upload_date = doc_info.get('upload_date', 'Unknown')[:10] if doc_info.get('upload_date') != 'Unknown' else 'Unknown'
                        doc_violations = [v for v in violations if v.get('document_hash') == doc_hash]
                        
                        st.write(f"**Type:** {doc_type.title()}")
                        st.write(f"**Date Added:** {upload_date}")
                        st.write(f"**Violations Found:** {len(doc_violations)}")
                        
                        if doc_violations:
                            high_count = len([v for v in doc_violations if v.get('severity') == 'high'])
                            if high_count > 0:
                                st.error(f"🚨 {high_count} critical issues in this document")
                    
                    with col2:
                        if st.button(f"View Document", key=f"view_{doc_hash}"):
                            # Load this specific document for viewing
                            cached_data = memory_handler.load_pdf_data(doc_hash)
                            if cached_data:
                                st.session_state.pdf_text = cached_data['pdf_text']
                                st.session_state.pdf_images = cached_data['pdf_images']
                                st.session_state.processed_pdf = True
                                st.session_state.pdf_analysis = cached_data.get('metadata', {})
                                st.session_state.legal_analysis = cached_data.get('metadata', {}).get('legal_analysis', {})
                                st.success(f"Loaded: {doc_info.get('filename', 'Document')}")
                                st.rerun()
        else:
            st.info("No documents in this case yet. Upload documents using the sidebar.")
    
    with tab2:
        st.subheader("🚨 Violations & Legal Issues")
        
        if violations:
            # Violation summary
            violation_summary = violation_detector.generate_violation_heatmap_data(violations)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("High Severity", violation_summary['severity_counts']['high'], delta="Critical" if violation_summary['severity_counts']['high'] > 0 else None)
            with col2:
                st.metric("Medium Severity", violation_summary['severity_counts']['medium'])
            with col3:
                st.metric("Low Severity", violation_summary['severity_counts']['low'])
            
            st.write(f"**Overall Risk Assessment:** {violation_summary['risk_level'].title()}")
            
            # Group violations by severity
            high_violations = [v for v in violations if v.get('severity') == 'high']
            medium_violations = [v for v in violations if v.get('severity') == 'medium']
            low_violations = [v for v in violations if v.get('severity') == 'low']
            
            if high_violations:
                st.error("### 🚨 CRITICAL VIOLATIONS - IMMEDIATE ATTENTION REQUIRED")
                for i, violation in enumerate(high_violations, 1):
                    with st.expander(f"{i}. {violation.get('description', violation.get('type', 'Unknown')).title()}", expanded=True):
                        st.write(f"**Document:** {violation.get('document_name', 'Unknown')}")
                        st.write(f"**Type:** {violation.get('type', 'unknown').replace('_', ' ').title()}")
                        st.write(f"**Context:** {violation.get('context', 'No context available')}")
                        if violation.get('pattern_matched'):
                            st.code(f"Pattern: {violation['pattern_matched']}")
            
            if medium_violations:
                st.warning("### ⚠️ SIGNIFICANT PROCEDURAL VIOLATIONS")
                for i, violation in enumerate(medium_violations[:10], 1):  # Show top 10
                    with st.expander(f"{i}. {violation.get('description', violation.get('type', 'Unknown')).title()}"):
                        st.write(f"**Document:** {violation.get('document_name', 'Unknown')}")
                        st.write(f"**Context:** {violation.get('context', 'No context available')[:200]}...")
        else:
            st.info("No violations detected yet. Process more documents to identify potential legal issues.")
    
    with tab3:
        st.subheader("📅 Case Timeline")
        
        timeline = st.session_state.case_data.get('timeline', [])
        if timeline:
            # Timeline visualization
            st.write(f"**{len(timeline)} timeline events identified across all documents**")
            
            # Timeline violations
            timeline_violations = violation_detector.analyze_timeline_violations(timeline)
            if timeline_violations:
                st.error(f"🚨 {len(timeline_violations)} timeline violations detected:")
                for tv in timeline_violations:
                    st.write(f"• **{tv['description']}** - {tv['context']}")
            
            # Display timeline
            for event in timeline:
                col1, col2, col3 = st.columns([2, 3, 2])
                with col1:
                    st.write(f"**{event.get('date_str', 'Unknown Date')}**")
                with col2:
                    st.write(f"{event.get('document_type', 'unknown').title()}")
                with col3:
                    st.write(f"{event.get('document', 'Unknown Document')}")
        else:
            st.info("No timeline events found. Timeline is generated automatically from dates found in documents.")
    
    with tab4:
        st.subheader("🔍 Global Case Search")
        
        # Search interface
        search_query = st.text_input("Search across all case documents:", placeholder="due process violation, custody order, timeline issues")
        
        search_type = st.selectbox(
            "Search Type:",
            ["comprehensive", "text_only", "pattern_based", "semantic"],
            help="Comprehensive combines all search methods for best results"
        )
        
        if st.button("🔍 Search Case") and search_query:
            with st.spinner("Searching across all documents..."):
                # Add development mode to case data for search
                search_case_data = st.session_state.case_data.copy()
                search_case_data['development_mode'] = st.session_state.development_mode
                
                search_results = global_search.search_all_documents(search_case_data, search_query, search_type)
                
                st.write(f"**Found {search_results['total_matches']} matches for '{search_query}'**")
                
                if search_results['results']:
                    for result in search_results['results'][:20]:  # Show top 20
                        with st.expander(f"📄 {result.get('document_name', 'Unknown')} - {result.get('match_type', 'unknown').title()} Match"):
                            st.write(f"**Relevance Score:** {result.get('relevance_score', 0):.2f}")
                            st.write(f"**Context:** {result.get('context', 'No context available')}")
                            if result.get('relevance_reason'):
                                st.write(f"**Why Relevant:** {result['relevance_reason']}")
                else:
                    st.info("No matches found. Try different search terms or search types.")
        
        # Search suggestions
        if docs:
            st.write("**Suggested Searches:**")
            suggestions = global_search.generate_search_suggestions(st.session_state.case_data)
            for suggestion in suggestions[:8]:
                if st.button(suggestion, key=f"suggestion_{suggestion}"):
                    # Auto-fill search
                    st.session_state.search_query = suggestion
                    st.rerun()
    
    with tab5:
        st.subheader("👥 Actor Tracking & Repeat Offenders")
        
        actor_tracking = st.session_state.case_data.get('actor_tracking', {})
        if actor_tracking:
            st.write("**Judges, attorneys, and caseworkers with multiple violations:**")
            
            # Sort by severity score
            sorted_actors = sorted(actor_tracking.items(), key=lambda x: x[1].get('severity_score', 0), reverse=True)
            
            for actor, info in sorted_actors:
                actor_type = info.get('type', 'unknown').title()
                violation_count = len(info.get('violations', []))
                severity_score = info.get('severity_score', 0)
                documents = info.get('documents', [])
                
                with st.expander(f"{actor} ({actor_type}) - Score: {severity_score}", expanded=severity_score > 5):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Role:** {actor_type}")
                        st.write(f"**Violations:** {violation_count}")
                        st.write(f"**Severity Score:** {severity_score}")
                        
                        if severity_score > 5:
                            st.error("🚨 High-risk actor - Consider recusal request")
                        elif severity_score > 2:
                            st.warning("⚠️ Multiple violations detected")
                    
                    with col2:
                        st.write("**Documents Involved:**")
                        for doc in documents:
                            st.write(f"• {doc}")
                        
                        st.write("**Violation Types:**")
                        violation_types = set(v.get('type', 'unknown') for v in info.get('violations', []))
                        for vtype in violation_types:
                            st.write(f"• {vtype.replace('_', ' ').title()}")
        else:
            st.info("No repeat actors identified yet. Actor tracking requires multiple documents with violations.")
    
    with tab6:
        st.subheader("📊 Advanced Legal Analysis")
        
        if st.session_state.legal_analysis_mode:
            if st.button("🧠 Generate AI Legal Analysis") and not st.session_state.development_mode:
                with st.spinner("Generating comprehensive legal analysis..."):
                    analysis_report = report_generator.generate_case_summary(st.session_state.case_data, st.session_state.development_mode)
                    st.markdown(analysis_report)
            elif st.session_state.development_mode:
                st.info("Enable production mode for AI-powered legal analysis")
            
            if st.button("📝 Generate Legal Brief Template") and not st.session_state.development_mode:
                with st.spinner("Creating legal brief template..."):
                    brief_template = report_generator.generate_legal_brief_template(st.session_state.case_data, st.session_state.development_mode)
                    st.markdown(brief_template)
            elif st.session_state.development_mode:
                st.info("Enable production mode for legal brief generation")
        else:
            st.info("Enable Legal Analysis Mode in the sidebar to access advanced AI analysis features")
        
        # Case contradictions
        contradictions = st.session_state.case_data.get('contradictions', [])
        if contradictions:
            st.error("🔍 **CONTRADICTIONS DETECTED:**")
            for contradiction in contradictions:
                st.write(f"• **{contradiction.get('type', 'unknown').replace('_', ' ').title()}:** {contradiction.get('description', 'No description')}")
                st.write(f"  Documents: {', '.join(contradiction.get('documents', []))}")
    
    with tab7:
        st.subheader("📋 Reports & Export")
        
        # Report generation options
        st.write("**Generate Reports:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Case Summary Report"):
                report = report_generator.generate_case_summary(st.session_state.case_data, st.session_state.development_mode)
                st.download_button(
                    label="💾 Download Case Summary",
                    data=report,
                    file_name=f"{st.session_state.case_data['case_name']}_summary.md",
                    mime="text/markdown"
                )
                st.success("Case summary generated!")
        
        with col2:
            if st.button("⚖️ Violation Briefing"):
                violations = st.session_state.case_data.get('violations', [])
                if violations:
                    briefing = report_generator.generate_violation_briefing(violations, st.session_state.case_data['case_name'])
                    st.download_button(
                        label="💾 Download Violation Brief",
                        data=briefing,
                        file_name=f"{st.session_state.case_data['case_name']}_violations.md",
                        mime="text/markdown"
                    )
                    st.success("Violation briefing generated!")
                else:
                    st.info("No violations to report")
        
        with col3:
            if st.button("📊 Export Case Data"):
                export_data = report_generator.export_case_data(st.session_state.case_data)
                import json
                st.download_button(
                    label="💾 Download Case Data",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"{st.session_state.case_data['case_name']}_data.json",
                    mime="application/json"
                )
                st.success("Case data exported!")
        
        # Save case session
        if st.button("💾 Save Case Session"):
            case_manager.save_case_session(st.session_state.current_case, st.session_state.case_data)
            st.success("Case session saved!")

else:
    # No active case - show getting started
    st.header("🚀 Getting Started")
    st.markdown("""
    ### Welcome to the Legal Intelligence Platform
    
    This advanced AI-powered system is designed specifically for:
    - **Family Court Cases** - Custody disputes, parental rights
    - **CPS Cases** - Child protective services investigations
    - **DHR Cases** - Department of Human Resources proceedings  
    - **ISP Plans** - Individualized service plans
    - **Court Motions & Orders** - All types of legal documents
    
    ### How to Begin:
    1. **Create a New Case** in the sidebar (e.g., "Smith v. State CPS - 2025")
    2. **Upload Legal Documents** - Court orders, CPS reports, motions, etc.
    3. **Let AI Analyze** - System automatically detects violations and issues
    4. **Review Results** - Timeline, violations, actor tracking, and more
    5. **Generate Reports** - Legal briefs, violation summaries, case analysis
    
    ### Key Features:
    - 🔍 **Automatic Violation Detection** - Finds due process violations, procedural errors
    - 📅 **Timeline Analysis** - Chronological case progression with gap detection  
    - 👥 **Actor Tracking** - Monitors judges, attorneys, caseworkers across documents
    - 🔍 **Global Search** - AI-powered search across all case documents
    - 📊 **Risk Assessment** - Severity scoring and legal issue prioritization
    - 📋 **Report Generation** - Professional legal briefs and case summaries
    
    **Start by creating your first case in the sidebar →**
    """)

# Current document viewer (if document is loaded)
if st.session_state.processed_pdf and st.session_state.pdf_images:
    st.header("📄 Document Viewer")
    display_pdf_page(st.session_state.current_page)
    
    if st.session_state.processed_pdf:
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.write(f"**You:** {message['content']}")
                else:
                    st.write(f"**Assistant:** {message['content']}")
        
        # Legal-focused chat input
        user_question = st.text_input(
            "Ask about legal issues, violations, or case details:",
            placeholder="Are there any due process violations? What are the key legal issues?"
        )
        
        # Token estimation and cost display
        if user_question and not st.session_state.development_mode:
            # Prepare messages for estimation
            messages = [
                {"role": "system", "content": chat_handler.system_prompt},
                {"role": "user", "content": f"Document content:\n{st.session_state.pdf_text}\n\nUser question: {user_question}"}
            ]
            
            cost_info = chat_handler.estimate_request_cost(messages)
            
            st.info(f"📊 **Token Estimate:** {cost_info['input_tokens']} input + {cost_info['output_tokens']} output tokens\n\n💰 **Estimated Cost:** {cost_info['cost_breakdown']}")
        
        # Send button with enhanced functionality
        if st.button("Send") and user_question:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_question
            })
            
            # Get AI response with memory-based retrieval
            with st.spinner("Thinking..."):
                try:
                    # Use vector search if available
                    relevant_chunks = []
                    if st.session_state.memory_loaded and st.session_state.pdf_hash:
                        relevant_chunks = memory_handler.search_similar_content(
                            st.session_state.pdf_hash, 
                            user_question, 
                            k=3
                        )
                    
                    # Get response
                    response = chat_handler.get_response(
                        user_question, 
                        st.session_state.pdf_text,
                        development_mode=st.session_state.development_mode,
                        relevant_chunks=relevant_chunks if relevant_chunks else None
                    )
                    
                    # Add assistant message to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error getting AI response: {str(e)}")
        
        # Memory and analysis info
        if st.session_state.memory_loaded:
            st.success("🧠 Memory loaded - Using cached content for faster responses")
        
        # Display PDF analysis info
        if st.session_state.pdf_analysis:
            analysis = st.session_state.pdf_analysis
            with st.expander("📊 PDF Processing Details"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Document Type:** {analysis['pdf_type']['type'].title()}")
                    st.write(f"**Confidence:** {analysis['pdf_type']['confidence']:.1%}")
                with col2:
                    st.write(f"**Method Used:** {analysis['extraction_method'].replace('_', ' ').title()}")
                    st.write(f"**Processing:** {analysis['processing_note']}")
                
                if 'analysis' in analysis and 'sample_text' in analysis['analysis']:
                    st.write("**Content Preview:**")
                    st.text(analysis['analysis']['sample_text'][:200] + "..." if len(analysis['analysis']['sample_text']) > 200 else analysis['analysis']['sample_text'])
        
        # Display Legal Analysis
        if st.session_state.legal_analysis:
            legal = st.session_state.legal_analysis
            with st.expander("⚖️ Legal Document Analysis", expanded=True):
                
                # Document Classification
                if 'document_type' in legal:
                    doc_type = legal['document_type']
                    st.write(f"**Document Classification:** {doc_type['type'].title()} (Confidence: {doc_type['confidence']:.1%})")
                
                # Legal Entities Found
                if 'legal_entities' in legal and legal['legal_entities']:
                    st.write("**Legal Entities Identified:**")
                    entities = legal['legal_entities']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if 'case_numbers' in entities:
                            st.write(f"• **Case Numbers:** {', '.join(entities['case_numbers'][:3])}")
                        if 'court_names' in entities:
                            st.write(f"• **Courts:** {', '.join(entities['court_names'][:2])}")
                        if 'judge_names' in entities:
                            st.write(f"• **Judges:** {', '.join(entities['judge_names'][:2])}")
                    
                    with col2:
                        if 'dates' in entities:
                            st.write(f"• **Key Dates:** {', '.join(entities['dates'][:3])}")
                        if 'attorney_names' in entities:
                            st.write(f"• **Attorneys:** {', '.join(entities['attorney_names'][:2])}")
                        if 'deadlines' in entities:
                            st.write(f"• **Deadlines:** {', '.join(entities['deadlines'][:2])}")
                
                # Potential Violations (Critical)
                if 'potential_violations' in legal and legal['potential_violations']:
                    st.error("🚨 **POTENTIAL LEGAL ISSUES DETECTED:**")
                    for violation in legal['potential_violations'][:5]:  # Show top 5
                        severity_color = "🔴" if violation['severity'] == 'high' else "🟡" if violation['severity'] == 'medium' else "🟢"
                        st.write(f"{severity_color} **{violation['type'].title()}**")
                        st.write(f"   Context: {violation['context'][:150]}...")
                
                # Specialized Analysis
                if 'specialized_analysis' in legal and legal['specialized_analysis']:
                    spec = legal['specialized_analysis']
                    if spec.get('case_type') == 'custody':
                        st.write("**👨‍👩‍👧‍👦 Custody Case Analysis:**")
                        if spec.get('key_issues'):
                            st.write(f"• Key Issues: {', '.join(spec['key_issues'])}")
                    elif spec.get('case_type') == 'cps':
                        st.write("**🛡️ CPS Case Analysis:**")
                        if spec.get('allegations'):
                            st.write(f"• Allegations: {', '.join(spec['allegations'])}")
                
                # Procedural Analysis
                if 'procedural_analysis' in legal:
                    proc = legal['procedural_analysis']
                    if not st.session_state.development_mode and 'analysis' in proc:
                        st.write("**⚖️ Procedural Analysis:**")
                        st.write(proc.get('analysis', 'No procedural issues identified'))
                    elif st.session_state.development_mode:
                        st.info("Enable production mode for detailed procedural analysis")
        
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
            
    else:
        st.info("Process a PDF first to start chatting about its contents.")

# Footer
st.markdown("---")
st.markdown("""
⚖️ **Legal Intelligence & Case Analysis Platform - Advanced Features:**

**🔍 Document Intelligence:**
- Automatic classification (custody orders, CPS reports, court motions, ISPs)
- Advanced violation detection with severity scoring
- Constitutional & due process violation identification
- Timeline analysis with gap detection

**📋 Case Management:**
- Multi-document case sessions with persistent storage
- Global search across all case documents (text, pattern, semantic)
- Actor tracking for judges, attorneys, caseworkers
- Contradiction detection across documents

**📊 Analysis & Reporting:**
- Risk assessment with violation heatmaps
- AI-powered legal analysis and brief generation
- Comprehensive case summaries and violation briefings
- Export capabilities for legal use

**🎯 Built For:** Family court cases • Child custody disputes • CPS investigations • DHR proceedings • ISP plans • Legal document analysis

*The watchdog system that courts fear - Uncovering procedural flaws and systemic abuse through intelligent document analysis.*
""")
