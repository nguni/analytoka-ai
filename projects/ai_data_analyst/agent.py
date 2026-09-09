import os

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

from tools.data_tools import inspect_dataset, analyze_sales


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. "
        "Make sure your .env file contains GEMINI_API_KEY."
    )


# ============================================================
# 2. CREATE GEMINI CLIENT
# ============================================================

client = genai.Client(api_key=api_key)


# ============================================================
# 3. TOOL REGISTRY
# ============================================================

# Gemini uses the names on the left.
# Python executes the functions on the right.

tool_registry = {
    "inspect_dataset": inspect_dataset,
    "analyze_sales": analyze_sales,
}


# ============================================================
# 4. DESCRIBE AVAILABLE TOOLS TO GEMINI
# ============================================================

data_tools = types.Tool(
    function_declarations=[

        # ----------------------------------------------------
        # TOOL 1: INSPECT DATASET
        # ----------------------------------------------------

        types.FunctionDeclaration(
            name="inspect_dataset",
            description=(
                "Inspect a CSV or Excel dataset. "
                "Use this tool when you need to understand the "
                "dataset structure, including rows, columns, "
                "column names, data types, and missing values."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "Path to the CSV or Excel dataset."
                        ),
                    }
                },
                "required": ["file_path"],
            },
        ),

        # ----------------------------------------------------
        # TOOL 2: ANALYZE SALES
        # ----------------------------------------------------

        types.FunctionDeclaration(
            name="analyze_sales",
            description=(
                "Analyze a sales dataset and calculate sales metrics. "
                "Returns total revenue, total quantity, revenue by "
                "product, and revenue by region."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "Path to the sales CSV or Excel dataset."
                        ),
                    }
                },
                "required": ["file_path"],
            },
        ),
    ]
)


# ============================================================
# 5. MAIN AGENT FUNCTION
# ============================================================

def run_agent(question: str, file_path: str) -> str:
    """
    Run the AI Data Analyst Agent.

    The agent:
    - receives a question
    - decides which tool to use
    - executes the tool
    - observes the result
    - can use another tool
    - returns a final answer
    """

    # --------------------------------------------------------
    # 6. CREATE AGENT PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are an AI Data Analyst Agent.

Your job is to help the user understand and analyze a dataset.

The dataset available to you is located at:

{file_path}

You have access to tools that can inspect and analyze the dataset.

Instructions:

- Use the available tools whenever you need information from the dataset.
- Never invent numbers or dataset information.
- Base your conclusions on the results returned by the tools.
- You may use multiple tools when necessary.
- Use inspect_dataset when you need information about rows,
  columns, data types, or missing values.
- Use analyze_sales when you need information about sales,
  revenue, products, quantities, or regional performance.
- After receiving a tool result, decide whether another tool
  is necessary.
- When you have enough information, answer the user's question.
- Keep your final answer clear and business-friendly.

User question:

{question}
"""

    # --------------------------------------------------------
    # 7. CREATE WORKING MEMORY
    # --------------------------------------------------------

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part(
                    text=prompt
                )
            ]
        )
    ]


    # --------------------------------------------------------
    # 8. AGENT LOOP
    # --------------------------------------------------------

    max_steps = 10

    for step in range(max_steps):

        print(f"\n--- Agent step {step + 1} ---")


        # ----------------------------------------------------
        # 9. ASK GEMINI WHAT TO DO NEXT
        # ----------------------------------------------------

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=[data_tools]
                ),
            )

        except errors.ClientError as error:

            # Handle Gemini quota / rate-limit error
            if error.code == 429:
                return (
                    "Gemini API quota has been reached. "
                    "Please wait and try again later."
                )

            # Handle other Gemini client errors
            return f"Gemini API error: {error}"

        except Exception as error:

            # Catch unexpected API/network errors
            return f"Unexpected error while contacting Gemini: {error}"


        # ----------------------------------------------------
        # 10. VALIDATE GEMINI RESPONSE
        # ----------------------------------------------------

        if not response.candidates:
            return "Gemini did not return a valid response."


        model_content = response.candidates[0].content


        if model_content is None:
            return "Gemini returned an empty response."


        # ----------------------------------------------------
        # 11. ADD GEMINI RESPONSE TO WORKING MEMORY
        # ----------------------------------------------------

        contents.append(model_content)


        # ----------------------------------------------------
        # 12. LOOK FOR A TOOL CALL
        # ----------------------------------------------------

        function_call = None

        if model_content.parts:

            for part in model_content.parts:

                if part.function_call:
                    function_call = part.function_call
                    break


        # ----------------------------------------------------
        # 13. NO TOOL CALL = FINAL ANSWER
        # ----------------------------------------------------

        if function_call is None:

            print("Agent has finished.")

            if response.text:
                return response.text

            return (
                "The agent finished but did not return "
                "a text response."
            )


        # ----------------------------------------------------
        # 14. GET TOOL NAME AND ARGUMENTS
        # ----------------------------------------------------

        tool_name = function_call.name
        arguments = dict(function_call.args)

        print("Agent selected tool:", tool_name)
        print("Arguments:", arguments)


        # ----------------------------------------------------
        # 15. FIND TOOL IN REGISTRY
        # ----------------------------------------------------

        tool_function = tool_registry.get(tool_name)


        # ----------------------------------------------------
        # 16. HANDLE UNKNOWN TOOL
        # ----------------------------------------------------

        if tool_function is None:

            error_result = {
                "error": f"Unknown tool requested: {tool_name}"
            }

            print(error_result["error"])


            tool_response = types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=tool_name,
                        response=error_result,
                    )
                ],
            )


            contents.append(tool_response)

            continue


        # ----------------------------------------------------
        # 17. EXECUTE THE TOOL
        # ----------------------------------------------------

        try:

            result = tool_function(**arguments)

            print("Tool result:", result)


        except Exception as error:

            result = {
                "error": str(error)
            }

            print("Tool error:", error)


        # ----------------------------------------------------
        # 18. SEND TOOL RESULT BACK TO GEMINI
        # ----------------------------------------------------

        tool_response = types.Content(
            role="user",
            parts=[
                types.Part.from_function_response(
                    name=tool_name,
                    response={
                        "result": result
                    },
                )
            ],
        )


        # ----------------------------------------------------
        # 19. ADD TOOL RESULT TO WORKING MEMORY
        # ----------------------------------------------------

        contents.append(tool_response)


        # The loop now starts again.
        #
        # Gemini will receive:
        #
        # User question
        #       +
        # Gemini tool request
        #       +
        # Tool result
        #
        # Gemini can then:
        #
        # 1. request another tool
        #
        # OR
        #
        # 2. return the final answer


    # --------------------------------------------------------
    # 20. SAFETY STOP
    # --------------------------------------------------------

    return (
        "The agent stopped because it reached the "
        "maximum number of reasoning steps."
    )