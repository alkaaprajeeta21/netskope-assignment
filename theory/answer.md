# Part B – Theory Answers

---

## 1. Python Concurrency in FastAPI

### Asyncio
- Best suited for **I/O-bound workloads** such as HTTP calls, database queries, and network I/O.
- Uses a single-threaded event loop with cooperative multitasking.
- FastAPI is built on `asyncio`, making it ideal for high-concurrency microservices.

**Limitation:** CPU-intensive tasks block the event loop and degrade overall throughput.

---

### Threads
- Useful for **blocking I/O** when async-compatible libraries are not available.
- Python’s GIL prevents true parallel execution of CPU-bound tasks.
- Suitable for wrapping legacy or third-party blocking code.

---

### Multiprocessing
- Best for **CPU-bound workloads** like ML inference or heavy data processing.
- Uses separate processes and bypasses the GIL.
- Comes with higher memory and IPC overhead.

---

### Recommendation
> In FastAPI services, use `asyncio` for request handling, threads for unavoidable blocking I/O, and multiprocessing only for background or offline CPU-heavy workloads.

---

## 2. LLM Cost Modeling (Self-Hosted vs API)

### Self-Hosted Open-Source Model
- Example: AWS `g5.xlarge` (A10G GPU) ≈ **$1.2/hour**
- Monthly cost ≈ **$900–1000**
- Fixed cost, includes infrastructure and operational overhead.

---

### API-Based LLM
- Pay-per-token or request (≈ $0.002 per 1K tokens).
- 1M requests/month ≈ **$2,000**.
- No infrastructure management.

---

### Break-Even Analysis
- Self-hosting becomes cost-effective only beyond **~500K requests/month**.

**Conclusion:**  
> API-based LLMs are simpler and cheaper at low to medium scale; self-hosting is justified only at sustained high throughput or strict data residency requirements.

---

## 3. RAG Pipeline Design (Scenario II)

### Pipeline Steps
1. Crawl public documentation (docs.netskope.com)
2. Clean, chunk, and embed content
3. Store embeddings in FAISS
4. Embed ticket text and retrieve top-K chunks
5. Construct a deterministic response
6. Return citations with excerpts

---

### Design Rationale
- Minimizes hallucination risk
- Ensures explainability through citations
- Avoids unnecessary LLM generation
- Easier to debug and audit

---

### Possible Improvements
- Cross-encoder re-ranking
- Heading-aware chunking
- Document freshness scoring

---

## 4. RAG Evaluation Without Human Labeling

### Metrics Used
- **Groundedness:** semantic similarity between the answer and retrieved content
- **Classifier stability:** consistency of classification across repeated runs
- **Citation coverage:** proportion of retrieved chunks referenced in the answer

---

### Why This Works
- Fully automated
- No manual labels required
- CI-friendly
- Detects hallucination risk early

---

## 5. Prompt Injection Mitigation

### Prompt Level
- System prompts with strict instructions
- JSON-only structured outputs
- Allow-listed labels

---

### Application Level
- Schema validation of model outputs
- Sanitization before downstream use
- No execution of generated text

---

### Retrieval Level
- Retrieval restricted to trusted, pre-ingested documents
- No user-supplied document ingestion

---

### Infrastructure & Policy
- Secrets managed via environment or secret manager
- Audit logging
- Offline evaluation pipeline for regression detection

---

### Final Note
> Prompt injection is mitigated through layered controls across prompt design, application logic, retrieval constraints, and infrastructure boundaries.
