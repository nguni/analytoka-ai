import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required to run the Gemini chat.")

    client = genai.Client(api_key=api_key)
    chat = client.chats.create(model="gemini-3.6-flash")

    print("AI Agent Chat")
    print("Type 'exit' to stop.\n")

    while True:
        question = input("You: ")

        if question.lower() == "exit":
            break

        response = chat.send_message(message=question)
        print("AI:", response.text)
        print()


if __name__ == "__main__":
    main()