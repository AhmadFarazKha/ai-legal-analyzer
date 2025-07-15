import google.generativeai as genai
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
import io

load_dotenv()

# --- Initialize Gemini API ---
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file. Please set it.")
    genai.configure(api_key=gemini_api_key)
    print("Gemini API configured successfully.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to configure Gemini API. Ensure GEMINI_API_KEY is correct in .env. Details: {e}")
    gemini_api_key = None 

# Use a suitable Gemini model for text analysis
text_model = genai.GenerativeModel('gemini-1.5-flash') 

# --- Document Reading Functions ---
def read_text_from_pdf(file_stream: io.BytesIO) -> str:
    """Extracts text from a PDF file stream."""
    reader = PdfReader(file_stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def read_text_from_docx(file_stream: io.BytesIO) -> str:
    """Extracts text from a DOCX file stream."""
    document = Document(file_stream)
    text = ""
    for para in document.paragraphs:
        text += para.text + "\n"
    return text

def read_text_from_txt(file_stream: io.BytesIO) -> str:
    """Reads text from a plain text file stream."""
    return file_stream.getvalue().decode('utf-8')

# --- AI Analysis Function ---
def analyze_legal_document(document_text: str) -> dict:
    """
    Analyzes legal document text to provide summary, key clauses, and risks in both English and Urdu using Gemini.
    """
    if not gemini_api_key:
        raise ValueError("Gemini API Key is not configured. Cannot analyze document.")
    if not document_text.strip():
        return {"error": "No text extracted from document for analysis.", "english_report": "", "urdu_report": ""}

    # Limit input length to avoid API token limits, adjust as needed based on Gemini's token limits and cost
    # 15000 characters is a rough estimate; actual tokens depend on content.
    truncated_text = document_text[:15000]

    prompt = f"""
    You are an expert AI Legal Document Analyzer. Your task is to review a legal document and provide a concise summary, extract key clauses, and identify potential risks.

    **VERY IMPORTANT:** Provide the full report in **BOTH English and Urdu**. Clearly label each language section.

    Here is the legal document for analysis:
    ---
    {truncated_text}
    ---

    Please provide the analysis in the following structured format:

    ---
    **English Report:**

    ### 1. Overall Legal Summary:
    [Provide a concise, 3-5 sentence summary of the document's main purpose, parties, and key agreements.]

    ### 2. Key Clauses Identified:
    [List 3-5 of the most important clauses (e.g., Termination, Indemnification, Governing Law, Payment Terms, Scope of Work). For each, provide the clause name and a brief summary of its content from the document.]
    - **[Clause Name 1]:** [Brief summary of content from document]
    - **[Clause Name 2]:** [Brief summary of content from document]
    ...

    ### 3. Potential Risks/Red Flags:
    [Identify any clauses or terms that could pose a significant risk, ambiguity, or unusual burden for one of the parties. Explain why it's a risk.]
    - **[Risk 1]:** [Explanation of why it's a risk and where it's located in the document (e.g., "Ambiguous termination clause in Section 5.2").]
    - **[Risk 2]:** [Explanation of why it's a risk.]
    ...

    If no significant risks are identified, state "No major risks identified based on the provided text."

    ---
    **اردو رپورٹ (Urdu Report):**

    ### 1. قانونی خلاصہ (Overall Legal Summary):
    [دستاویز کا 3-5 جملوں پر مشتمل مختصر خلاصہ فراہم کریں جس میں اس کا بنیادی مقصد، فریقین اور اہم معاہدات بیان کیے گئے ہوں۔]

    ### 2. کلیدی شقوں کی نشاندہی (Key Clauses Identified):
    [3-5 اہم ترین شقوں کی فہرست دیں (مثلاً، معاہدے کا اختتام، ہرجانے کا ضامن ہونا، نافذ العمل قانون، ادائیگی کی شرائط، کام کا دائرہ کار)۔ ہر ایک کے لیے، شق کا نام اور دستاویز سے اس کے مواد کا مختصر خلاصہ فراہم کریں۔]
    - **[شق کا نام 1]:** [دستاویز سے مواد کا مختصر خلاصہ]
    - **[شق کا نام 2]:** [دستاویز سے مواد کا مختصر خلاصہ]
    ...

    ### 3. ممکنہ خطرات/ریڈ فلیگز (Potential Risks/Red Flags):
    [ایسی شقوں یا شرائط کی نشاندہی کریں جو کسی فریق کے لیے نمایاں خطرہ، ابہام، یا غیر معمولی بوجھ بن سکتی ہیں۔ وضاحت کریں کہ یہ خطرہ کیوں ہے۔]
    - **[خطرہ 1]:** [خطرہ کی وضاحت اور دستاویز میں اس کا مقام (مثلاً، "سیکشن 5.2 میں مبہم اختتامی شق")۔]
    - **[خطرہ 2]:** [خطرہ کی وضاحت۔]
    ...

    اگر کوئی نمایاں خطرات نہیں پائے جاتے ہیں، تو بیان کریں "فراہم کردہ متن کی بنیاد پر کوئی بڑے خطرات کی نشاندہی نہیں ہوئی۔"
    ---
    """

    try:
        response = text_model.generate_content(prompt)
        full_report_text = response.text

        # Basic splitting into English and Urdu sections based on markers
        english_section_tag = "**English Report:**"
        urdu_section_tag = "**اردو رپورٹ (Urdu Report):**"

        english_report = ""
        urdu_report = ""

        if english_section_tag in full_report_text and urdu_section_tag in full_report_text:
            english_part = full_report_text.split(english_section_tag, 1)[1].split(urdu_section_tag, 1)[0].strip()
            urdu_part = full_report_text.split(urdu_section_tag, 1)[1].strip()
            english_report = english_part
            urdu_report = urdu_part
        else:
            # Fallback if splitting tags aren't found as expected
            print(f"Warning: Could not parse English/Urdu sections. Full AI output: {full_report_text[:500]}...")
            english_report = "--- Could not neatly separate English and Urdu reports. Full AI output below: ---\n\n" + full_report_text
            urdu_report = "" # No separate Urdu if cannot split neatly

        return {"english_report": english_report, "urdu_report": urdu_report}

    except Exception as e:
        error_msg = str(e).lower()
        if "quota" in error_msg or "rate limit" in error_msg:
            raise Exception("API Error: You might have hit a rate limit or quota. Please try again later.")
        if "authentication" in error_msg or "api key" in error_msg or "unauthorized" in error_msg:
            raise Exception("API Error: Invalid or missing API Key. Double-check .env file or deployment secrets.")
        if "content_filter" in error_msg or "safety" in error_msg:
            raise Exception("API Error: Content may violate safety guidelines. Please rephrase or use a different document.")
        if "tokens" in error_msg and "exceeded" in error_msg:
            raise Exception("API Error: Document is too long for analysis (token limit exceeded). Try a shorter document.")
        raise Exception(f"An unexpected error occurred during AI analysis: {e}. Please try again.")

# Example Usage (for testing - typically run via app.py)
if __name__ == "__main__":
    print("This module defines the core document analysis logic.")
    print("It also contains functions to read text from PDF, DOCX, and TXT files.")
    print("To test, you should run app.py.")