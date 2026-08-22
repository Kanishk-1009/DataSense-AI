"""
M6 Evaluation Framework
=======================
Provides a controlled experiment harness that compares the single-agent
pipeline (M4, 1 LLM call) against the multi-agent pipeline (M5, 7 LLM calls)
on identical EDA input.

Public API
----------
>>> from backend.evaluation.evaluator import run_evaluation
>>> result = run_evaluation(eda_result, dataset_name="titanic", model="llama3.1:8b")
>>> print(result.model_dump_json(indent=2))
"""
