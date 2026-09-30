"""Inventory assistant as an explicit LangGraph graph, with human approval before any write."""
from getpass import getpass
from typing import Literal

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from tools import login, make_read_tools, make_write_tools

SYSTEM_PROMPT = """You are an inventory assistant for a small electronics store.
Answer questions using the tools, never from memory or guesswork.
Only call the tools you have been given. Never invent a tool or write a tool call as text.
Use the exact argument names from the tool definitions: item_id, not id.
To change or delete an item, first find its id with list_items.
If more than one item matches what the user described, do not pick one. List every match with its id, price and category, and ask the user which one they mean.
Write actions need the user's approval. If the user rejects an action, do not retry it; say it was cancelled.
Prices are in Indian rupees.
If a tool returns 403, tell the user they don't have permission to do that.
If a tool returns any other error, tell the user plainly what went wrong.
If a tool succeeds, confirm what was done.
Keep answers short."""

WRITE_TOOLS = {"create_item", "update_item", "delete_item", "create_category", "create_tag"}

username = input("username: ")
password = getpass("password: ")
token = login(username, password)

tools = make_read_tools(token) + make_write_tools(token)
TOOLS_BY_NAME = {t.name: t for t in tools}
llm = ChatOllama(model="qwen2.5:7b", temperature=0).bind_tools(tools)


def describe(call):
    """Turn a tool call into a line a human can check, with the item's details if it has an item_id."""
    text = f"{call['name']}({call['args']})"
    item_id = call["args"].get("item_id")
    if item_id is None:
        return text
    try:
        item = TOOLS_BY_NAME["get_item"].invoke({"item_id": item_id})
    except Exception:
        return text + "  -> could not look up this item"
    if "error" in item:
        return text + f"  -> item {item_id} not found"
    stock = "in stock" if item["in_stock"] else "out of stock"
    added = item["created_at"][:16].replace("T", " ")
    return text + f"  -> {item['name']}, Rs. {item['price']}, {item['category']}, {stock}, added {added}"


def call_model(state: MessagesState):
    """Ask the LLM what to do next."""
    response = llm.invoke([SystemMessage(SYSTEM_PROMPT)] + state["messages"])
    return {"messages": [response]}


def route(state: MessagesState):
    """After the model: finish, run read tools directly, or ask for approval first."""
    last = state["messages"][-1]
    if not last.tool_calls:
        return END
    if any(call["name"] in WRITE_TOOLS for call in last.tool_calls):
        return "approve"
    return "tools"


def approve(state: MessagesState) -> Command[Literal["tools", "model"]]:
    """Pause the graph and wait for a human yes/no before any write."""
    last = state["messages"][-1]
    pending = [describe(c) for c in last.tool_calls if c["name"] in WRITE_TOOLS]
    answer = interrupt(pending)
    if answer == "y":
        return Command(goto="tools")
    rejected = [
        ToolMessage(content="The user rejected this action. Do not retry it.", tool_call_id=c["id"])
        for c in last.tool_calls
    ]
    return Command(goto="model", update={"messages": rejected})


graph = StateGraph(MessagesState)
graph.add_node("model", call_model)
graph.add_node("approve", approve)
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "model")
graph.add_conditional_edges("model", route, ["approve", "tools", END])
graph.add_edge("tools", "model")
app = graph.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "session-1"}, "recursion_limit": 10}

print("ask about the inventory. type 'quit' to exit.\n")
while True:
    question = input("you: ").strip()
    if question.lower() in ("quit", "exit"):
        break

    seen = len(app.get_state(config).values.get("messages", []))
    result = app.invoke({"messages": [{"role": "user", "content": question}]}, config)

    while "__interrupt__" in result:
        for action in result["__interrupt__"][0].value:
            print(f"  [approval needed] {action}")
        answer = input("  approve? (y/n): ").strip().lower()
        result = app.invoke(Command(resume=answer), config)

    for m in result["messages"][seen:]:
        for call in getattr(m, "tool_calls", None) or []:
            print(f"  [tool] {call['name']}({call['args']})")
        if m.type == "tool":
            print(f"  [result] {m.content[:200]}")

    print("agent:", result["messages"][-1].text, "\n")