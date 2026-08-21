import json
import urllib.request
import urllib.error

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

CHROMA_PATH = "./chroma_db"

COLLECTION_NAME = "who_medication_safety_day1"

OLLAMA_MODEL = "llama3.2:latest"

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

# Always return up to 5 closest source chunks
RELEVANCE_TOP_K = 5

# Retrieve more candidates first
RETRIEVAL_CANDIDATES = 30

# Only the BEST result is used to decide
# whether the question belongs to the knowledge base
DISTANCE_REFUSAL_THRESHOLD = 0.75


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# ============================================================
# CONNECT TO CHROMADB
# ============================================================

print("Connecting to ChromaDB...")

client_db = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client_db.get_or_create_collection(
    name=COLLECTION_NAME
)

print(
    "Collection:",
    collection.name,
    "| items:",
    collection.count()
)


# ============================================================
# GROUNDED SYSTEM PROMPT
# ============================================================

GROUNDED_SYSTEM_PROMPT = """
You are HealthInsight AI.

You are a citation-bound healthcare knowledge assistant.

Your ONLY knowledge source is the retrieved content inside
<context>.

The source document is the WHO document:
"Medication Safety in Polypharmacy".

STRICT RULES:

1. Answer ONLY using facts explicitly supported by <context>.

2. NEVER use your general medical knowledge.

3. NEVER complete missing information using assumptions.

4. NEVER invent facts.

5. NEVER invent numbers.

6. NEVER invent medical advice.

7. NEVER invent page numbers.

8. NEVER invent sections.

9. NEVER invent citations.

10. If the context does not directly support the answer,
you MUST refuse.

11. You may combine information from multiple retrieved
results ONLY when the information is actually supported
by those results.

12. The retrieved results are ranked by semantic similarity.
Smaller distance means a closer match.

13. The answer must be based on the retrieved passages,
not on the question alone.

IMPORTANT:

A result can be semantically related but still not contain
enough information to answer the question.

If the retrieved passages do not contain enough information,
return:

confidence = "insufficient"
citations = []
evidence = ""

recommendation = a clear refusal

Do NOT answer from outside knowledge.

RETURN ONLY THIS JSON:

{
  "recommendation": "direct answer or refusal",
  "evidence": "supporting evidence directly from the retrieved context",
  "citations": [
    {
      "document": "string",
      "section": "string",
      "page": number
    }
  ],
  "confidence": "high | medium | low | insufficient"
}

For insufficient context:

{
  "recommendation": "I couldn't find enough information in the indexed WHO guideline to answer this confidently. ...",
  "evidence": "",
  "citations": [],
  "confidence": "insufficient"
}

Return ONLY valid JSON.
"""


# ============================================================
# REFERENCE FILTER
# ============================================================

