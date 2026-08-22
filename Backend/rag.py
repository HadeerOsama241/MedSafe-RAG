import os
import json
import re
import requests
import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# 1. CONFIGURATION
# ============================================================

# ============================================================
# CHROMA API KEY — CHANGE THIS LINE LATER
# ============================================================
CHROMA_API_KEY = "ck-EA4u5Tb8XfxycCRcTiwYaVYZ9XHojafAjp8pLcVhXH15"

CHROMA_TENANT = "70ff981a-a0e8-4bcc-a0d7-878ba669cfbd"
CHROMA_DATABASE = "medsafe-rag"

COLLECTION_NAME = "who_medication_safety_day1"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2:latest"

# Number of candidates requested from Chroma
RETRIEVAL_CANDIDATES = 30

# Number of final chunks sent to LLM
TOP_K = 5

# Compatibility name used by app.py
RELEVANCE_TOP_K = TOP_K

# Refuse if closest result is too far
DISTANCE_REFUSAL_THRESHOLD = 0.75


# ============================================================
# 2. LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)

print("Embedding model loaded.")


# ============================================================
# 3. CONNECT TO CHROMA CLOUD
# ============================================================

print("Connecting to Chroma Cloud...")

if (
    not CHROMA_API_KEY
    or CHROMA_API_KEY == "YOUR_CHROMA_API_KEY"
):
    raise RuntimeError(
        "CHROMA_API_KEY is missing. "
        "Put your Chroma API key in the CHROMA_API_KEY variable "
        "at the top of rag.py."
    )


chroma_client = chromadb.CloudClient(
    api_key=CHROMA_API_KEY,
    tenant=CHROMA_TENANT,
    database=CHROMA_DATABASE
)


collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)


collection_count = collection.count()


print(
    f"Cloud collection: {COLLECTION_NAME} | "
    f"items: {collection_count}"
)


# ============================================================
# 4. CONSTANTS / FILTERING
# ============================================================

EXCLUDED_SECTIONS = {
    "references",
    "reference",
    "bibliography",
    "front matter",
    "contents",
    "table of contents",
    "acknowledgements"
}


def normalize_text(text):
    """
    Normalize text to make filtering more reliable.
    """

    if not text:
        return ""

    text = str(text)

    text = text.replace("\x00", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normalize_section(section):
    """
    Normalize section metadata.
    """

    if not section:
        return ""

    return normalize_text(section)


def is_reference_heavy(text, section=""):
    """
    Detect chunks that are mainly references,
    citations, bibliography entries,
    or very weak fragments.
    """

    text = normalize_text(text)

    section = normalize_section(section)

    if not text:
        return True

    section_lower = section.lower().strip()

    # Explicit excluded sections
    if section_lower in EXCLUDED_SECTIONS:
        return True

    # Reference-like section names
    if "reference" in section_lower:
        return True

    if "bibliograph" in section_lower:
        return True

    # Very short chunks
    if len(text) < 80:
        return True

    # Mostly citation-like text
    citation_matches = re.findall(
        r"\(\s*\d+(?:[-–]\d+)?\s*\)",
        text
    )

    if len(citation_matches) >= 5 and len(text) < 500:
        return True

    # Too many URLs / DOI-like strings
    url_count = len(
        re.findall(
            r"(https?://|doi\.org|www\.)",
            text.lower()
        )
    )

    if url_count >= 2:
        return True

    return False


# ============================================================
# 5. METADATA HELPERS
# ============================================================

def get_metadata_value(
    metadata,
    *keys,
    default=""
):
    """
    Safely get metadata from Chroma.
    """

    if not metadata:
        return default

    for key in keys:

        value = metadata.get(key)

        if (
            value is not None
            and str(value).strip()
        ):
            return value

    return default


def get_page(metadata):
    """
    Get page number safely.
    """

    value = get_metadata_value(
        metadata,
        "page",
        "page_number",
        "page_num",
        default=""
    )

    try:
        return int(value)

    except (TypeError, ValueError):
        return value


def get_section(metadata):
    """
    Get section safely.
    """

    section = get_metadata_value(
        metadata,
        "section",
        "section_name",
        "heading",
        default=""
    )

    return normalize_section(section)


def get_document(metadata):
    """
    Get document name safely.
    """

    return get_metadata_value(
        metadata,
        "document",
        "document_name",
        default="WHO Medication Safety in Polypharmacy"
    )


def get_source(metadata):
    """
    Get source file safely.
    """

    return get_metadata_value(
        metadata,
        "source_pdf",
        "source",
        "file_name",
        default="WHO-UHC-SDS-2019.11-eng.pdf"
    )


# ============================================================
# 6. RETRIEVAL
# ============================================================

def retrieve_documents(
    query,
    top_k=TOP_K
):
    """
    Retrieve relevant chunks from Chroma Cloud.

    - Request many candidates.
    - Filter weak/reference chunks.
    - Sort by distance ascending.
    - Lower distance = more relevant.
    """

    print("\nRetrieving documents...")

    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True
    ).tolist()


    raw_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=RETRIEVAL_CANDIDATES,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )


    documents = raw_results.get(
        "documents",
        [[]]
    )[0]

    metadatas = raw_results.get(
        "metadatas",
        [[]]
    )[0]

    distances = raw_results.get(
        "distances",
        [[]]
    )[0]


    candidates = []


    for i in range(len(documents)):

        text = normalize_text(
            documents[i]
        )

        metadata = (
            metadatas[i]
            if i < len(metadatas)
            else {}
        )

        distance = (
            distances[i]
            if i < len(distances)
            else 999.0
        )


        section = get_section(
            metadata
        )


        # ----------------------------------------------------
        # Filter weak/reference chunks
        # ----------------------------------------------------

        if is_reference_heavy(
            text,
            section
        ):

            print(
                "Filtered weak/reference chunk"
            )

            continue


        if (
            section.lower()
            in EXCLUDED_SECTIONS
        ):

            print(
                f"Filtered section: {section}"
            )

            continue


        # ----------------------------------------------------
        # Similarity
        # ----------------------------------------------------

        similarity = max(
            0.0,
            min(
                1.0,
                1.0 - float(distance)
            )
        )


        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

        chunk_id = get_metadata_value(
            metadata,
            "chunk_id",
            "id",
            default=""
        )


        page = get_page(
            metadata
        )


        document = get_document(
            metadata
        )


        source = get_source(
            metadata
        )


        candidates.append({

            "text": text,

            "chunk_id": chunk_id,

            "distance": float(
                distance
            ),

            "similarity": similarity,

            "similarity_percent": round(
                similarity * 100,
                2
            ),

            "document": document,

            "page": page,

            "page_number": page,

            "section": section,

            "source": source,

            "source_pdf": source
        })


    # ========================================================
    # Sort CLOSEST -> FARTHEST
    # ========================================================

    candidates.sort(
        key=lambda x: x["distance"]
    )


    results = candidates[:top_k]


    # ========================================================
    # Assign ranks
    # ========================================================

    for rank, result in enumerate(
        results,
        start=1
    ):

        result["rank"] = rank


    print(
        "\nFinal filtered retrieval:"
    )


    for result in results:

        print(
            f"#{result['rank']} | "
            f"page={result['page']} | "
            f"section={result['section']} | "
            f"distance={result['distance']:.4f} | "
            f"text_length={len(result['text'])}"
        )


    print(
        f"\nRetrieved relevant results: "
        f"{len(results)}"
    )


    for result in results:

        print(
            f"#{result['rank']} | "
            f"distance={result['distance']:.4f} | "
            f"similarity={result['similarity']:.4f} | "
            f"similarity%={result['similarity_percent']:.2f}% | "
            f"page={result['page']} | "
            f"section={result['section']}"
        )


    return results


# ============================================================
# 7. BUILD CONTEXT
# ============================================================

def build_context(results):

    """
    Build numbered context for Ollama.
    """

    context_parts = []


    for result in results:

        context_parts.append(

            f"""
SOURCE {result['rank']}

Document: {result['document']}

Page: {result['page']}

Section: {result['section']}

Source file: {result['source']}

Text:

{result['text']}
""".strip()
        )


    return (
        "\n\n"
        "=============================="
        "\n\n"
    ).join(
        context_parts
    )


# ============================================================
# 8. FIND BEST SOURCE
# ============================================================

def find_best_source(results):

    """
    Always select strongest retrieved chunk.
    """

    if not results:
        return None

    return results[0]


# ============================================================
# 9. VALIDATE CITATION
# ============================================================

def validate_citation(
    citation,
    results
):

    """
    Make sure citation comes from
    an actual retrieved result.
    """

    if not citation:
        return False


    document = citation.get(
        "document",
        ""
    )

    section = citation.get(
        "section",
        ""
    )

    page = citation.get(
        "page",
        ""
    )


    for result in results:

        if (
            str(result["document"]).strip()
            == str(document).strip()

            and

            str(result["section"]).strip()
            == str(section).strip()

            and

            str(result["page"]).strip()
            == str(page).strip()
        ):

            return True


    return False


# ============================================================
# 10. CALL OLLAMA
# ============================================================

def call_ollama(
    query,
    results
):

    context = build_context(
        results
    )


    system_prompt = """

You are HealthInsight, a citation-grounded medical information assistant.

Your task is to answer ONLY from the supplied WHO document context.

Rules:

1. Do NOT use outside knowledge.

2. Do NOT invent facts.

3. Do NOT invent pages.

4. Do NOT invent sections.

5. Do NOT create citations yourself.

6. The final citation will be selected by the application from the retrieved chunks.

7. Keep the answer concise and directly related to the question.

8. The evidence must be directly supported by the supplied context.

9. If the context does not contain enough information, say that the available WHO context is insufficient.

10. Return valid JSON only.

Return exactly:

{
  "recommendation": "answer based only on context",
  "evidence": "direct supporting statement based only on context",
  "confidence": "high"
}

"""


    user_prompt = f"""

Question:

{query}

WHO DOCUMENT CONTEXT:

{context}

Answer the question using only this context.

"""


    payload = {

        "model": OLLAMA_MODEL,

        "messages": [

            {
                "role": "system",
                "content": system_prompt
            },

            {
                "role": "user",
                "content": user_prompt
            }

        ],

        "stream": False,

        "format": "json",

        "options": {
            "temperature": 0.0
        }
    }


    response = requests.post(

        OLLAMA_URL,

        json=payload,

        timeout=120
    )


    response.raise_for_status()


    data = response.json()


    raw_content = data.get(
        "message",
        {}
    ).get(
        "content",
        ""
    )


    print(
        "\nRaw Ollama response:"
    )

    print(
        raw_content
    )


    try:

        parsed = json.loads(
            raw_content
        )

    except json.JSONDecodeError:

        parsed = {

            "recommendation":
                raw_content.strip(),

            "evidence":
                "",

            "confidence":
                "medium"
        }


    return parsed


# ============================================================
# 11. MAIN RAG FUNCTION
# ============================================================

def ask_healthinsight(query):

    query = normalize_text(
        query
    )


    if not query:

        return {

            "recommendation":
                "",

            "evidence":
                "",

            "citations":
                [],

            "confidence":
                "low",

            "query":
                query,

            "refused":
                True,

            "reason":
                "Empty query",

            "results":
                []
        }


    # --------------------------------------------------------
    # Retrieval
    # --------------------------------------------------------

    results = retrieve_documents(
        query,
        top_k=TOP_K
    )


    if not results:

        return {

            "recommendation":
                "I could not find sufficient information "
                "in the WHO document to answer this question.",

            "evidence":
                "",

            "citations":
                [],

            "confidence":
                "low",

            "query":
                query,

            "refused":
                True,

            "reason":
                "No relevant retrieved chunks",

            "results":
                []
        }


    # --------------------------------------------------------
    # Distance refusal
    # --------------------------------------------------------

    top_distance = results[0]["distance"]


    if (
        top_distance
        > DISTANCE_REFUSAL_THRESHOLD
    ):

        return {

            "recommendation":
                "I could not find sufficiently relevant "
                "information in the WHO document to answer "
                "this question.",

            "evidence":
                "",

            "citations":
                [],

            "confidence":
                "low",

            "query":
                query,

            "refused":
                True,

            "reason":
                "Retrieval relevance too low",

            "top_distance":
                top_distance,

            "results":
                results
        }


    # --------------------------------------------------------
    # Ask LLM
    # --------------------------------------------------------

    llm_result = call_ollama(
        query,
        results
    )


    # --------------------------------------------------------
    # Citation selected by application
    # --------------------------------------------------------

    best_source = find_best_source(
        results
    )


    citation = {

        "document":
            best_source["document"],

        "section":
            best_source["section"],

        "page":
            best_source["page"]
    }


    # --------------------------------------------------------
    # Validate citation
    # --------------------------------------------------------

    if not validate_citation(
        citation,
        results
    ):

        print(
            "Citation validation failed. "
            "Using top retrieved result."
        )


        best_source = results[0]


        citation = {

            "document":
                best_source["document"],

            "section":
                best_source["section"],

            "page":
                best_source["page"]
        }


    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    final_result = {

        "recommendation":
            normalize_text(
                llm_result.get(
                    "recommendation",
                    ""
                )
            ),

        "evidence":
            normalize_text(
                llm_result.get(
                    "evidence",
                    ""
                )
            ),

        "citations":
            [
                citation
            ],

        "confidence":
            llm_result.get(
                "confidence",
                "medium"
            ),

        "query":
            query,

        "refused":
            False,

        "top_distance":
            top_distance,

        "results":
            results
    }


    print(
        "\nFINAL RESULT:"
    )


    print(
        json.dumps(
            final_result,
            indent=2,
            ensure_ascii=False
        )
    )


    return final_result


# # ============================================================
# 12. BACKWARD-COMPATIBILITY ALIASES
# ============================================================

def query_rag(query):
    """
    Compatibility alias.
    """
    return ask_healthinsight(query)


def rag_chat(query):
    """
    Compatibility alias.
    """
    return ask_healthinsight(query)


def run_pipeline(query):
    """
    Main pipeline used by Flask app.
    """
    return ask_healthinsight(query)

# ============================================================
# 13. TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n=============================="
    )

    print(
        "Testing HealthInsight RAG"
    )

    print(
        "==============================\n"
    )


    print(
        f"Chroma Cloud database: "
        f"{CHROMA_DATABASE}"
    )


    print(
        f"Collection: "
        f"{COLLECTION_NAME}"
    )


    print(
        f"Collection items: "
        f"{collection_count}"
    )


    test_query = (
        "What medication-related risks or problems "
        "are associated with polypharmacy?"
    )


    result = ask_healthinsight(
        test_query
    )


    print(
        "\n=============================="
    )

    print(
        "TEST FINISHED"
    )

    print(
        "=============================="
    )