import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# -----------------------------------------
# 1. Make our app folder available
# -----------------------------------------

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))


# -----------------------------------------
# 2. Load our calculator
# -----------------------------------------

from app.tools import calculator


# -----------------------------------------
# 3. Load Gemini API key
# -----------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


# -----------------------------------------
# 4. Describe the calculator to Gemini
# -----------------------------------------

calculator_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="calculator",
            description="Perform basic mathematical calculations.",
            parameters={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    },
                    "operation": {
                        "type": "string",
                        "description": (
                            "Operation to perform: "
                            "add, subtract, multiply, or divide"
                        )
                    }
                },
                "required": ["a", "b", "operation"]
            }
        )
    ]
)


# -----------------------------------------
# 5. Ask user a question
# -----------------------------------------

question = input("You: ")


# -----------------------------------------
# 6. Send question + tool description
# -----------------------------------------

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=question,
    config=types.GenerateContentConfig(
        tools=[calculator_tool]
    )
)


# -----------------------------------------
# 7. Inspect Gemini's response
# -----------------------------------------

print("\n--- Gemini response parts ---")

for part in response.candidates[0].content.parts:

    if part.function_call:

        print("\nGemini wants to use a tool!")

        print("Tool name:")
        print(part.function_call.name)

        print("\nArguments:")
        print(part.function_call.args)

    elif part.text:

        print("\nGemini answered directly:")
        print(part.text)