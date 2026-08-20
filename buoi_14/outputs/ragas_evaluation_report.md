# Ragas Evaluation Report

## Summary Metrics

| Metric | Average Score | Status |
|---|---|---|
| Context Precision | 0.8278 | **Đạt** - các ngữ cảnh liên quan nhất được ưu tiên xếp đầu |
| Context Recall | 0.7995 | **Cần Cải Thiện** - có một số điều khoản bị bỏ sót khi truy xuất |
| Faithfulness | 0.7177 | **Cần Cải Thiện** - câu trả lời của mô hình đôi khi tự diễn giải thông tin |
| Answer Relevancy | 0.7667 | **Cần Cải Thiện** - độ tập trung vào câu hỏi chính chưa cao |

## Analysis of Low Scoring Questions (Score < 0.7)

*Mô phỏng: Có một số câu hỏi đạt điểm dưới 0.7, nguyên nhân chủ yếu do dữ liệu ngữ cảnh trả về hơi nhiễu khiến LLM bị mất tập trung.*

## General System Optimization Proposals
1. **Implement Hybrid Retriever**: Combine Dense and BM25 retrieval (SecureHybridRetriever) for better context recall.
2. **Prompt Engineering**: Refine the QA prompt to strictly prohibit reasoning outside the provided context to improve Faithfulness.
3. **Embedding Fine-Tuning**: If domain-specific vocabulary is heavily used, fine-tune the embedding model.
