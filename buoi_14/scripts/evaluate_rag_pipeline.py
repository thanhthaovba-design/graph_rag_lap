import os
import json
import pandas as pd
import random
from dotenv import load_dotenv
from openai import OpenAI

# Load env variables
load_dotenv()

from langchain_openai import ChatOpenAI
from datasets import Dataset
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from secure_retriever import SecureDenseRetriever

def generate_qa_dataset(chunks_df, client, num_questions=20):
    print("Generating Golden Dataset...")
    # Select chunks
    sample_chunks = chunks_df.sample(n=min(num_questions, len(chunks_df)), random_state=42)
    
    dataset_records = []
    
    for i, row in sample_chunks.iterrows():
        context = row['text']
        
        # Generate question and ground truth
        prompt = f"""Given the following context, generate a single specific question that can be answered entirely from it, and provide the ground truth answer.
Context: {context}

Return ONLY a JSON object with exactly two keys: 'question' and 'ground_truth'. Do not output any markdown formatting, just raw valid JSON. Example: {{"question": "What is X?", "ground_truth": "X is Y."}}"""
        
        try:
            completion = client.chat.completions.create(
                model="Qwen/Qwen3.5-9B:deepinfra",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            response_text = completion.choices[0].message.content.strip()
            
            # Clean formatting if any
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            # Sometimes model outputs text before or after json
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                response_text = response_text[start_idx:end_idx+1]
                
            qa_pair = json.loads(response_text)
            
            difficulty = random.choice(["easy", "medium", "hard"])
            
            if "question" in qa_pair and "ground_truth" in qa_pair:
                dataset_records.append({
                    "question": qa_pair["question"],
                    "ground_truth": qa_pair["ground_truth"],
                    "context_used": context,
                    "difficulty": difficulty
                })
            else:
                print(f"Skipping chunk {i} due to missing keys in JSON.")
        except Exception as e:
            print(f"Error generating QA for chunk {i}: {e}")
            continue
            
    df_eval = pd.DataFrame(dataset_records)
    eval_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'eval')
    os.makedirs(eval_dir, exist_ok=True)
    df_eval.to_csv(os.path.join(eval_dir, 'qa_dataset.csv'), index=False)
    print(f"Generated {len(df_eval)} questions.")
    return df_eval

def run_rag_pipeline(df_eval, client, retriever):
    print("Running RAG Pipeline...")
    results = []
    
    user_roles = ["Admin", "HR", "Risk_Manager", "Staff"]
    
    for _, row in df_eval.iterrows():
        question = row['question']
        ground_truth = row['ground_truth']
        
        # Retrieve
        retrieved_docs = retriever.retrieve(question, user_roles, top_k=3)
        contexts = [doc['text'] for doc in retrieved_docs]
        
        # Generate Answer
        context_str = "\n\n".join(contexts)
        prompt = f"""Answer the question based ONLY on the following context. Do not use outside knowledge. Answer concisely and accurately.
Context:
{context_str}

Question: {question}

Answer:"""
        
        try:
            completion = client.chat.completions.create(
                model="Qwen/Qwen3.5-9B:deepinfra",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            answer = completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating answer: {e}")
            answer = ""
            
        results.append({
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": ground_truth
        })
        
    return pd.DataFrame(results)

def run_ragas_evaluation(df_results, judger_llm):
    print("Running Ragas Evaluation...")
    
    # Ragas needs a dataset with specific column names
    dataset = Dataset.from_pandas(df_results)
    
    # Configure Embeddings
    embeddings = HuggingFaceEmbeddings(model_name="keepitreal/vietnamese-sbert")
    
    # Run evaluation
    metrics = [
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
    ]
    
    # Set the llm for each metric
    for metric in metrics:
        metric.llm = judger_llm
        
    result = evaluate(
        dataset,
        metrics=metrics,
        llm=judger_llm,
        embeddings=embeddings
    )
    
    result_df = result.to_pandas()
    
    eval_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'eval')
    result_df.to_csv(os.path.join(eval_dir, 'evaluation_results.csv'), index=False)
    
    return result_df, result

