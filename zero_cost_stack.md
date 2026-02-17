# The "Zero Cost" Industry-Grade Tech Stack

You requested **Zero Cost** but **Industry Grade**. Ideally, "Industry Grade" implies paid SLAs, but we can achieve **"Enterprise Functionality"** using **Open Source Software (OSS)** hosted locally or on a cheap VPS.

Here is the swap list to make your project 100% free to run (assuming you have a computer to run it on).

## 1. The Core Swaps

| Component | Paid / Cloud Version | **The Zero-Cost "Industry Grade" Alternative** | Why it's good |
| :--- | :--- | :--- | :--- |
| **LLM Inference** | GPT-4o / Claude 3.5 Sonnet | **Google Gemini 2.0 Flash (Free Tier)** OR **Ollama (Llama 3 / Mistral)** | Gemini's free tier is generous (15 RPM). Ollama is truly offline/free if you have RAM. |
| **OCR / Vision** | Azure Doc Intelligence ($) | **Surya OCR** or **PaddleOCR** | **Surya** is SOTA for line/table detection. It beats Tesseract significantly for contracts. |
| **Vector DB** | Pinecone ($ / Limited Free) | **ChromaDB** (Local) or **Qdrant** (Docker) | You are already using Chroma. It's excellent and free. |
| **Storage** | AWS S3 | **MinIO** (Docker) | MinIO is S3-compatible. You code for S3, but point it to `localhost:9000`. |
| **Database** | Supabase / RDS | **PostgreSQL** (Docker) | Run the official Postgres image. Industry standard. |
| **Task Queue** | SimpleQueue / SQS | **Redis** (Docker) | Run Redis locally. It's the standard for Celery/FastAPI queues. |
| **Authentication** | Auth0 / Clerk | **FastAPI OAuth2 (JWT)** | Implement self-hosted JWT auth. It's good learning and free. |

---

## 2. Updated Architecture Implementation

### A. OCR Pipeline (Replacing Azure)
Current Plan: `Azure ComputerVisionClient`
**New Plan**: `Surya OCR` (local Python package)

```python
# Install: pip install surya-ocr
from surya.ocr import run_ocr
from surya.model.detection import segformer
from surya.model.recognition.model import load_model, load_processor

def ocr_pipeline(image):
    # Runs locally on CPU or GPU
    predictions = run_ocr([image], [langs], det_model, det_processor, rec_model, rec_processor)
    return predictions[0].text_lines
```
*Note: Surya requires PyTorch. If that's too heavy, `PaddleOCR` is a lighter generic alternative.*

### B. Storage (Replacing S3)
Current Plan: `Upload to S3`
**New Plan**: `MinIO`

1.  Run Docker: `docker run -p 9000:9000 -p 9001:9001 minio/minio server /data`
2.  Use `boto3` in Python just like AWS, but change the `endpoint_url`:
    ```python
    s3 = boto3.client('s3', endpoint_url='http://localhost:9000', aws_access_key_id='minioadmin', ...)
    ```

### C. LLM "Brain" (Replacing GPT-4)
Current Plan: `langchain_openai.ChatOpenAI`
**New Plan**: `langchain_google_genai.ChatGoogleGenerativeAI` or `langchain_community.chat_models.ChatOllama`

*   **Recommendation**: Stick with **Gemini 2.0 Flash**. It has a massive context window (1M tokens) which is *essential* for reading entire legal contracts at once, and it is currenly free for developers (within limits).
*   **Backup**: Use **Ollama** running `llama3:8b`. It's smart enough for "Clause Extraction" but might struggle with complex "Negotiation Strategy" compared to a large model.

---

## 3. Cost-Free Infrastructure Diagram

```mermaid
graph TD
    User[User Laptop] -->|Localhost:3000| Frontend
    Frontend -->|Localhost:8000| API[FastAPI]
    
    subgraph Docker_Compose_Network
        API -->|Task| Redis[Redis]
        API -->|Store| MinIO[MinIO (S3)]
        API -->|Read/Write| DB[PostgreSQL]
        
        Worker[Celery Worker] -->|Poll| Redis
        Worker -->|OCR| Surya[Surya OCR (In-process)]
        Worker -->|Inference| Ollama[Ollama (Optional)]
        Worker -->|Inference| Gemini[Gemini API (Cloud Free Tier)]
        
        Worker -->|Embed| Chroma[ChromaDB (Local Storage)]
    end
```

## 4. Immediate Next Steps
1.  **Stop using Azure**: Delete the Azure imports in `document_parser.py`.
2.  **Install Docker Desktop**: This is required to run MinIO, Redis, and Postgres cleanly on Windows.
3.  **Update Requirements**: Add `surya-ocr` (or `paddleocr`), remove `azure-cognitiveservices-vision-computervision`.
