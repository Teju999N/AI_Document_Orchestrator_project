import streamlit as st
import pdfplumber
import requests
import json
from google import genai

# Load secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]

client = genai.Client(api_key=GEMINI_API_KEY)

st.title("📄 AI Resume Screening Orchestrator")

# ---------- FILE UPLOAD ---------- #
uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "txt"])

def extract_text(file):
    if file.type == "application/pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    else:
        return file.read().decode("utf-8")

# ---------- JOB DESCRIPTION ---------- #
job_desc = st.text_input("Ask me a question")

if uploaded_file and job_desc:
    resume_text = extract_text(uploaded_file)

    st.subheader("🔍 Analyzing Resume...")

    prompt = f"""
    You are an AI resume analyzer.

    Analyze the resume according to user question.

    Resume:
    {resume_text[:3000]}

    Job Description:
    {job_desc[:1500]}

    Return STRICT JSON:

    {{
      "candidate_name": "",
      "match_score": 0,
      "matched_skills": [],
      "missing_skills": [],
      "experience_relevance": "",
      "shortlist_category": "",
      "reason": ""
    }}

    Rules:
    - score >= 70 → Shortlisted
    - score < 70 → Not Shortlisted
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    try:
        data = json.loads(response.text)
        st.success("✅ Analysis Complete")

        st.json(data)

        # ---------- SHORTLIST DISPLAY ---------- #
        score = int(data.get("match_score", 0))

        st.subheader("📊 Shortlisting Result")

        if score >= 70:
            st.success("Shortlisted")
        else:
            st.error("Not Shortlisted")

    except:
        st.error("❌ JSON parsing failed")
        data = {"error": response.text}

    # ---------- EMAIL SECTION ---------- #
    st.subheader("📧 Notify Recruiter")

    recruiter_email = st.text_input("Recruiter Email")

    if st.button("Send Decision Email"):

        payload = {
            "analysis": data,
            "email": recruiter_email
        }

        res = requests.post(N8N_WEBHOOK_URL, json=payload)

        if res.status_code == 200:
            result = res.json()

            st.subheader("🧠 Final Summary")
            st.write(result.get("final_answer"))

            st.subheader("✉ Email Content")
            st.write(result.get("email_body"))

            st.subheader("📢 Status")
            st.success(result.get("status"))

        else:
            st.error("❌ n8n connection failed")
