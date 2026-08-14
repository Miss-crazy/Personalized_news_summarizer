"""
evaluation/ragas_eval.py
RAGAS evaluation module for Personalized News Summarizer.
Evaluates RAG performance across standard metrics:
- Faithfulness: Grounding of answer in retrieved context
- Answer Relevance: Relevance of answer to question
- Context Precision: Signal-to-noise ratio in retrieved cluster summaries
- Context Recall: Extent to which retrieved context covers ground truth
"""

import os
import json
import logging
from typing import List, Dict, Any

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevance,
    context_precision,
    context_recall,
)
from langchain_community.llms import Ollama
from langchain_community.embeddings import HuggingFaceEmbeddings

from rag.chain import ask, personalised_ask
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL, EMBEDDING_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample benchmark dataset for news summarizer QA
BENCHMARK_TESTSET: List[Dict[str, Any]] = [
    {
        "question": "What are the latest developments in artificial intelligence and technology regulation?",
        "ground_truth": "Governments and tech organizations are discussing AI regulatory frameworks, safety guidelines, and computational infrastructure investments."
    },
    {
        "question": "What is happening in recent space exploration and NASA missions?",
        "ground_truth": "NASA and international space programs are conducting new planetary exploration, rover operations, and astronomical observations."
    },
    {
        "question": "What are the top recent updates in business and market economy?",
        "ground_truth": "Central banks and market analysts are monitoring inflation rates, interest policy shifts, and quarterly corporate earnings."
    }
]


def prepare_evaluation_dataset(testset: List[Dict[str, Any]], user_id: str = None) -> Dataset:
    """
    Run RAG pipeline on test questions and format output into HuggingFace Dataset
    matching Ragas schema (question, answer, contexts, ground_truth).
    """
    questions = []
    answers = []
    contexts = []
    ground_truths = []

    for item in testset:
        query = item["question"]
        gt = item["ground_truth"]

        logger.info("Evaluating query: '%s'", query)
        if user_id:
            result = personalised_ask(query, user_id=user_id)
        else:
            result = ask(query)

        # Extract context summaries from retrieved sources
        retrieved_contexts = [
            f"{s.get('label', '')}: {s.get('summary', '')}" 
            for s in result.sources
        ] if result.sources else ["No relevant news context retrieved."]

        questions.append(query)
        answers.append(result.answer)
        contexts.append(retrieved_contexts)
        ground_truths.append(gt)

    data_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }

    return Dataset.from_dict(data_dict)


def run_ragas_evaluation(user_id: str = None, output_file: str = "evaluation_report.json"):
    """
    Run Ragas evaluation using local Ollama LLM and SentenceTransformer embeddings.
    """
    logger.info("Preparing RAGAS dataset...")
    eval_dataset = prepare_evaluation_dataset(BENCHMARK_TESTSET, user_id=user_id)

    # Initialize local evaluator LLM and embedding model
    evaluator_llm = Ollama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=0.0
    )
    evaluator_embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    metrics = [
        faithfulness,
        answer_relevance,
        context_precision,
        context_recall,
    ]

    logger.info("Running Ragas evaluation across %d metrics...", len(metrics))
    results = evaluate(
        dataset=eval_dataset,
        metrics=metrics,
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )

    df = results.to_pandas()
    print("\n" + "=" * 50)
    print(" 📊 RAGAS EVALUATION METRICS REPORT")
    print("=" * 50)
    print(df[["question", "faithfulness", "answer_relevance", "context_precision", "context_recall"]])
    print("=" * 50)

    # Export report to JSON
    summary_scores = {k: float(v) for k, v in results.items() if isinstance(v, (int, float))}
    report_data = {
        "summary_scores": summary_scores,
        "details": df.to_dict(orient="records")
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    logger.info("Evaluation report saved to %s", output_file)
    return report_data


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Ragas evaluation on Personalized News Summarizer")
    parser.add_argument("--user", type=str, default=None, help="Optional user ID for personalized RAG evaluation")
    parser.add_argument("--output", type=str, default="evaluation_report.json", help="Output file path for JSON report")
    args = parser.parse_args()

    run_ragas_evaluation(user_id=args.user, output_file=args.output)
