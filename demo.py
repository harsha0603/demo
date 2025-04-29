import streamlit as st
import pandas as pd
import openai
import os
from dotenv import load_dotenv
from docx import Document

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# App config
st.set_page_config(page_title="AI Real Estate Agent", layout="wide")
st.title("🏘️ AI Real Estate Agent")

# Initialize session state
if 'upload_stage' not in st.session_state:
    st.session_state.upload_stage = "company_info"
if 'company_data' not in st.session_state:
    st.session_state.company_data = None
if 'properties_data' not in st.session_state:
    st.session_state.properties_data = None

# Helper functions
def load_docx(file):
    if file:
        doc = Document(file)
        return "\n".join(para.text for para in doc.paragraphs)
    return None

def summarize_text(text, max_length=2000):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user", 
            "content": f"Summarize this in {max_length} characters or less:\n{text}"
        }],
        temperature=0.3
    )
    return response.choices[0].message.content

def analyze_properties_csv(file):
    if not file:
        return None
    
    df = pd.read_csv(file)
    csv_str = df.to_csv(index=False)[:5000]  # Limit CSV size
    
    prompt = f"""
    Analyze this properties CSV data (first 5k chars). Identify:
    1. Column names and their purpose
    2. Data quality issues
    3. Structure summary
    
    Data:
    {csv_str}
    
    Respond in this format:
    - Columns: [list]
    - Issues: [list]
    - Structure: [summary]
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    return {
        "data": csv_str,
        "analysis": response.choices[0].message.content,
        "dataframe": df
    }

# Step 1: Company Info Upload
if st.session_state.upload_stage == "company_info":
    st.markdown("### 👋 Welcome! Let's get started.")
    uploaded_file = st.file_uploader("Upload Company Info (DOCX)", type=["docx"])
    
    if uploaded_file:
        with st.spinner("Processing..."):
            company_text = load_docx(uploaded_file)[:3000]  # Limit to 3000 chars
            st.session_state.company_data = summarize_text(company_text)  # Pre-summarize
            st.session_state.upload_stage = "properties"
            st.success("✅ Company info processed!")
            st.write(st.session_state.company_data)
            st.button("Continue")

# Step 2: Properties CSV Upload
if st.session_state.upload_stage == "properties":
    st.markdown("### 🏢 Property Data Upload")
    uploaded_file = st.file_uploader("Upload Properties CSV", type=["csv"])
    
    if uploaded_file:
        with st.spinner("Analyzing..."):
            analysis = analyze_properties_csv(uploaded_file)
            st.session_state.properties_data = analysis
            st.success("✅ Done!")
            st.write(analysis["analysis"])
            st.dataframe(analysis["dataframe"].head())
            st.session_state.upload_stage = "complete"
            st.button("Start Chatting")

# Chat Interface
if st.session_state.upload_stage == "complete":
    st.divider()
    user_input = st.text_input("Ask about properties:")
    
    if user_input:
        with st.spinner("Thinking..."):
            system_prompt = f"""
            You are a real estate AI. Use this data:
            Company: {st.session_state.company_data[:1000]}
            Properties: {st.session_state.properties_data['analysis'][:2000]}
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.6
            )
            st.write(response.choices[0].message.content)