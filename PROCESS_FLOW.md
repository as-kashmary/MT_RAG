# MT_RAG Application - Complete Process Flow

## System Overview
This is a **Retrieval-Augmented Generation (RAG)** system that uses semantic search and hybrid retrieval to answer user queries based on uploaded documents. It has two main servers: **Admin Server** (for document management) and **User Server** (for query answering).

---

## OVERALL ARCHITECTURE

```
ADMIN SIDE                                      USER SIDE
┌─────────────────────────────────────────────┐ ┌──────────────────────────────────────────┐
│         ADMIN SERVER (Port 8000)             │ │      USER SERVER (Port 8001)             │
│                                              │ │                                          │
│ 1. /parser → Uploads & Parses Documents     │ │ 1. /retrieve_bm25... → Load BM25 Index   │
│ 2. /chunk → Creates Semantic Chunks         │ │ 2. /context_generation → Hybrid Search   │
│ 3. /embedding → Stores Vectors in Pinecone  │ │ 3. /response_generation → LLM Response   │
│ 4. Updates MongoDB with Chunks & BM25       │ │                                          │
└──────────────┬───────────────────────────────┘ └──────────────┬───────────────────────────┘
               │                                                 │
               ├─────────────────────────────────────────────────┤
               ↓                                                 ↓
        ┌─────────────────────────────────────────────────────────────────┐
        │                    EXTERNAL SERVICES                             │
        │ ┌────────────────────┐    ┌─────────────┐   ┌─────────────────┐ │
        │ │   MONGODB          │    │  PINECONE   │   │  OLLAMA (LLM)   │ │
        │ │ (Stores BM25 Index │    │ (Vector DB) │   │ (For Responses) │ │
        │ │  & Chunks)         │    │             │   │                 │ │
        │ └────────────────────┘    └─────────────┘   └─────────────────┘ │
        └─────────────────────────────────────────────────────────────────┘
```

---

## DETAILED STEP-BY-STEP FLOW

### 🔴 PHASE 1: DOCUMENT INGESTION (ADMIN SERVER)

#### Step 1️⃣: `/parser` Endpoint - Document Parsing
**Purpose:** Extract text content from different file formats

**What happens:**
1. Admin uploads a document (PDF, TXT, or DOCX)
2. System detects file type
3. Appropriate loader extracts raw text:
   - **PDF**: Uses `PyPDFLoader` → extracts & concatenates all pages
   - **TXT**: Uses `TextLoader` with proper encoding detection
   - **DOCX**: Uses `Docx2txtLoader`
4. Extracted text is stored in `admin_session.parsed_contents_list`

**Input:**
```
- admin_id: Unique admin identifier
- product_id: Which product this document belongs to
- company_id: Which company owns this product
- document_path: File or folder path
```

**Output:**
```json
{
  "file_name": "airpods.txt",
  "product_id": "airpods",
  "company_id": "apple",
  "time": 0.45
}
```

---

#### Step 2️⃣: `/chunk` Endpoint - Semantic Chunking
**Purpose:** Split documents into semantically meaningful chunks

**What happens:**
1. Takes the raw text from Step 1
2. Uses **SemanticChunker** with embeddings to split text intelligently:
   - Instead of splitting by word count or characters
   - Splits based on semantic similarity between sentences
   - Uses percentile-based breakpoint (default: 90th percentile)
3. Each chunk is a logically complete piece (paragraph, sentence group)

**Example:**
```
Raw Text: "The AirPods Pro provide excellent noise cancellation. 
They are wireless and connect via Bluetooth. The battery lasts up to 6 hours..."

↓ Semantic Chunking ↓

Chunk 1: "The AirPods Pro provide excellent noise cancellation. They are wireless..."
Chunk 2: "The battery lasts up to 6 hours of continuous listening..."
```

