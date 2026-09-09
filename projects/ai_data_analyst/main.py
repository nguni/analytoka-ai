#from agent import run_agent

from agent_groq import run_agent


file_path = "projects/ai_data_analyst/data/sample_sales.csv"


print("AI Data Analyst Agent")
print("Type 'exit' to stop.\n")


while True:

    question = input("You: ")

    if question.lower() == "exit":
        print("Goodbye!")
        break

    answer = run_agent(
        question=question,
        file_path=file_path
    )

    print("\nAI:", answer)
    print()