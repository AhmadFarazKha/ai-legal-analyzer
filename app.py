import streamlit as st
import os
from src.core.document_processor import analyze_legal_document, read_text_from_pdf, read_text_from_docx, read_text_from_txt
from src.utils.file_handler import create_directories_if_not_exist
from dotenv import load_dotenv
import io

create_directories_if_not_exist("data")

load_dotenv()

# --- Streamlit Session State Initialization ---
if 'uploaded_file_bytes' not in st.session_state:
    st.session_state.uploaded_file_bytes = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = ""
if 'analysis_report' not in st.session_state:
    st.session_state.analysis_report = None
if 'show_report' not in st.session_state:
    st.session_state.show_report = False

# --- Page Configuration (Theme controlled by .streamlit/config.toml) ---
st.set_page_config(
    page_title="AI Legal Document Analyzer",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- NO CUSTOM CSS IN THIS VERSION ---
# This version removes all custom CSS from app.py to guarantee no CSS code appears on the page.
# Styling will rely solely on .streamlit/config.toml

# --- Application Content ---
st.title("⚖️ AI Legal Document Analyzer")
st.markdown("<p style='text-align: center; font-size: 1.1rem; margin-bottom: 2rem;'>Upload your legal documents (TXT, PDF, DOCX) for AI-powered summary, clause extraction, and risk identification in both English and Urdu.</p>", unsafe_allow_html=True)

col_main_l, col_main_center, col_main_r = st.columns([1, 4, 1])

with col_main_center:
    with st.container(border=True): # Streamlit native border
        st.markdown("### 1. Upload Your Legal Document")
        uploaded_file = st.file_uploader(
            "Choose a document file (.txt, .pdf, .docx)",
            type=["txt", "pdf", "docx"],
            key="document_uploader"
        )

        document_text = ""
        if uploaded_file is not None:
            st.session_state.uploaded_file_bytes = uploaded_file.getvalue()
            st.session_state.file_name = uploaded_file.name
            st.session_state.analysis_report = None
            st.session_state.show_report = False

            file_extension = st.session_state.file_name.split('.')[-1].lower()
            try:
                if file_extension == "txt":
                    document_text = read_text_from_txt(io.BytesIO(st.session_state.uploaded_file_bytes))
                elif file_extension == "pdf":
                    document_text = read_text_from_pdf(io.BytesIO(st.session_state.uploaded_file_bytes))
                elif file_extension == "docx":
                    document_text = read_text_from_docx(io.BytesIO(st.session_state.uploaded_file_bytes))
                else:
                    st.error("Unsupported file type. Please upload .txt, .pdf, or .docx.")
                    st.stop()
                
                if not document_text.strip():
                    st.warning("Could not extract text from the document. It might be scanned or protected.")
                    st.stop()

                st.success(f"Successfully extracted text from '{st.session_state.file_name}'!")
                st.info(f"First 200 characters of extracted text:\n\n{document_text[:200]}...")

            except Exception as e:
                st.error(f"Error reading document: {e}. Ensure it's not corrupted or protected.")
                st.session_state.uploaded_file_bytes = None
                st.stop()
        elif st.session_state.uploaded_file_bytes is not None:
            file_extension = st.session_state.file_name.split('.')[-1].lower()
            try:
                if file_extension == "txt":
                    document_text = read_text_from_txt(io.BytesIO(st.session_state.uploaded_file_bytes))
                elif file_extension == "pdf":
                    document_text = read_text_from_pdf(io.BytesIO(st.session_state.uploaded_file_bytes))
                elif file_extension == "docx":
                    document_text = read_text_from_docx(io.BytesIO(st.session_state.uploaded_file_bytes))
                if not document_text.strip():
                    st.warning("Text could not be re-extracted from the document on rerun.")
            except Exception:
                pass

        if not document_text.strip() and st.session_state.uploaded_file_bytes is None:
             st.info("Please upload a legal document to get started.")


    st.markdown("---")

    col_btn_analyze, col_btn_clear = st.columns(2)
    with col_btn_analyze:
        if st.button("Analyze Document with AI 🧠", use_container_width=True, key="btn_analyze_doc"):
            if document_text.strip():
                with st.spinner("AI is analyzing your legal document... This may take a moment for long documents."):
                    try:
                        analysis_output = analyze_legal_document(document_text)
                        st.session_state.analysis_report = analysis_output
                        st.session_state.show_report = True
                        st.success("Document analysis complete!")
                    except Exception as e:
                        st.error(f"Error during AI analysis: {e}. Ensure your API key is correct and document content is appropriate.")
                        st.session_state.show_report = False
            else:
                st.warning("Please upload a document AND ensure text is extracted before analyzing.")
                st.session_state.show_report = False

    with col_btn_clear:
        if st.button("Clear All 🗑️", use_container_width=True, key="btn_clear_all"):
            st.session_state.uploaded_file_bytes = None
            st.session_state.file_name = ""
            st.session_state.analysis_report = None
            st.session_state.show_report = False
            st.info("All cleared! Ready for a new document.")
            st.rerun()

# Display Analysis Result
if st.session_state.show_report and st.session_state.analysis_report:
    with col_main_center:
        with st.container(border=True): # Streamlit native border
            tab_english, tab_urdu = st.tabs(["English Report", "اردو رپورٹ"])

            with tab_english:
                st.markdown("### 💡 AI Analysis Report (English):")
                st.markdown(st.session_state.analysis_report["english_report"])

                st.download_button(
                    label="Download English Report ⬇️",
                    data=st.session_state.analysis_report["english_report"].encode('utf-8'),
                    file_name=f"{st.session_state.file_name.replace('.', '_')}_english_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="btn_download_english_report"
                )
            
            with tab_urdu:
                st.markdown("### 💡 قانونی تجزیہ رپورٹ (اردو):")
                st.markdown(st.session_state.analysis_report["urdu_report"])

                st.download_button(
                    label="اردو رپورٹ ڈاؤن لوڈ کریں ⬇️",
                    data=st.session_state.analysis_report["urdu_report"].encode('utf-8'),
                    file_name=f"{st.session_state.file_name.replace('.', '_')}_urdu_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="btn_download_urdu_report"
                )
        
st.markdown("---")
st.info("Powered by Google Gemini AI and Streamlit.")
st.markdown("<p style='text-align: center; font-size: 0.9rem; color: #a0a0a0; margin-top: 2rem;'>Developed with ❤️ in Mianwali, Punjab, Pakistan</p>", unsafe_allow_html=True)