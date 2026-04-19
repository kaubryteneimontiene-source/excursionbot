from langchain_community.callbacks import get_openai_callback
from cache import get_cached_response, save_cached_response
import os
from logger import log_query, log_error, log_session_start
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from rag.retriever import get_retriever
from tools.budget import calculate_group_budget
from tools.weather import suggest_activities
from tools.flight import build_itinerary
from tools.wikipedia_tool import search_site_wikipedia
from prompts import get_system_prompt

load_dotenv()

# ---- LANGSMITH TRACING ----
# Add to your .env:
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your_langsmith_key
# LANGCHAIN_PROJECT=ExcursionBot
os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "false"))
os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGCHAIN_PROJECT", "ExcursionBot"))


def create_agent():
    """Create the excursion assistant agent."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    tools = [
        calculate_group_budget,
        suggest_activities,
        build_itinerary,
        search_site_wikipedia,
    ]

    agent = create_react_agent(
        model=llm,
        tools=tools,
    )

    return agent


def get_context(query: str, retriever) -> tuple[str, list, list]:
    """Retrieve relevant context, source filenames and raw chunks."""
    try:
        docs = retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in docs])
        chunks = [doc.page_content for doc in docs]

        sources = []
        for doc in docs:
            source = doc.metadata.get("source", "")
            filename = source.replace("\\", "/").split("/")[-1]
            name = filename.replace(".txt", "").replace("_", " ").title()
            if name and name not in sources:
                sources.append(name)

        return context, sources, chunks
    except Exception as e:
        print(f"Retrieval error: {e}")
        return "No additional context available.", [], []


# Global instances (created once, reused)
retriever = None
agent_executor = None


def initialize():
    """Initialize the agent and retriever."""
    global retriever, agent_executor
    print("Initializing ExcursionBot...")
    retriever = get_retriever()
    agent_executor = create_agent()
    log_session_start()
    print("ExcursionBot ready!")


def reload_retriever_after_upload():
    """Reload retriever after new document uploaded."""
    global retriever
    retriever = get_retriever()
    print("Retriever reloaded after upload!")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def _invoke_agent_with_retry(agent_exec, messages: list) -> dict:
    """Invoke agent with automatic retry on failure (max 3 attempts)."""
    return agent_exec.invoke({"messages": messages})


def chat(user_message: str, chat_history: list, language: str = "English") -> tuple[str, int, int, list, list, list]:
    """
    Main chat function.
    Returns:
        tuple of (response_text, prompt_tokens, completion_tokens, sources, tools_used, chunks)
    """
    global retriever, agent_executor

    if not retriever or not agent_executor:
        initialize()

    conversational_phrases = [
        "yes", "no", "ok", "okay", "thanks", "thank you", "hello",
        "hi", "hey", "bye", "goodbye", "great", "cool", "awesome",
        "sure", "nope", "yep", "got it", "nice", "perfect", "good",
        "wow", "interesting", "really", "oh", "i see", "understood",
        "help", "start", "begin", "what can you do", "who are you"
    ]

    is_conversational = (
        user_message.strip().lower() in conversational_phrases
        or len(user_message.strip()) < 15
    )

    if not is_conversational:
        cached = get_cached_response(user_message)
        if cached:
            print(f"Cache hit for: {user_message[:50]}")
            return (
                cached["response"], 0, 0,
                cached["sources"],
                cached["tools_used"],
                cached["chunks"]
            )

    if is_conversational:
        context = "No context needed - this is a conversational message."
        sources = []
        chunks = []
    else:
        context, sources, chunks = get_context(user_message, retriever)

    full_message = (
        f"{user_message}\n\n"
        f"[Background context from knowledge base - use only if relevant]:\n"
        f"{context}"
    )

    messages = [SystemMessage(content=get_system_prompt(language))]

    for message in chat_history:
        if message["role"] == "user":
            messages.append(HumanMessage(content=message["content"]))
        elif message["role"] == "assistant":
            messages.append(AIMessage(content=message["content"]))

    messages.append(HumanMessage(content=full_message))

    try:
        with get_openai_callback() as cb:
            result = _invoke_agent_with_retry(agent_executor, messages)
            prompt_tokens = cb.prompt_tokens
            completion_tokens = cb.completion_tokens

        tools_used = []
        for message in result["messages"]:
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    tools_used.append({
                        "name": tool_call["name"],
                        "args": tool_call["args"]
                    })

        response = result["messages"][-1].content
        log_query(user_message, response, sources, 0)

        if not is_conversational:
            save_cached_response(
                user_message, response, sources, tools_used, chunks
            )

        return response, prompt_tokens, completion_tokens, sources, tools_used, chunks

    except Exception as e:
        error_msg = (
            "⚠️ Sorry, I ran into an issue after 3 attempts. "
            "Please try again or rephrase your question."
        )
        log_error(str(e), context=user_message)
        return error_msg, 0, 0, [], [], []