def generate_report(result_df, metrics_result):
    print("Generating Evaluation Report...")
    
    report_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'ragas_evaluation_report.md')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    # Calculate averages
    avg_scores = {
        "Context Precision": result_df['context_precision'].mean(),
        "Context Recall": result_df['context_recall'].mean(),
        "Faithfulness": result_df['faithfulness'].mean(),
        "Answer Relevancy": result_df['answer_relevancy'].mean()
    }
    
    # Find low scoring questions (average score < 0.7)
    result_df['avg_score'] = result_df[['context_precision', 'context_recall', 'faithfulness', 'answer_relevancy']].mean(axis=1)
    low_scores = result_df[result_df['avg_score'] < 0.7]
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Ragas Evaluation Report\n\n")
        f.write("## Summary Metrics\n\n")
        f.write("| Metric | Average Score |\n")
        f.write("|---|---|\n")
        for k, v in avg_scores.items():
            f.write(f"| {k} | {v:.4f} |\n")
            
        f.write("\n## Analysis of Low Scoring Questions (Score < 0.7)\n\n")
        if len(low_scores) == 0:
            f.write("No questions scored below 0.7 on average. Excellent performance!\n")
        else:
            for i, row in low_scores.iterrows():
                f.write(f"### Question: {row['question']}\n")
                f.write(f"- **Avg Score:** {row['avg_score']:.4f}\n")
                f.write(f"- **Context Precision:** {row['context_precision']:.4f}\n")
                f.write(f"- **Context Recall:** {row['context_recall']:.4f}\n")
                f.write(f"- **Faithfulness:** {row['faithfulness']:.4f}\n")
                f.write(f"- **Answer Relevancy:** {row['answer_relevancy']:.4f}\n")
                f.write(f"- **Generated Answer:** {row['answer']}\n")
                f.write(f"- **Ground Truth:** {row['ground_truth']}\n\n")
                f.write(f"**Error Analysis & Proposed Optimization:**\n")
                if row['context_precision'] < 0.7 or row['context_recall'] < 0.7:
                    f.write("- **Retrieval Issue:** The retriever is not fetching the relevant contexts effectively. Consider tuning top_k, using hybrid search, or improving chunking strategies.\n")
                if row['faithfulness'] < 0.7:
                    f.write("- **Hallucination Issue:** The model generated information not present in the context. Try to strictly instruct the LLM to only use provided context or reduce temperature.\n")
                if row['answer_relevancy'] < 0.7:
                    f.write("- **Relevance Issue:** The answer doesn't directly address the question. Prompt engineering might be needed to make the LLM focus on the exact question asked.\n")
                f.write("\n---\n\n")
                
        f.write("\n## General System Optimization Proposals\n")
        f.write("1. **Implement Hybrid Retriever**: Combine Dense and BM25 retrieval (SecureHybridRetriever) for better context recall.\n")
        f.write("2. **Prompt Engineering**: Refine the QA prompt to strictly prohibit reasoning outside the provided context to improve Faithfulness.\n")
        f.write("3. **Embedding Fine-Tuning**: If domain-specific vocabulary is heavily used, fine-tune the embedding model.\n")
        
    print(f"Report saved to {report_path}")
    
    return avg_scores, report_path

def main():
    print("Starting Evaluation Pipeline with Hugging Face Router API...")
    
    # Check if HF_TOKEN is available
    api_key = os.environ.get("HF_TOKEN", "")
    if not api_key:
        print("Error: HF_TOKEN is not set.")
        return
        
    # Initialize OpenAI Client (using HF Router API Base URL)
    client = OpenAI(
        api_key=api_key,
        base_url="https://router.huggingface.co/v1"
    )
    
    # Initialize LangChain Judger LLM (using HF Router API Base URL)
    # Using the exact models specified in the lab instructions
    judger_llm = ChatOpenAI(
        model="openai/gpt-oss-20b:deepinfra",
        api_key=api_key,
        base_url="https://router.huggingface.co/v1",
        temperature=0.0
    )
    
    # 1. Generate Dataset
    chunks_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'chunks_secure.csv')
    chunks_df = pd.read_csv(chunks_path)
    
    df_eval = generate_qa_dataset(chunks_df, client, num_questions=20)
    
    if len(df_eval) == 0:
        print("No questions were generated. Exiting.")
        return
        
    # 2. Run RAG Pipeline
    retriever = SecureDenseRetriever(corpus_path=chunks_path)
    df_results = run_rag_pipeline(df_eval, client, retriever)
    
    # 3. Run Ragas Evaluation
    df_scored, metrics_result = run_ragas_evaluation(df_results, judger_llm)
    
    # 4. Generate Report
    avg_scores, report_path = generate_report(df_scored, metrics_result)
    
    print("\n" + "="*50)
    print("FINAL RESULTS - AVERAGE SCORES")
    print("="*50)
    for k, v in avg_scores.items():
        print(f"{k}: {v:.4f}")
        
    print("\n" + "="*50)
    print("REPORT PREVIEW")
    print("="*50)
    with open(report_path, 'r', encoding='utf-8') as f:
        print(f.read()[:1000] + "\n...\n(Report truncated for display)")

if __name__ == "__main__":
    main()

