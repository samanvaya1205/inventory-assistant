from getpass import getpass

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from tools import login, make_read_tools, make_write_tools

load_dotenv()

SYSTEM_PROMPT = """You are an inventory assistant for a small electronics store.
Answer questions using the tools, never from memory or guesswork.
Only call the tools you have been given. Never invent a tool or write a tool call as text.
To change or delete an item, first find its id with list_items.
Prices are in Indian rupees.
If a tool returns 403, tell the user they don't have permission to do that.
If a tool returns any other error, tell the user plainly what went wrong.
If a tool succeeds, confirm what was done.
Keep answers short."""

username = input("username: ")
password = getpass("password: ")
token = login(username, password)

agent = create_agent(
    model=ChatOllama(model="llama3.1:8b", temperature=0),
    tools=make_read_tools(token) + make_write_tools(token),
    system_prompt=SYSTEM_PROMPT,
)

print("ask about the inventory. type 'quit' to exit. \n")
messages = []
while True:
    question = input("you: ").strip()
    if question.lower() in ("quit", "exit"):
        break
    messages.append({"role": "user", "content": question})
    result = agent.invoke({"messages": messages})

    for m in result["messages"][len(messages):]:
        for call in getattr(m, "tool_calls", None) or []:
            print(f" [tool] {call['name']}({call['args']})")

            messages = result["messages"]
            print("agent:", messages[-1].text, "\n")