def is_reference_heavy(text):

    if not text:
        return True

    text_lower = text.lower()

    reference_words = [
        "bibliography",
        "isbn",
        "doi:",
        "http://",
        "https://"
    ]

    score = 0

    for word in reference_words:

        if word in text_lower:
            score += 1

    # Only reject extremely short chunks
    # if they are basically empty.
    if len(text.strip()) < 30:
        score += 1

    return score >= 2


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve(
    query,
    top_k=RELEVANCE_TOP_K
):

    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True
    )

    # Retrieve many candidates first
    candidate_count = max(
        RETRIEVAL_CANDIDATES,
        top_k
    )

    results = collection.query(
        query_embeddings=[
            query_embedding.tolist()
        ],
        n_results=candidate_count,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    retrieved = []

    if not results.get("ids"):
        return retrieved

    if not results["ids"][0]:
        return retrieved

    for i in range(
        len(results["ids"][0])
    ):

        text = (
            results["documents"][0][i]
            if results["documents"][0]
            else ""
        )

        metadata = (
            results["metadatas"][0][i]
            or {}
        )

        distance = (
            results["distances"][0][i]
            if results.get("distances")
            and results["distances"][0]
            else 1.0
        )

        section = metadata.get(
            "section",
            ""
        )

        # ----------------------------------------------------
        # Ignore bibliography/reference chunks
        # ----------------------------------------------------

        if is_reference_heavy(text):

            print(
                "Filtered reference-heavy chunk"
            )

            continue

        if section:

            section_lower = section.lower()

            if (
                "reference" in section_lower
                or "bibliography" in section_lower
            ):

                print(
                    "Filtered section:",
                    section
                )

                continue

        retrieved.append({

            "chunk_id":
                results["ids"][0][i],

            "text":
                text,

            "distance":
                float(distance),

            "document":
                metadata.get(
                    "document",
                    "WHO Medication Safety in Polypharmacy"
                ),

            "section":
                section,

            "page_number":
                metadata.get(
                    "page_number"
                ),

            "source":
                metadata.get(
                    "source",
                    "WHO-UHC-SDS-2019.11-eng.pdf"
                ),

            "source_pdf":
                metadata.get(
                    "source_pdf",
                    "WHO-UHC-SDS-2019.11-eng.pdf"
                )
        })

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # ChromaDB returns DISTANCE.
    #
    # Smaller distance = closer result.
    #
    # Therefore we sort ascending.
    # --------------------------------------------------------

    retrieved.sort(
        key=lambda x: x["distance"]
    )

    # --------------------------------------------------------
    # Return FIVE closest chunks.
    # --------------------------------------------------------

    return retrieved[:top_k]


# ============================================================
# TOP DISTANCE
# ============================================================

def top_distance(retrieved):

    if not retrieved:
        return 1.0

    return min(
        item["distance"]
        for item in retrieved
    )


# ============================================================
# REFUSAL MESSAGE
# ============================================================

def build_refusal_message(query):

    return (
        "I couldn't find enough information in the indexed "
        "WHO guideline to answer this confidently. "
        f'I searched the retrieved passages for "{query}". '
        "Try rephrasing the question or ask about a topic "
        "covered by the WHO Medication Safety knowledge base."
    )


# ============================================================
# BUILD CONTEXT
# ============================================================

def assemble_prompt(
    query,
    retrieved_chunks
):

    context_blocks = []

    for index, item in enumerate(
        retrieved_chunks,
        start=1
    ):

        page = item.get(
            "page_number"
        )

        if page is None:
            page = "Not specified"

        section = item.get(
            "section"
        )

        if not section:
            section = "Not specified"

        context_blocks.append(

            f"""
RESULT #{index}

Document:
{item["document"]}

Section:
{section}

Page:
{page}

Distance:
{item["distance"]}

Content:
{item["text"]}
"""
        )

    context = (
        "\n\n==============================\n\n"
        .join(context_blocks)
    )

    return f"""
<context>

{context}

</context>

QUESTION:
{query}

IMPORTANT:

Answer ONLY from the information explicitly contained
inside <context>.

If the context does not directly contain enough information
to answer the question, refuse.

Do not use outside medical knowledge.

Return ONLY valid JSON.
"""


# ============================================================
# CALL OLLAMA
# ============================================================

def call_ollama(
    system_prompt,
    user_message
):

    payload = {

        "model":
            OLLAMA_MODEL,

        "messages": [

            {
                "role":
                    "system",

                "content":
                    system_prompt
            },

            {
                "role":
                    "user",

                "content":
                    user_message
            }

        ],

        "stream":
            False,

        "options": {

            "temperature":
                0
        }
    }

    data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(

        OLLAMA_URL,

        data=data,

        headers={
            "Content-Type":
                "application/json"
        },

        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:

            response_data = (
                response
                .read()
                .decode("utf-8")
            )

            result = json.loads(
                response_data
            )

            return (
                result
                .get("message", {})
                .get("content", "")
            )

    except urllib.error.HTTPError as e:

        error_body = (
            e.read()
            .decode(
                "utf-8",
                errors="ignore"
            )
        )

        raise RuntimeError(
            f"Ollama HTTP error {e.code}: "
            f"{error_body}"
        )

    except urllib.error.URLError as e:

        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure Ollama is running. "
            f"Details: {e}"
        )

    except Exception as e:

        raise RuntimeError(
            f"Ollama error: {str(e)}"
        )


# ============================================================
# PARSE JSON
# ============================================================

def parse_llm_json(raw_text):

    if not raw_text:

        return (
            None,
            "Empty model response"
        )

    cleaned = raw_text.strip()

    # Remove markdown code fences
    if cleaned.startswith("```"):

        lines = cleaned.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):

            lines = lines[:-1]

        cleaned = "\n".join(
            lines
        ).strip()

    # Find JSON object
    if not cleaned.startswith("{"):

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if (
            start != -1
            and end != -1
        ):

            cleaned = cleaned[
                start:end + 1
            ]

    try:

        return (
            json.loads(cleaned),
            None
        )

    except json.JSONDecodeError as e:

        return (
            None,
            str(e)
        )


