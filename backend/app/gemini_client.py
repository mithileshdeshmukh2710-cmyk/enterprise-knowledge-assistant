import os

from dotenv import load_dotenv
from google import genai


# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)


class GeminiClient:

    def __init__(self):

        if not API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is missing from .env"
            )

        self.client = genai.Client(
            api_key=API_KEY
        )

        self.model = MODEL_NAME

    def generate_answer(self, prompt):

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response"
            )

        return response.text