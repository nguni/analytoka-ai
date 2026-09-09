import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Import our calculator tool
from app.tools import calculator

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Create Gemini client
client = genai.Client(api_key=api_key)

# Ask the user a question
question = input("You: ")

# Send the question to Gemini
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=question,
    config={
        "tools": [calculator]
    }
)

print("\nAI:", response.text)