# ============================================================
# VALIDATE RESPONSE
# ============================================================

def validate_response(obj):

    if not isinstance(
        obj,
        dict
    ):

        return False

    required = [
        "recommendation",
        "evidence",
        "citations",
        "confidence"
    ]

    for key in required:

        if key not in obj:
            return False

    allowed_confidence = [
        "high",
        "medium",
        "low",
        "insufficient"
    ]

    if (
        obj["confidence"]
        not in allowed_confidence
    ):

        return False

    if not isinstance(
        obj["recommendation"],
        str
    ):

        return False

    if not isinstance(
        obj["evidence"],
        str
    ):

        return False

    if not isinstance(
        obj["citations"],
        list
    ):

        return False

    # --------------------------------------------------------
    # Insufficient MUST have no evidence/citations
    # --------------------------------------------------------

    if obj["confidence"] == "insufficient":

        if obj["evidence"].strip():
            return False

        if obj["citations"]:
            return False

    # --------------------------------------------------------
    # High / Medium must have evidence + citations
    # --------------------------------------------------------

    if obj["confidence"] in [
        "high",
        "medium"
    ]:

        if not obj["evidence"].strip():
            return False

        if not obj["citations"]:
            return False

    # --------------------------------------------------------
    # Validate citations
    # --------------------------------------------------------

    for citation in obj["citations"]:

        if not isinstance(
            citation,
            dict
        ):

            return False

        if "document" not in citation:
            return False

        if "section" not in citation:
            return False

        if "page" not in citation:
            return False

    return True


# ============================================================
# BUILD FRONTEND RESULTS
# ============================================================

def build_results(
    retrieved
):

    results = []

    for item in retrieved:

        page = item.get(
            "page_number"
        )

        if page is None:
            page = "Not specified"

        section = item.get(
            "section"
        )

        if not section:
            section = "Not specified"

        source = item.get(
            "source"
        )

        if not source:
            source = (
                item.get(
                    "source_pdf"
                )
                or
                "WHO-UHC-SDS-2019.11-eng.pdf"
            )

        # ----------------------------------------------------
        # ChromaDB uses distance:
        #
        # Smaller distance = more similar
        #
        # Convert it to a similarity score.
        # ----------------------------------------------------

        distance = float(
            item["distance"]
        )

        similarity = max(
            0.0,
            1.0 - distance
        )

        results.append({

            "rank": 0,

            "answer":
                item["text"],

            "text":
                item["text"],

            "chunk_id":
                item["chunk_id"],

            "distance":
                distance,

            "similarity":
                similarity,

            "similarity_percent":
                round(
                    similarity * 100,
                    2
                ),

            "document":
                item["document"],

            "page":
                page,

            "page_number":
                page,

            "section":
                section,

            "source":
                source,

            "source_pdf":
                source
        })

    # --------------------------------------------------------
    # MOST IMPORTANT PART
    #
    # Highest similarity first.
    # Therefore:
    #
    # 0.90
    # 0.80
    # 0.70
    # 0.60
    # 0.50
    #
    # NOT:
    #
    # 0.50
    # 0.60
    # 0.70
    # 0.80
    # 0.90
    # --------------------------------------------------------

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    # --------------------------------------------------------
    # Re-number ranks after sorting
    # --------------------------------------------------------

    for index, result in enumerate(
        results,
        start=1
    ):

        result["rank"] = index

    return results


# ============================================================
# MAIN RAG PIPELINE
# ============================================================