**Data Structure Created:**
```python
admin_session.parsed_contents_list = [
    {
        "file_name": "airpods.txt",
        "product_id": "airpods",
        "company_id": "apple",
        "chunks": [
            "Chunk text 1",
            "Chunk text 2",
            "Chunk text 3",
            ...
        ]
    }
]
```

---

#### Step 3️⃣: `/embedding` Endpoint - Vector Embedding & Storage
**Purpose:** Convert text chunks into numerical vectors and store them

**What happens:**

##### 3a: Convert Chunks to Vectors
1. Uses `LocalEmbeddings` model: `multilingual-e5-large-instruct`
   - This model converts any text → 1024-dimensional vector
   - Loaded on server startup (lazy loading)
2. Each chunk → vector representation capturing semantic meaning

##### 3b: Create BM25 Index
1. **BM25** is a keyword-based ranking algorithm
2. For each chunk, tokenize into words
3. Calculate BM25 scores based on:
   - Term frequency in chunk (TF)
   - Document frequency across chunks (IDF)
   - Document length normalization
4. Store BM25 internal state in MongoDB:
   ```python
   bm25_variables = {
       'corpus_size': 100,
       'avgdl': 45.2,
       'doc_freqs': {...},
       'idf': {...},
       'doc_len': [...],
       'average_idf': 3.5,
       'k1': 1.5,
       'b': 0.75,
       'epsilon': 0.25
   }
   ```

##### 3c: Store in Vector Database (Pinecone)
1. Vectors are uploaded to **Pinecone** (cloud vector database)
2. Each vector has:
   - **ID**: Unique identifier (e.g., "0", "1", "2")
   - **Values**: The 1024-dimensional vector
   - **Metadata**: {chunk_index, chunk_text, product_id, company_id}
   - **Namespace**: `{company_id}_{product_id}` (e.g., "apple_airpods")

##### 3d: Store in MongoDB
1. Chunks and BM25 index saved for future retrieval:
   ```json
   {
       "company_id": "apple",
       "product_id": "airpods",
       "chunks": [
           {"index": 0, "text": "..."},
           {"index": 1, "text": "..."}
       ],
       "bm25_index_variables": {...},
       "chunk_length": 50
   }
   ```

---

### 🟢 PHASE 2: USER QUERY ANSWERING (USER SERVER)

#### Step 4️⃣: `/retrieve_bm25_index_and_chunks` Endpoint
**Purpose:** Load all necessary data into memory for a user session

**What happens:**
1. User specifies `company_id` and `product_id` they want to query
2. System retrieves from MongoDB:
   - All chunks for this product
   - BM25 index variables for this product
3. Stores in `user_session` for fast access:
   ```python
   user_session.product_based_bm25_dict[product_id] = {
       "bm25_object": <BM25 object>,
       "chunk_length": 50,
       "chunks": [
           (1, "Chunk text 1"),
           (2, "Chunk text 2"),
           ...
       ]
   }
   ```

**Why?** 
- Avoids repeated database queries
- Keeps data in RAM for fast retrieval
- One session per user stores multiple products

---

#### Step 5️⃣: `/context_generation` Endpoint - Hybrid Retrieval
**Purpose:** Find the most relevant chunks for a user query

**What happens:**

##### 5a: User Input
```json
{
  "user_id": "user123",
  "product_id": "airpods",
  "query": "How can I improve the noise cancellation on my AirPods?",
  "company_id": "apple"  // from previous step
}
```

##### 5b: Dual Retrieval Process (Fusion Retrieval)

###### PART 1: Vector Search (Semantic)
1. Embed the query using same model that embedded chunks
2. Find most similar vectors in Pinecone using cosine similarity
3. Returns chunks sorted by semantic relevance to query

```
Query: "How can I improve the noise cancellation?"
↓ Embed to vector ↓
Query Vector: [0.2, 0.5, -0.1, ..., 0.3]
↓ Search Pinecone ↓
Results (sorted by similarity):
- Chunk 5: similarity=0.95 ✓ "To improve ANC, enable transparency..."
- Chunk 12: similarity=0.87 ✓ "Adjust noise cancellation in settings..."
- Chunk 3: similarity=0.65 "Battery charging information..."
```

###### PART 2: BM25 Search (Keyword)
1. Tokenize query: "How → how, can → can, improve → improve, noise → noise, cancellation → cancellation"
2. Calculate BM25 scores for each chunk
3. Higher scores for chunks containing these keywords

```
BM25 Scores:
- Chunk 5: 3.5 ✓ (contains "improve", "noise", "cancellation")
- Chunk 12: 2.8 ✓ (contains "noise", "cancellation")
- Chunk 3: 0.1 (few matching keywords)
```

###### PART 3: Fusion (Combine Both)
1. Normalize both scores to 0-1 range
2. Use alpha=0.5 (equal weight):
   ```
   Combined Score = 0.5 × vector_score + 0.5 × bm25_score
   ```
3. Rank by combined score

```
Results:
1. Chunk 5: 0.5×0.95 + 0.5×3.5 = 1.925 ← BEST
2. Chunk 12: 0.5×0.87 + 0.5×2.8 = 1.835
3. Chunk 3: 0.5×0.65 + 0.5×0.1 = 0.375
```

##### 5c: Get Top-K Chunks
1. Retrieve top 5 indexed chunks (e.g., indices: [5, 12, 2, 8, 1])
2. Adjust indices (+1) to match MongoDB storage (1-based indexing)
3. Fetch actual chunk texts from memory:
   ```python
   result_indexes = [5, 12, 2, 8, 1]  # From fusion
   sorted_chunks = []
   for idx in result_indexes:
       sorted_chunks.append(find_chunk_with_index(idx))
   # sorted_chunks[0], sorted_chunks[1], sorted_chunks[2] = Top 3
   ```

##### 5d: Concatenate Top Chunks into Context
```python
context = top_chunk_1 + top_chunk_2 + top_chunk_3

# Example:
context = """To improve ANC, enable transparency mode to adjust levels. 
    Adjust noise cancellation in Settings > Bluetooth > AirPods > 
    Noise Control. Choose Noise Cancellation, Transparency, or Off."""
```

**Output:**
```json
{
  "context": "To improve ANC, enable transparency mode... Adjust noise cancellation in Settings..."
}
```

---

#### Step 6️⃣: `/response_generation` Endpoint - LLM Response
**Purpose:** Generate a natural language answer using the retrieved context

**What happens:**

##### 6a: Create Prompt
```
Prompt = """
Using the following context, provide a detailed and informative answer to the query.

Context: {context from Step 5}

Query: {user's original query}

Answer:
"""
```

Example:
```
Context: To improve ANC, enable transparency mode to adjust levels. 
Adjust noise cancellation in Settings > Bluetooth > AirPods > Noise Control. 
Choose Noise Cancellation, Transparency, or Off.

Query: How can I improve the noise cancellation on my AirPods?

Answer:
```

##### 6b: Stream Response from LLM
1. Send prompt to Ollama API (cloud LLM)
2. Using model: `deepseek-v3.1:671b-cloud`
3. Response streams back word-by-word
4. Accumulate all chunks into final response

```python
response = ""
for chunk in llm.chat(model="deepseek-v3.1:671b-cloud", prompt=prompt):
    response += chunk  # Accumulate streaming chunks
```

##### 6c: Return Final Answer
```json
{
  "response": "To improve noise cancellation on your AirPods Pro, you can adjust the settings through your device. Go to Settings > Bluetooth > AirPods > Noise Control and choose between Noise Cancellation (blocks external sound), Transparency (lets external sound in), or Off. You can also enable Adaptive Audio to automatically adjust based on your environment."
}
```

---

## 📊 DATA FLOW DIAGRAM

