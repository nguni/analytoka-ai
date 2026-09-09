import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# -----------------------------------------
# 1. Add project root to Python path
# -----------------------------------------

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))


# -----------------------------------------
# 2. Import our calculator
# -----------------------------------------

from app.tools import calculator


# -----------------------------------------
# 3. Load Gemini API key
# -----------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


# -----------------------------------------
# 4. Define the calculator tool
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
# 5. Ask the user
# -----------------------------------------

question = input("You: ")


# -----------------------------------------
# 6. Send question to Gemini
# -----------------------------------------

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=question,
    config=types.GenerateContentConfig(
        tools=[calculator_tool]
    )
)


# -----------------------------------------
# 7. Check if Gemini requested a tool
# -----------------------------------------

for part in response.candidates[0].content.parts:

    if part.function_call:

        tool_name = part.function_call.name
        arguments = part.function_call.args

        print("\nGemini selected tool:", tool_name)
        print("Arguments:", arguments)


        # ---------------------------------
        # 8. Execute the tool
        # ---------------------------------

        if tool_name == "calculator":

            result = calculator(
                a=arguments["a"],
                b=arguments["b"],
                operation=arguments["operation"]
            )

            print("Tool result:", result)


            # ---------------------------------
            # 9. Send tool result back to Gemini
            # ---------------------------------

            final_response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(
                                text=question
                            )
                        ]
                    ),

                    response.candidates[0].content,

                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=tool_name,
                                response={
                                    "result": result
                                }
                            )
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    tools=[calculator_tool]
                )
            )

            print("\nAI:", final_response.text)

    elif part.text:

        print("\nAI:", part.text)