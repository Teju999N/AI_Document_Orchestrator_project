# AI_Document_Orchestrator_project
AI Resume Orchestrator An AI-powered system that automates resume screening, candidate evaluation, and communication using Streamlit, Groq API, and n8n workflows.

Overview The AI Resume Orchestrator simplifies the recruitment process by: Analyzing resumes using AI Generating match scores based on job descriptions Automatically shortlisting candidates Triggering email workflows for recruiters and candidates.

Features
1. Upload resumes (PDF / TXT)
2. AI-based resume analysis
3. Match score generation
4. Automatic shortlisting decision
5. Email automation using n8n
6. Recruiter notification (for shortlisted candidates)
7. Candidate feedback with improvement suggestions (for rejected candidates)
8. Real-time workflow execution via webhooks

Architecture Streamlit App → Groq AI Model → Decision Logic → n8n Webhook → Email Automation
How It Works
1. User uploads a resume and provides a job description
2. Resume text is extracted and sent to the AI model
3. AI returns structured output: Candidate name Match score, Skills analysis Final decision Based on the score: ≥ 70 → Shortlisted → Recruiter notified < 70 → Rejected → Candidate gets feedback + suggestions
4. n8n workflow automates email communication

Tech Stack Frontend: Streamlit Backend: Python AI Model: Groq (LLaMA 3) Automation: n8n Libraries: pdfplumber, requests, json, re
Setup Instructions 1️. Clone Repository git clone https://github.com/your-username/ai-resume-orchestrator.git cd ai-resume-orchestrator 2. Install Dependencies pip install -r requirements.txt 3️. Configure Secrets Create .streamlit/secrets.toml:
GROQ_API_KEY = "your_groq_api_key" N8N_WEBHOOK_URL = "your_n8n_webhook_url" 4️. Run the App streamlit run app.py

n8n Workflow Setup
1. Create a Webhook node
2. Add IF condition based on score/type
3. Configure: Recruiter email (shortlisted) Candidate feedback email (rejected)
4. Add "Respond to Webhook" node
5. Activate workflow

Demo Flow Upload Resume → Analyze → View Score → Send Email → Workflow Triggered
Use Cases Automated resume screening HR workflow automation Candidate evaluation systems AI-based recruitment tools
Impact Reduces manual screening effort Improves consistency in hiring decisions Enhances candidate experience with feedback Enables scalable recruitment workflows
Future Enhancements Dashboard for analytics Resume ranking system Bulk candidate processing Integration with job portals
