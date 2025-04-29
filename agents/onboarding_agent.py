# agents/onboarding_agent.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

class OnboardingAgent:
    def __init__(self):
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
        self.llm = ChatOpenAI(
            model="gpt-4",
            openai_api_key=api_key,
            temperature=0.7
        )
        
        self.prompt = ChatPromptTemplate.from_template("""
            Extract company details from this conversation:
            {input}
            
            Return JSON with:
            - name (str)
            - business_type (residential/commercial/both)
            - chatbot_style (professional/friendly/luxury)
            - missing_info (list of unclear fields)
        """)
    
    def extract_info(self, user_input: str) -> dict:
        chain = self.prompt | self.llm
        response = chain.invoke({"input": user_input})
        return json.loads(response.content)