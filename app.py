import streamlit as st
from agents.onboarding_agent import OnboardingAgent
from utils.file_processor import process_docx, process_csv
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment and init AI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize session state
if 'stage' not in st.session_state:
    st.session_state.stage = "company_upload"
    st.session_state.company_acknowledged = False
    st.session_state.properties_acknowledged = False

# --- STAGE 1: Company Upload ---
if st.session_state.stage == "company_upload":
    st.title("🏢 Welcome to Your AI Real Estate Assistant")
    company_file = st.file_uploader("Upload your company profile (DOCX)", type=["docx"])

    if company_file:
        with st.spinner("Analyzing your company profile..."):
            company_text = process_docx(company_file)
            
            # AI-generated acknowledgment
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Create a warm acknowledgment highlighting 1-2 unique details from the company profile."},
                    {"role": "user", "content": f"Company profile excerpt: {company_text[:2000]}"}
                ]
            )
            
            st.session_state.company_text = company_text
            st.session_state.stage = "properties_upload"
            st.success(response.choices[0].message.content)
            st.button("Next: Upload Properties")

# --- STAGE 2: Properties Upload ---
elif st.session_state.stage == "properties_upload":
    st.title("📊 Now, Add Your Properties")
    properties_file = st.file_uploader("Upload property data (CSV)", type=["csv"])

    if properties_file:
        with st.spinner("Crunching your property numbers..."):
            properties_data = process_csv(properties_file)
            
            # AI-generated property summary
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Summarize key stats: property count, price range, and one unique insight."},
                    {"role": "user", "content": f"Property data sample: {properties_data[:2000]}"}
                ]
            )
            
            st.session_state.properties_data = properties_data
            st.session_state.stage = "generate_profile"
            st.success("✅ Data received!")
            st.markdown(f"**Property Snapshot:**\n\n{response.choices[0].message.content}")
            st.button("Generate My Company Profile")

# --- STAGE 3: AI-Generated Profile ---
elif st.session_state.stage == "generate_profile":
    st.title("🎉 Your AI-Powered Profile")
    with st.spinner("Creating your custom profile..."):
        # Combine data into a professional profile
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Create a structured company profile with: 1) Overview, 2) Property Highlights, 3) Unique Selling Points."},
                {"role": "user", "content": f"""
                    Company: {st.session_state.company_text[:3000]}
                    Properties: {st.session_state.properties_data[:3000]}
                """}
            ]
        )
        
        st.balloons()
        st.markdown(f"## 🏡 Custom Company Profile\n\n{response.choices[0].message.content}")
        st.download_button("Download Profile", response.choices[0].message.content, file_name="company_profile.md")

# --- STAGE 4: Edit & Preview ---
elif st.session_state.stage == "generate_profile":
    # Generate and store the profile first
    with st.spinner("Creating your custom profile..."):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Create a structured company profile..."},
                {"role": "user", "content": f"""
                    Company: {st.session_state.company_text[:3000]}
                    Properties: {st.session_state.properties_data[:3000]}
                """}
            ]
        )
        generated_profile = response.choices[0].message.content
        st.session_state.final_profile = generated_profile  # Store in session state

    # Display profile
    st.balloons()
    st.markdown(f"## 🏡 Custom Company Profile")
    st.write(st.session_state.final_profile)

    # --- EDIT MODE ---
    st.subheader("✏️ Edit Your Profile")
    edited_profile = st.text_area(
        "Make adjustments:",
        value=st.session_state.final_profile,  # Now using the stored profile
        height=300
    )

    if st.button("Save Changes"):
        st.session_state.final_profile = edited_profile
        st.success("Profile updated!")