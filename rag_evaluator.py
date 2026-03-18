import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()


def evaluate_rag_response(
    question: str,
    context_chunks: list,
    answer: str
) -> dict:
    """
    Evaluate RAG response quality using LLM-based scoring.

    Metrics:
    - context_relevance: Are the retrieved chunks relevant to the question?
    - answer_faithfulness: Is the answer based on the context?
    - answer_relevance: Does the answer actually address the question?

    Returns dict with scores (0-1) and explanation.
    """
    if not context_chunks or not answer:
        return {
            "context_relevance": 0.0,
            "answer_faithfulness": 0.0,
            "answer_relevance": 0.0,
            "overall": 0.0,
            "explanation": "No context or answer to evaluate."
        }

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    context_text = "\n\n".join(context_chunks[:3])

    eval_prompt = f"""You are evaluating a RAG (Retrieval Augmented Generation) system.

QUESTION: {question}

RETRIEVED CONTEXT:
{context_text}

GENERATED ANSWER:
{answer}

Please evaluate on these 3 metrics and respond ONLY in this exact format:
CONTEXT_RELEVANCE: [score 0.0-1.0] | [one sentence explanation]
ANSWER_FAITHFULNESS: [score 0.0-1.0] | [one sentence explanation]
ANSWER_RELEVANCE: [score 0.0-1.0] | [one sentence explanation]

Scoring guide:
- CONTEXT_RELEVANCE: How relevant are the retrieved chunks to the question? (1.0 = perfectly relevant)
- ANSWER_FAITHFULNESS: Is the answer grounded in the context without hallucination? (1.0 = fully grounded)
- ANSWER_RELEVANCE: Does the answer directly address the question asked? (1.0 = perfectly addresses it)
"""

    try:
        result = llm.invoke([HumanMessage(content=eval_prompt)])
        response_text = result.content

        scores = {}
        explanations = {}

        for line in response_text.strip().split("\n"):
            if "CONTEXT_RELEVANCE:" in line:
                parts = line.split("|")
                score_part = parts[0].replace("CONTEXT_RELEVANCE:", "").strip()
                scores["context_relevance"] = float(score_part)
                explanations["context_relevance"] = parts[1].strip() if len(parts) > 1 else ""
            elif "ANSWER_FAITHFULNESS:" in line:
                parts = line.split("|")
                score_part = parts[0].replace("ANSWER_FAITHFULNESS:", "").strip()
                scores["answer_faithfulness"] = float(score_part)
                explanations["answer_faithfulness"] = parts[1].strip() if len(parts) > 1 else ""
            elif "ANSWER_RELEVANCE:" in line:
                parts = line.split("|")
                score_part = parts[0].replace("ANSWER_RELEVANCE:", "").strip()
                scores["answer_relevance"] = float(score_part)
                explanations["answer_relevance"] = parts[1].strip() if len(parts) > 1 else ""

        overall = sum(scores.values()) / len(scores) if scores else 0.0

        return {
            "context_relevance": scores.get("context_relevance", 0.0),
            "answer_faithfulness": scores.get("answer_faithfulness", 0.0),
            "answer_relevance": scores.get("answer_relevance", 0.0),
            "overall": round(overall, 2),
            "explanations": explanations
        }

    except Exception as e:
        print(f"Evaluation error: {e}")
        return {
            "context_relevance": 0.0,
            "answer_faithfulness": 0.0,
            "answer_relevance": 0.0,
            "overall": 0.0,
            "explanation": f"Evaluation failed: {str(e)}"
        }


def format_score_emoji(score: float) -> str:
    """Convert score to emoji indicator."""
    if score >= 0.8:
        return "🟢"
    elif score >= 0.6:
        return "🟡"
    else:
        return "🔴"