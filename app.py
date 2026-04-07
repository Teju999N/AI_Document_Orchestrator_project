import streamlit as st
import pdfplumber
import requests
import json
from groq import Groq
import re

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
# from google import genai
# Load secrets
# GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GROQ_API_KEY=st.secrets["GROQ_API_KEY"]
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]

# client = genai.Client(api_key=GEMINI_API_KEY)

st.title("📄 AI Resume Orchestrator")

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

# ---------- ✅ RESUME VALIDATION ---------- #
def is_resume(text):
    text_lower = text.lower()
    sections = ["education", "experience", "skills", "projects"]
    
    identity = ["email", "phone", "contact", "linkedin", "github"]

    # Count matches
    section_score = sum(1 for s in sections if s in text_lower)
    identity_score = sum(1 for i in identity if i in text_lower)

    # Extra check: length (resume is usually structured, not too long essay)
    word_count = len(text.split())

    # Final logic
    if section_score >= 2 and identity_score >= 1 and word_count < 3000:
        return True

    return False
    
# ---------- EMAIL EXTRACTION ---------- #
def extract_email(text):
    pattern = r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+"
    match = re.search(pattern, text)
    return match.group(0) if match else None
    
# ---------- JOB DESCRIPTION ---------- #
job_desc = st.text_input("Ask me a question")

if uploaded_file and job_desc:
    resume_text = extract_text(uploaded_file)
    #  VALIDATE BEFORE AI
    if not is_resume(resume_text):
        st.error("❌ Please upload a resume only")
        st.stop()

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
    response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0
    )


    try:
        output = response.choices[0].message.content
    
        # Extract only JSON part
        clean_output = re.search(r'\{.*\}', output, re.DOTALL).group()
    
        data = json.loads(clean_output)
    
        st.success("✅ Analysis Complete")
        st.subheader("📄 Candidate Summary")

        st.write(f"👤 Name: {data.get('candidate_name', 'N/A')}")
        st.write(f"📊 Match Score: {data.get('match_score', 0)}")
        
        st.write("✅ Matched Skills:")
        st.write(", ".join(data.get("matched_skills", [])) or "None")
        
        st.write("❌ Missing Skills:")
        st.write(", ".join(data.get("missing_skills", [])) or "None")
        
        st.write(f"💼 Experience Relevance: {data.get('experience_relevance', '')}")
        
        st.write(f"📌 Decision: {data.get('shortlist_category', '')}")
        
        st.write(f"📝 Reason: {data.get('reason', '')}")
          # st.json(data)
    
        # ---------- SHORTLIST DISPLAY ---------- #
        score = int(data.get("match_score", 0))
    
        st.subheader("📊 Shortlisting Result")
    
        if score >= 70:
            st.success("Shortlisted")
        else:
            st.error("Not Shortlisted")
    
    except Exception as e:
        st.error("❌ JSON parsing failed")
        st.write(output)  # shows actual model output (VERY USEFUL)
        data = {}

    def send_to_n8n(payload):
        try:
            res = requests.post(N8N_WEBHOOK_URL, json=payload)
    
            if res.status_code != 200:
                st.error(f"❌ Error: {res.status_code}")
                st.write(res.text)
                return
    
            try:
                result = res.json()
    
                st.subheader("📢 Status")
                st.success(result.get("Status"))
    
            except:
                st.error("❌ Invalid JSON from n8n")
                st.write(res.text)

        except Exception as e:
            st.error("❌ n8n connection failed")
            st.write(str(e))
  
    # ---------- EMAIL SECTION ---------- #
    
    candidate_email = extract_email(resume_text)
    
    # ✅ CASE 1: SHORTLISTED
    if score >= 70:
    
        recruiter_email = st.text_input("Recruiter Email")
    
        if st.button("Send Selection Email"):
    
            payload = {
                "analysis": data,
                "score": score,
                "candidate_email": candidate_email,
                "recruiter_email": recruiter_email,
                "type": "selected"   # 🔥 helpful in n8n
            }
    
            send_to_n8n(payload)
    
    # ❌ CASE 2: NOT SHORTLISTED
    else:
        if candidate_email:
            st.success(f"📧 Candidate Email: {candidate_email}")
        else:
            candidate_email = st.text_input("Enter Candidate Email")
    
        if st.button("Send Feedback Email"):
    
            payload = {
                "analysis": data,
                "score": score,
                "candidate_email": candidate_email,
                "type": "rejected"   # 🔥 helpful in n8n
            }
    
            send_to_n8n(payload)
