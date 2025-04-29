import unittest
from agents.onboarding_agent import OnboardingAgent

class TestOnboarding(unittest.TestCase):
    def test_info_extraction(self):
        agent = OnboardingAgent()
        response = agent.extract_info("We're LuxHomes, selling luxury homes in Miami")
        self.assertIn("luxury", response["chatbot_style"])