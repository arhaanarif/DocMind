import streamlit as st
from backend.api.api_client import DocMindAPIClient
import base64
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="DocMind - Research Paper Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize API client
@st.cache_resource
def get_api_client():
    return DocMindAPIClient()

api_client = get_api_client()

# Initialize session state
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "selected_document_id" not in st.session_state:
    st.session_state.selected_document_id = None
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "summary_data" not in st.session_state:
    st.session_state.summary_data = None
if "suggested_questions" not in st.session_state:
    st.session_state.suggested_questions = []

# 🎨 Custom CSS - Royal Light Theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styling */
    .main > div {
        padding-top: 1rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        text-align: center;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: rotate(45deg);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .main-header h1 {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        animation: fadeInUp 1s ease-out;
    }
    
    .main-header .subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        font-weight: 300;
        margin-top: 0.5rem;
        opacity: 0.95;
        animation: fadeInUp 1s ease-out 0.3s both;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Navigation Bar */
    .nav-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .nav-container .stRadio > div {
        display: flex;
        justify-content: center;
        gap: 1rem;
    }
    
    .nav-container .stRadio > div > label {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 0.7rem 1.5rem;
        border-radius: 8px;
        border: 2px solid transparent;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;
        color: #475569;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .nav-container .stRadio > div > label:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .nav-container .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Main Container */
    .main-container {
        background: rgba(248, 250, 252, 0.8);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.8);
    }
    
    /* Card Styling */
    .content-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(226, 232, 240, 0.6);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .content-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .content-card h3 {
        color: #1e293b;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        margin-bottom: 1rem;
        font-size: 1.3rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* PDF Viewer Styling */
    .pdf-viewer {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .page-controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 1rem;
        padding: 0.5rem;
        background: #f8fafc;
        border-radius: 8px;
    }
    
    /* Chat Interface */
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 1rem;
        background: #f8fafc;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .chat-message {
        margin-bottom: 1rem;
        animation: fadeIn 0.5s ease-in;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 4px 18px;
        margin-left: 2rem;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: white;
        color: #1e293b;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin-right: 2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Summary Styling */
    .summary-section {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #0ea5e9;
    }
    
    .key-points {
        background: #fefce8;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #eab308;
    }
    
    .suggested-questions {
        background: #f0fdf4;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #22c55e;
    }
    
    .question-button {
        background: white;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        margin: 0.3rem;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-block;
    }
    
    .question-button:hover {
        background: #667eea;
        color: white;
        transform: translateY(-1px);
    }
    
    /* Health Status */
    .health-status {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin-top: 1rem;
        flex-wrap: wrap;
    }
    
    .health-item {
        background: rgba(255, 255, 255, 0.2);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        backdrop-filter: blur(10px);
    }
    
    /* Footer */
    .main-footer {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: white;
        padding: 2rem 1.5rem;
        border-radius: 15px;
        margin-top: 3rem;
        text-align: center;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .main-footer h4 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #f1f5f9;
    }
    
    .main-footer p {
        opacity: 0.9;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    .tech-stack {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .footer-link {
        color: #60a5fa;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.3s ease;
    }
    
    .footer-link:hover {
        color: #93c5fd;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* File Uploader */
    .stFileUploader > div {
        border: 2px dashed #cbd5e1;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        border-color: #667eea;
        background: #f8fafc;
    }
    
    /* Metrics */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        flex: 1;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .nav-container .stRadio > div {
            flex-direction: column;
        }
        
        .health-status {
            flex-direction: column;
            align-items: center;
        }
        
        .user-message, .assistant-message {
            margin-left: 0;
            margin-right: 0;
        }
    }
</style>
""", unsafe_allow_html=True)

# 🔷 1. Header Section
def render_header():
    # Check API health first
    health = api_client.health_check()
    
    st.markdown("""
    <div class="main-header">
        <h1>🧠 DocMind – Research Paper Intelligence</h1>
        <div class="subtitle">Upload, Analyze, Summarize, and Interact with Academic Papers Seamlessly</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Health status display
    if health["success"]:
        status = health["data"]["status"]
        components = health["data"]["components"]
        
        health_html = f"""
        <div class="health-status">
            <div class="health-item">
                <strong>System:</strong> {'🟢 Healthy' if status == 'healthy' else '🔴 Issues'}
            </div>
            <div class="health-item">
                <strong>Database:</strong> {'🟢 Connected' if components['database']['status'] == 'healthy' else '🔴 Error'}
            </div>
            <div class="health-item">
                <strong>Processor:</strong> {'🟢 Ready' if components['pdf_processor']['system_status'] == 'operational' else '🔴 Error'}
            </div>
            <div class="health-item">
                <strong>RAG:</strong> {'🟢 Active' if components['rag_pipeline']['rag_pipeline'] == 'healthy' else '🔴 Error'}
            </div>
        </div>
        """
        st.markdown(health_html, unsafe_allow_html=True)
    else:
        st.error("🔴 **API Unavailable** - Please ensure the backend is running at http://localhost:8000")
        st.stop()

# 🔷 2. Navigation Bar
def render_navigation():
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    nav_options = ["📄 Upload", "📊 Analysis", "🤖 Chatbot"]
    nav_selection = st.radio("", nav_options, horizontal=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    return nav_selection.split(" ", 1)[1]  # Remove emoji

# 🔷 3. Left Column - PDF Viewer
def render_pdf_viewer():
    st.markdown("""
    <div class="content-card">
        <h3>📖 PDF Viewer</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Get documents
    documents_response = api_client.get_documents()
    documents = documents_response.get("data", {}).get("documents", [])
    
    if documents:
        # Document selector
        doc_options = {f"{doc['title']} (ID: {doc['document_id']})": doc["document_id"] for doc in documents}
        selected_doc = st.selectbox("📚 Select Document", list(doc_options.keys()), key="pdf_selector")
        st.session_state.selected_document_id = doc_options[selected_doc]
        
        # PDF Preview (placeholder - replace with actual PDF rendering)
        st.markdown('<div class="pdf-viewer">', unsafe_allow_html=True)
        
        # Try to get PDF preview - if not available, show placeholder
        try:
            preview = api_client.get_pdf_preview(st.session_state.selected_document_id, st.session_state.current_page)
            if preview["success"] and "image" in preview["data"]:
                st.image(
                    base64.b64decode(preview["data"]["image"]), 
                    caption=f"Page {st.session_state.current_page}",
                    use_column_width=True
                )
            else:
                # Fallback placeholder
                st.markdown("""
                <div style="background: #f8fafc; padding: 4rem; text-align: center; border-radius: 8px; border: 2px dashed #cbd5e1;">
                    <h4 style="color: #64748b;">📄 PDF Preview</h4>
                    <p style="color: #94a3b8;">Page {}</p>
                    <small style="color: #cbd5e1;">Preview will appear here when document is processed</small>
                </div>
                """.format(st.session_state.current_page), unsafe_allow_html=True)
        except:
            # Error handling
            st.markdown("""
            <div style="background: #fef2f2; padding: 4rem; text-align: center; border-radius: 8px; border: 2px dashed #fca5a5;">
                <h4 style="color: #dc2626;">⚠️ Preview Unavailable</h4>
                <p style="color: #ef4444;">Unable to load PDF preview</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Page controls
        st.markdown('<div class="page-controls">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Prev", key="prev_page") and st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()
                
        with col2:
            st.markdown(f"<div style='text-align: center; font-weight: 500;'>Page {st.session_state.current_page}</div>", unsafe_allow_html=True)
            
        with col3:
            if st.button("Next ➡️", key="next_page"):
                st.session_state.current_page += 1
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.markdown("""
        <div class="content-card">
            <div style="text-align: center; padding: 2rem; color: #64748b;">
                <h4>📭 No Documents Available</h4>
                <p>Upload a PDF document to get started</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# 🔷 4. Right Column Functions

def render_upload_section():
    st.markdown("""
    <div class="content-card">
        <h3>📄 Upload Document</h3>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file", 
        type=['pdf'], 
        help="Upload a research paper or document for analysis",
        key="file_uploader"
    )
    
    if uploaded_file is not None:
        # File info
        file_size = len(uploaded_file.read())
        uploaded_file.seek(0)  # Reset file pointer
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"📄 **{uploaded_file.name}**\n\n📊 Size: {file_size:,} bytes")
        
        with col2:
            if st.button("🚀 Process Document", type="primary", use_container_width=True):
                with st.spinner("Processing PDF..."):
                    result = api_client.upload_pdf(uploaded_file.read(), uploaded_file.name)
                    
                if result["success"]:
                    st.success("✅ **Document processed successfully!**")
                    
                    # Display result info
                    data = result["data"]
                    st.markdown(f"""
                    <div class="summary-section">
                        <h4>📄 Document Details</h4>
                        <p><strong>Title:</strong> {data.get('document_title', 'N/A')}</p>
                        <p><strong>Document ID:</strong> {data.get('document_id', 'N/A')}</p>
                        <p><strong>Status:</strong> Successfully processed</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Auto-select the uploaded document
                    st.session_state.selected_document_id = data.get('document_id')
                    
                    time.sleep(1)
                    st.rerun()
                    
                else:
                    st.error(f"❌ **Upload failed:** {result['error']}")

def render_analysis_section():
    st.markdown("""
    <div class="content-card">
        <h3>📊 Document Analysis</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Get documents for analysis
    documents_response = api_client.get_documents()
    documents = documents_response.get("data", {}).get("documents", [])
    
    if documents:
        # Document selector for analysis
        doc_options = {f"{doc['title']} (ID: {doc['document_id']})": doc["document_id"] for doc in documents}
        selected_doc = st.selectbox("📚 Select Document for Analysis", list(doc_options.keys()), key="analysis_selector")
        document_id = doc_options[selected_doc]
        
        # Metadata Viewer
        st.markdown("""
        <div class="content-card">
            <h3>📋 Document Metadata</h3>
        </div>
        """, unsafe_allow_html=True)
        
        doc_result = api_client.get_document(document_id)
        if doc_result["success"]:
            doc_data = doc_result["data"]["document"]
            
            # Create metrics display
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 Pages", doc_data.get('page_count', 'N/A'))
            with col2:
                st.metric("🆔 Document ID", document_id)
            with col3:
                st.metric("👥 Authors", "Available" if doc_data.get('authors') else "N/A")
            with col4:
                st.metric("📅 Upload Date", "Recent" if doc_data.get('upload_timestamp') else "N/A")
            
            # Detailed metadata
            st.markdown(f"""
            <div class="summary-section">
                <h4>📄 Document Information</h4>
                <p><strong>Title:</strong> {doc_data.get('title', 'N/A')}</p>
                <p><strong>Authors:</strong> {doc_data.get('authors', 'N/A')}</p>
                <p><strong>File Name:</strong> {doc_data.get('file_name', 'N/A')}</p>
                <p><strong>Pages:</strong> {doc_data.get('page_count', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Summary Generator
        st.markdown("""
        <div class="content-card">
            <h3>📝 AI Summary Generator</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Generate Summary", type="primary", use_container_width=True):
                with st.spinner("Analyzing document..."):
                    summary_result = api_client.summarize_document(document_id)
                    
                if summary_result["success"]:
                    st.session_state.summary_data = summary_result["data"]
                    st.success("✅ Summary generated successfully!")
                else:
                    st.error(f"❌ Summary generation failed: {summary_result['error']}")
        
        # Display summary if available
        if st.session_state.summary_data:
            data = st.session_state.summary_data
            
            # Main summary
            st.markdown(f"""
            <div class="summary-section">
                <h4>📋 Document Summary</h4>
                <p>{data.get('summary', 'No summary available')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Key points
            if data.get('key_points'):
                st.markdown("""
                <div class="key-points">
                    <h4>🔑 Key Points</h4>
                </div>
                """, unsafe_allow_html=True)
                
                for i, point in enumerate(data['key_points'], 1):
                    st.markdown(f"**{i}.** {point}")
            
            # Suggested questions
            if data.get('questions'):
                st.markdown("""
                <div class="suggested-questions">
                    <h4>❓ Suggested Questions</h4>
                </div>
                """, unsafe_allow_html=True)
                
                for i, question in enumerate(data['questions'][:4], 1):
                    if st.button(f"{i}. {question}", key=f"suggest_q_{i}"):
                        # Add question to chat and navigate to chatbot
                        st.session_state.conversation_history.append({
                            "role": "user", 
                            "content": question
                        })
                        st.info(f"Question added to chat: {question}")
    
    else:
        st.markdown("""
        <div class="content-card">
            <div style="text-align: center; padding: 2rem; color: #64748b;">
                <h4>📭 No Documents Available</h4>
                <p>Upload a document first to enable analysis</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_chatbot_section():
    st.markdown("""
    <div class="content-card">
        <h3>🤖 AI Research Assistant</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Document selector for chat
    documents_response = api_client.get_documents()
    documents = documents_response.get("data", {}).get("documents", [])
    
    if documents:
        doc_options = {"🌐 All Documents": None}
        doc_options.update({f"{doc['title']} (ID: {doc['document_id']})": doc["document_id"] for doc in documents})
        
        selected_chat_doc = st.selectbox("📚 Chat Context", list(doc_options.keys()), key="chat_selector")
        chat_document_id = doc_options[selected_chat_doc]
        
        # Chat history display
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        if st.session_state.conversation_history:
            for message in st.session_state.conversation_history:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message">
                        <div class="user-message">
                            <strong>👤 You:</strong> {message['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message">
                        <div class="assistant-message">
                            <strong>🤖 Assistant:</strong> {message['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #64748b;">
                <h4>💬 Start a Conversation</h4>
                <p>Ask questions about your documents below</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat input
        with st.form("chat_form", clear_on_submit=True):
            question = st.text_input(
                "💬 Ask a question about your documents...", 
                placeholder="What is the main contribution of this paper?",
                key="chat_input"
            )
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col2:
                submit = st.form_submit_button("📤 Send", type="primary", use_container_width=True)
            with col3:
                if st.form_submit_button("🗑️ Clear", use_container_width=True):
                    st.session_state.conversation_history = []
                    st.rerun()
        
        if submit and question:
            # Add user message
            st.session_state.conversation_history.append({
                "role": "user",
                "content": question
            })
            
            # Get AI response
            with st.spinner("🤖 AI is thinking..."):
                chat_result = api_client.chat(
                    question=question,
                    document_id=chat_document_id,
                    conversation_history=st.session_state.conversation_history[-10:]  # Last 10 messages
                )
            
            if chat_result["success"]:
                response_data = chat_result["data"]
                
                # Add AI response
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": response_data["answer"]
                })
                
                # Show sources if available
                if response_data.get("sources"):
                    with st.expander("📚 Sources"):
                        for source in response_data["sources"][:3]:  # Show top 3 sources
                            st.markdown(f"""
                            **📄 Document {source.get('document_id', 'N/A')}** - Page {source.get('page_number', 'N/A')}
                            
                            _{source.get('content_preview', 'No preview available')[:200]}..._
                            """)
            else:
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": f"❌ Sorry, I encountered an error: {chat_result['error']}"
                })
            
            st.rerun()
    
    else:
        st.markdown("""
        <div class="content-card">
            <div style="text-align: center; padding: 2rem; color: #64748b;">
                <h4>📭 No Documents Available</h4>
                <p>Upload documents first to start chatting</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# 🔷 5. Footer Section
def render_footer():
    st.markdown("""
    <div class="main-footer">
        <h4>🧠 DocMind - Research Paper Intelligence Tool</h4>
        <p>
            DocMind is an AI-powered platform designed for seamless academic exploration. 
            Upload research papers, extract insights, generate summaries, and interact with documents 
            through an intelligent conversational interface powered by advanced RAG technology.
        </p>
        
        <div class="tech-stack">
            <h5>🔧 Technology Stack</h5>
            <p>
                <strong>Frontend:</strong> Streamlit • 
                <strong>Backend:</strong> FastAPI • 
                <strong>Database:</strong> PostgreSQL • 
                <strong>Vector Store:</strong> ChromaDB • 
                <strong>PDF Processing:</strong> PyMuPDF • 
                <strong>AI:</strong> RAG Pipeline
            </p>
        </div>
        
        <p>
            <strong>Project by Arhaan Arif</strong> | 
            <a href="https://github.com/arhaanarif/docmind" class="footer-link" target="_blank">
                🔗 GitHub Repository
            </a>
        </p>
    </div>
    """, unsafe_allow_html=True)

# 🔷 Main Application
def main():
    # 1. Header
    render_header()
    
    # 2. Navigation
    nav_selection = render_navigation()
    
    # 3. Main Content Area
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Create two-column layout
    col1, col2 = st.columns([0.4, 0.6], gap="large")
    
    # Left Column: PDF Viewer
    with col1:
        render_pdf_viewer()
    
    # Right Column: Content based on navigation
    with col2:
        if nav_selection == "Upload":
            render_upload_section()
        elif nav_selection == "Analysis":
            render_analysis_section()
        elif nav_selection == "Chatbot":
            render_chatbot_section()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 4. Footer
    render_footer()

# Run the application
if __name__ == "__main__":
    main()