def run_pipeline(query):

    query = query.strip()

    # --------------------------------------------------------
    # 1. RETRIEVE TOP 5
    # --------------------------------------------------------

    retrieved = retrieve(
        query,
        top_k=RELEVANCE_TOP_K
    )

    # --------------------------------------------------------
    # 2. NO RESULTS
    # --------------------------------------------------------

    if not retrieved:

        return {

            "query":
                query,

            "recommendation":
                build_refusal_message(
                    query
                ),

            "evidence":
                "",

            "citations":
                [],

            "confidence":
                "insufficient",

            "refused":
                True,

            "refusal_reason":
                "no_relevant_results",

            "results":
                [],

            "top_distance":
                1.0
        }

    # --------------------------------------------------------
    # 3. BEST MATCH
    # --------------------------------------------------------

    distance = top_distance(
        retrieved
    )

    print(
        "\nRetrieved relevant results:",
        len(retrieved)
    )

    for index, item in enumerate(
        retrieved,
        start=1
    ):

        similarity = max(
            0.0,
            1.0 - item["distance"]
        )

        print(
            f"#{index} | "
            f"distance={item['distance']:.4f} | "
            f"similarity={similarity:.4f} | "
            f"similarity%={similarity * 100:.2f}% | "
            f"page={item.get('page_number')} | "
            f"section={item.get('section')}"
        )

    # --------------------------------------------------------
    # 4. KNOWLEDGE BASE GATE
    #
    # Only BEST match must pass threshold.
    # --------------------------------------------------------

    if (
        distance
        > DISTANCE_REFUSAL_THRESHOLD
    ):

        print(
            "Question rejected by distance gate:",
            distance
        )

        return {

            "query":
                query,

            "recommendation":
                build_refusal_message(
                    query
                ),

            "evidence":
                "",

            "citations":
                [],

            "confidence":
                "insufficient",

            "refused":
                True,

            "refusal_reason":
                "no_relevant_results",

            "results":
                [],

            "top_distance":
                distance
        }

    # --------------------------------------------------------
    # 5. BUILD CONTEXT
    # --------------------------------------------------------

    user_message = assemble_prompt(
        query,
        retrieved
    )

    # --------------------------------------------------------
    # 6. OLLAMA
    # --------------------------------------------------------

    try:

        raw = call_ollama(
            GROUNDED_SYSTEM_PROMPT,
            user_message
        )

    except Exception as e:

        print(
            "Ollama error:",
            str(e)
        )

        return {

            "query":
                query,

            "recommendation":
                "The local AI service could not be reached.",

            "evidence":
                "",

            "citations":
                [],

            "confidence":
                "insufficient",

            "refused":
                True,

            "refusal_reason":
                f"llm_error: {str(e)}",

            "results":
                build_results(
                    retrieved
                ),

            "top_distance":
                distance
        }

    # --------------------------------------------------------
    # 7. PARSE
    # --------------------------------------------------------

    parsed, parse_error = (
        parse_llm_json(raw)
    )

    if parsed is None:

        print(
            "JSON parse failed:",
            parse_error
        )

        return {

            "query":
                query,

            "recommendation":
                build_refusal_message(
                    query
                ),

            "evidence":
                "",

            "citations":
                [],

            "confidence":
                "insufficient",

            "refused":
                True,

            "refusal_reason":
                "json_parse_failed",

            "results":
                build_results(
                    retrieved
                ),

            "top_distance":
                distance
        }

    # --------------------------------------------------------
    # 8. VALIDATE
    # --------------------------------------------------------

    if not validate_response(
        parsed
    ):

        print(
            "Response validation failed"
        )

        return {

            "query":
                query,

            "recommendation":
                build_refusal_message(
                    query
                ),

            "evidence":
                "",

            "citations":
                [],

            "confidence":
                "insufficient",

            "refused":
                True,

            "refusal_reason":
                "response_validation_failed",

            "results":
                build_results(
                    retrieved
                ),

            "top_distance":
                distance
        }

    # --------------------------------------------------------
    # 9. FINAL RESPONSE
    # --------------------------------------------------------

    parsed["query"] = query

    parsed["refused"] = (
        parsed["confidence"]
        == "insufficient"
    )

    parsed["top_distance"] = distance

    # --------------------------------------------------------
    # Valid question:
    # ALWAYS return TOP 5 source chunks.
    #
    # Invalid/outside question:
    # return 0 results.
    # --------------------------------------------------------

    if parsed["refused"]:

        parsed["results"] = []

    else:

        parsed["results"] = (
            build_results(
                retrieved
            )
        )

    return parsed


# ============================================================
# TEST
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

    test_question = (
        "What medication-related risks "
        "or problems are associated "
        "with polypharmacy?"
    )

    result = run_pipeline(
        test_question
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )