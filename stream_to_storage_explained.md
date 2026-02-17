# Why "Stream to Storage"?

You asked about: `API -->|2. Stream to Storage| ObjectStore[S3 / MinIO / LocalDisk]`

In brief: **Do NOT load the file into RAM. Send it straight to the hard drive (or S3).**

## The Problem: "Load to RAM" (The Bad Way)
If User A uploads a **500MB** PDF scan:
1.  Python/FastAPI reads the whole 500MB into your server's RAM.
2.  If 10 users do this at once, your server needs **5GB RAM**.
3.  **Your Server Crashes**.

## The Solution: "Stream to Storage" (The Good Way)
Instead of "holding" the file, your API acts like a **pipe**.
1.  User starts uploading.
2.  FastAPI receives chunk #1 (1MB).
3.  FastAPI immediately writes chunk #1 to MinIO (or Disk).
4.  FastAPI forgets chunk #1 and takes chunk #2.

**Result**: You can upload a **10GB movie** using only **5MB of RAM**.

## Code Example (FastAPI + MinIO)

```python
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Connect to MinIO/S3
    s3 = boto3.client("s3", endpoint_url="http://minio:9000")
    
    # "upload_fileobj" handles the streaming automatically!
    # It reads the file object (spooled in temp memory) and sends it to S3
    s3.upload_fileobj(file.file, "my-bucket", file.filename)
    
    return {"status": "saved directly to storage"}
```

This is **Critical** for your "Zero Cost" architecture because you are likely running on a small machine (e.g., 8GB RAM). You can't afford to waste RAM holding PDFs.
