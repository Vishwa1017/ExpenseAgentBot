from langchain.agents import create_agent
from dotenv import load_dotenv
from backend.services.db.analytics_queries import get_monthly_summary, get_category_breakdown, get_top_merchants



load_dotenv()  

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

SQLagent = create_agent(
    model="openai:gpt-5.4",
    tools=[get_weather, get_monthly_summary, get_category_breakdown, get_top_merchants],
    system_prompt="You are a helpful assistant who can provide insights on financial transactions and also answer general questions like weather.",
)

# result = SQLagent.invoke(   
#     {"messages": [{"role": "user", "content": "How much did I spend on groceries in February 2026?"}]}
# )
# print(result["messages"][-1].content_blocks)


while True:
    user_input = input("Ask a question (or 'exit' to quit): ")
    if user_input.lower() == "exit":
        break

    result = SQLagent.invoke({"messages": [{"role": "user", "content": user_input}]})
    print(result["messages"][-1].content_blocks)