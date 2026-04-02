import streamlit as st
import pdfplumber
import requests
import json
from google import genai

# Load secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]

# Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

st.title("📄 AI Document Orchestrator")

# ---------------- FILE UPLOAD ---------------- #
uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])

def extract_text(file):
    if file.type == "application/pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    else:
        return file.read().decode("utf-8")

# ---------------- USER QUERY ---------------- #
query = st.text_input("Ask your question about the document")

# ---------------- GEMINI EXTRACTION ---------------- #
if uploaded_file and query:
    text = extract_text(uploaded_file)

    st.subheader("📊 Extracting Structured Data...")

    prompt = f"""
    You are an AI data extractor.

    Given the document and user query, extract 5-8 most relevant key-value pairs.

    Return STRICT JSON ONLY.

    Document:
    {text[:8000]}

    Question:
    {query}

    Output format:
    {{
      "key1": "value1",
      "key2": "value2",
      "risk_level": "Low/Medium/High"
    }}
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    try:
        extracted_json = json.loads(response.text)
        st.success("✅ Structured Data Extracted")
        st.json(extracted_json)

    except:
        st.error("❌ JSON parsing failed")
        extracted_json = {"error": response.text}

    # ---------------- EMAIL SECTION ---------------- #
    st.subheader("📧 Email Automation")

    email = st.text_input("Recipient Email ID")

    if st.button("Send Alert Mail"):

        payload = {
            "document_text": text[:5000],
            "question": query,
            "extracted_data": extracted_json,
            "email": email
        }

        res = requests.post(N8N_WEBHOOK_URL, json=payload)

        if res.status_code == 200:
            data = res.json()

            st.subheader("🧠 Final Analytical Answer")
            st.write(data.get("final_answer", "No response"))

            st.subheader("✉ Generated Email Body")
            st.write(data.get("email_body", "No email sent"))

            st.subheader("📢 Email Status")
            st.success(data.get("status", "Unknown"))

        else:
            st.error("❌ Failed to connect to n8n")