```
ADMIN WORKFLOW:
Document Upload
    ↓
/parser (Extract Text)
    ↓
/chunk (Semantic Chunking)
    ↓
/embedding (Create Vectors & BM25)
    ↓
Save to MongoDB + Pinecone
    ↓
Ready for Queries

USER WORKFLOW:
User Query
    ↓
/retrieve_bm25_index_and_chunks (Load Session Data)
    ↓
/context_generation (Hybrid Retrieval)
    ├─→ Vector Search (Semantic)
    ├─→ BM25 Search (Keyword)
    └─→ Fusion & Ranking
    ↓
/response_generation (LLM Answer)
    ↓
User Response
```

---

## 🔐 DATA STORAGE LOCATIONS

| Data | Storage | Purpose |
|------|---------|---------|
| Raw Documents | Local filesystem | Original files uploaded |
| Chunks | MongoDB | Persistent storage, retrieval by company/product |
| BM25 Index | MongoDB | Pre-computed scores for keyword search |
| Vectors | Pinecone | Vector search in cloud |
| Embedding Model | Local `./models/` | Multi-lingual semantic understanding |
| Session Data | Server RAM | Fast access during user session |

---

## 🎯 KEY CONCEPTS

### 1. **Semantic Chunking**
- Instead of fixed-size chunks, splits based on semantic meaning
- Uses embeddings to find natural break points
- Better for RAG: preserves context within chunks

### 2. **Hybrid Retrieval (Fusion)**
- **Vector Search**: Understands meaning, good for paraphrases
- **BM25 Search**: Exact keywords, good for specific terms
- **Combined**: Gets benefits of both approaches

### 3. **BM25 (Okapi BM25)**
- Probabilistic ranking function
- Considers: term frequency, document frequency, document length
- Stored as variables (not full corpus) to save space

### 4. **Namespaces**
- Pinecone organizes vectors by namespace
- Format: `{company_id}_{product_id}`
- Allows querying only relevant company/product vectors

### 5. **Sessions**
- **Admin Session**: Stores parsed content & chunks during upload
- **User Session**: Stores BM25 objects & chunks for each user

---

## 📝 EXAMPLE: Complete Flow

### User: "Can I use AirPods underwater?"

**Step 1-3:** Admin uploads AirPods documentation (done previously)

**Step 4:** User loads AirPods product data
```
GET /retrieve_bm25_index_and_chunks?user_id=user123&company_id=apple&product_id=airpods
```

**Step 5:** System finds relevant chunks
```
Vector Search finds: "AirPods are water-resistant up to 1 meter for up to 30 minutes"
BM25 Search finds: "Water resistance, underwater, submersion"
Combined: Returns water-resistance chunk as most relevant
```

**Step 6:** LLM generates answer
```
Prompt Context: "AirPods are water-resistant up to 1 meter for up to 30 minutes..."
LLM Response: "AirPods are water-resistant, not waterproof. They can handle 
splashes and brief water submersion up to 1 meter for 30 minutes. However, 
they are not designed for underwater use like swimming. For extended water 
activities, avoid deep water immersion."
```

---

## 🔧 Technologies Used

- **FastAPI**: Web framework for both servers
- **MongoDB**: Document storage for chunks & BM25 indexes
- **Pinecone**: Cloud vector database
- **Ollama**: LLM API for response generation
- **LangChain**: Document loading, semantic chunking
- **HuggingFace**: Embeddings model (multilingual-e5-large-instruct)
- **Rank-BM25**: BM25 implementation

---

## 🚀 Server Startup

```bash
# Terminal 1: Admin Server (Port 8000)
python -m src.admin_server

# Terminal 2: User Server (Port 8001)  
python -m src.user_server
```

Both servers:
1. Load embedding model on startup
2. Connect to Pinecone
3. Initialize MongoDB connections
4. Ready to accept requests

---

## 📌 Important Notes

- **Index Collision**: Future issue to resolve with ID uniqueness in Pinecone
- **Multiprocessing**: Can be added for faster document parsing
- **Scaling**: BM25 rebuilding needed when knowledge base updates frequently
- **Authentication**: Admin endpoints require Bearer token for security
