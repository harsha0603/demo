import streamlit as st
import pandas as pd
import openai
import os
from dotenv import load_dotenv
from docx import Document
from datetime import datetime

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
if 'company_type' not in st.session_state:
    st.session_state.company_type = None
if 'company_summary' not in st.session_state:
    st.session_state.company_summary = None

# Helper functions
def load_docx(file):
    if file:
        doc = Document(file)
        return "\n".join(para.text for para in doc.paragraphs)
    return None

def generate_summary(text, property_type):
    prompt = f"""
    Generate a concise 3-4 sentence summary of this real estate company document 
    that specializes in {property_type}. Focus on:
    - Company's specialty
    - Key offerings
    - Unique selling points
    
    Document text:
    {text[:3000]}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

def analyze_properties_csv(file):
    if not file:
        return None
    
    df = pd.read_csv(file)
    return {
        "dataframe": df
    }

# Step 1: Company Info Upload
if st.session_state.upload_stage == "company_info":
    st.markdown("### 👋 Welcome! Let's get started.")
    uploaded_file = st.file_uploader("Upload Company Info (DOCX)", type=["docx"])
    
    # Add property type selection
    st.session_state.company_type = st.selectbox(
        "Select property type:",
        options=[
            "Coliving",
            "Residential Property for Rent",
            "Commercial Property for Rent",
            "Residential Property for Resale",
            "Residential Property for Sale by Developer",
            "Commercial Property for Resale",
            "Commercial Property for Sale by Developer"
        ]
    )
    
    if uploaded_file and st.session_state.company_type:
        with st.spinner("Processing company information..."):
            company_text = load_docx(uploaded_file)
            st.session_state.company_data = company_text
            st.session_state.company_summary = generate_summary(company_text, st.session_state.company_type)
            st.session_state.upload_stage = "properties"
            
            st.success("✅ Company info processed!")
            st.markdown("### Company Summary")
            st.write(st.session_state.company_summary)
            st.button("Continue to Property Data Upload")

# Step 2: Properties CSV Upload
if st.session_state.upload_stage == "properties":
    st.markdown("### 🏢 Property Data Upload")
    uploaded_file = st.file_uploader("Upload Properties CSV", type=["csv"])
    
    if uploaded_file:
        with st.spinner("Analyzing property data..."):
            analysis = analyze_properties_csv(uploaded_file)
            st.session_state.properties_data = analysis
            st.success("✅ Property data successfully loaded!")
            st.markdown("Here's a preview of your property data:")
            st.dataframe(analysis["dataframe"].head(5))
            st.session_state.upload_stage = "complete"
            st.button("Start Property Search")

# Chat Interface
if st.session_state.upload_stage == "complete":
    st.divider()
    st.markdown(f"### 🧠 {st.session_state.company_type} Property Search")
    
    # Initialize session state for conversation
    if 'conversation_state' not in st.session_state:
        st.session_state.conversation_state = "initial_questions"
        st.session_state.user_data = {
            "property_type": None,
            "location": None,
            "move_in_date": None,
            "tenancy_duration": None,
            "additional_filters": {}
        }
    
    # Initial 4 questions
    if st.session_state.conversation_state == "initial_questions":
        st.markdown("#### Please answer these 4 key questions:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            property_type = st.selectbox(
                "1. Property Type",
                ["Condo", "HDB", "Landed", "Commercial"],
                key="property_type"
            )
            
            location = st.text_input(
                "2. Preferred Location/Area",
                key="location"
            )
        
        with col2:
            move_in_date = st.date_input(
                "3. Move-in Date",
                min_value=datetime.today(),
                key="move_in_date"
            )
            
            tenancy_duration = st.number_input(
                "4. Tenancy Duration (months)",
                min_value=1,
                max_value=36,
                value=12,
                key="tenancy_duration"
            )
        
        if st.button("Find Properties"):
            st.session_state.user_data.update({
                "property_type": property_type,
                "location": location,
                "move_in_date": str(move_in_date),
                "tenancy_duration": tenancy_duration
            })
            st.session_state.conversation_state = "show_initial_recommendations"
            st.rerun()

    elif st.session_state.conversation_state == "show_initial_recommendations":
        with st.spinner("Finding your ideal properties..."):
            requirements = f"""
            Client Requirements:
            1. Property Type: {st.session_state.user_data["property_type"]}
            2. Location: {st.session_state.user_data["location"]}
            3. Move-in Date: {st.session_state.user_data["move_in_date"]}
            4. Tenancy Duration: {st.session_state.user_data["tenancy_duration"]} months
            """
            
            prompt = f"""
            As a {st.session_state.company_type} specialist, recommend the top 5 properties matching these core requirements:
            {requirements}
            
            Available Properties:
            {st.session_state.properties_data['dataframe'].to_csv()[:10000]}
            
            For each property, include:
            - Property ID/Name
            - Location (distance from requested area)
            - Availability date
            - Lease term options
            - Price range
            - 1-2 sentence highlight
            
            Format as a numbered list with clear spacing between properties.
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            st.markdown("## 🏡 Top 5 Matching Properties")
            st.write(response.choices[0].message.content)
            
            # Add a button to refine search instead of automatically showing refinement options
            if st.button("🔍 Refine Search with More Criteria"):
                st.session_state.conversation_state = "follow_up_questions"
                st.rerun()
            
            if st.button("🔄 Start New Search"):
                st.session_state.conversation_state = "initial_questions"
                st.session_state.user_data = {k: None for k in st.session_state.user_data}
                st.rerun()

    # Follow-up questions (only shown if user clicks "Refine Search")
    elif st.session_state.conversation_state == "follow_up_questions":
        st.markdown("## 🔍 Refine Your Search")
        st.write("Please provide additional preferences to narrow down your options:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            budget = st.number_input(
                "Maximum Budget (SGD)",
                min_value=1000,
                step=500,
                key="budget"
            )
            
            bedrooms = st.number_input(
                "Number of Bedrooms",
                min_value=1,
                max_value=6,
                key="bedrooms"
            )
            
            bathrooms = st.number_input(
                "Number of Bathrooms",
                min_value=1,
                max_value=6,
                key="bathrooms"
            )
        
        with col2:
            amenities = st.multiselect(
                "Must-have Amenities",
                ["Swimming Pool", "Gym", "Parking", "Security", "Pet-Friendly", 
                 "Balcony", "Furnished", "Air Conditioning", "WiFi"],
                key="amenities"
            )
            
            transport = st.text_input(
                "Nearest MRT/Bus Station",
                key="transport"
            )
        
        if st.button("Show Refined Results"):
            st.session_state.user_data["additional_filters"] = {
                "budget": budget,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "amenities": amenities,
                "transport": transport
            }
            st.session_state.conversation_state = "show_refined_recommendations"
            st.rerun()
        
        if st.button("⬅️ Back to Initial Results"):
            st.session_state.conversation_state = "show_initial_recommendations"
            st.rerun()

    # Show refined recommendations
    elif st.session_state.conversation_state == "show_refined_recommendations":
        with st.spinner("Refining your property matches..."):
            full_criteria = f"""
            Core Requirements:
            1. Property Type: {st.session_state.user_data["property_type"]}
            2. Location: {st.session_state.user_data["location"]}
            3. Move-in Date: {st.session_state.user_data["move_in_date"]}
            4. Tenancy Duration: {st.session_state.user_data["tenancy_duration"]} months
            
            Additional Filters:
            - Budget: {st.session_state.user_data["additional_filters"]["budget"]} SGD
            - Bedrooms: {st.session_state.user_data["additional_filters"]["bedrooms"]}
            - Bathrooms: {st.session_state.user_data["additional_filters"]["bathrooms"]}
            - Amenities: {', '.join(st.session_state.user_data["additional_filters"]["amenities"])}
            - Transport: {st.session_state.user_data["additional_filters"]["transport"]}
            """
            
            prompt = f"""
            Based on these refined criteria:
            {full_criteria}
            
            Analyze these properties:
            {st.session_state.properties_data['dataframe'].to_csv()[:10000]}
            
            Provide:
            1. Top 3 best matches with explanation
            2. Price comparison to budget
            3. Amenities score (x/y requested amenities)
            4. Transport accessibility
            5. Any notable compromises
            
            Format clearly with bullet points for each property.
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            st.markdown("## 🎯 Your Best Matches")
            st.write(response.choices[0].message.content)
            
            if st.button("Start New Search"):
                st.session_state.conversation_state = "initial_questions"
                st.session_state.user_data = {k: None for k in st.session_state.user_data}
                st.rerun()