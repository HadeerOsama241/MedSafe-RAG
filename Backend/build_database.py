import os
import re

import fitz
import chromadb
from sentence_transformers import SentenceTransformer
from llama_parse import LlamaParse
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document as LlamaDocument


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_PATH = os.path.join(
    BASE_DIR,
    "WHO-UHC-SDS-2019.11-eng.pdf"
)

CHROMA_PATH = os.path.join(
    BASE_DIR,
    "chroma_db"
)

COLLECTION_NAME = "who_medication_safety_day1"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


# =========================================================
# 1. CHECK PDF
# =========================================================

if not os.path.exists(PDF_PATH):
    raise FileNotFoundError(
        f"PDF not found:\n{PDF_PATH}"
    )

print("=" * 60)
print("PDF FOUND")
print("=" * 60)
print(PDF_PATH)


# =========================================================
# 2. LLAMACLOUD API KEY
# =========================================================

LLAMA_CLOUD_API_KEY = os.environ.get(
    "LLAMA_CLOUD_API_KEY"
)

if not LLAMA_CLOUD_API_KEY:
    raise ValueError(
        "LLAMA_CLOUD_API_KEY is not set."
    )

print("\nLlamaCloud API key found.")


# =========================================================
# 3. PARSE PDF WITH LLAMAPARSE
# =========================================================

print("\n" + "=" * 60)
print("PARSING PDF WITH LLAMAPARSE")
print("=" * 60)

parser = LlamaParse(
    api_key=LLAMA_CLOUD_API_KEY,
    result_type="markdown",
    verbose=True
)

documents = parser.load_data(
    PDF_PATH
)

print(
    "Parsed documents:",
    len(documents)
)


# =========================================================
# 4. VERIFY PDF PAGES
# =========================================================

pdf_doc = fitz.open(
    PDF_PATH
)

pdf_page_count = len(
    pdf_doc
)

print(
    "PDF pages:",
    pdf_page_count
)

print(
    "LlamaParse documents:",
    len(documents)
)

if len(documents) != pdf_page_count:
    raise ValueError(
        "LlamaParse did not return one document per PDF page. "
        "Do not guess page numbers."
    )


# =========================================================
# 5. ADD PAGE METADATA
# =========================================================

for i, doc in enumerate(documents):

    doc.metadata = dict(
        getattr(
            doc,
            "metadata",
            {}
        ) or {}
    )

    doc.metadata["page_number"] = i + 1

    doc.metadata["source_pdf"] = (
        os.path.basename(PDF_PATH)
    )


print(
    "\nPage metadata example:"
)

print(
    documents[0].metadata
)


# =========================================================
# 6. TEXT CLEANING
# =========================================================

def clean_text(text):

    if not text:
        return ""

    # Remove repeated running header
    text = re.sub(
        r'\nMEDICATION SAFETY IN POLYPHARMACY\s*\n',
        '\n',
        text,
        flags=re.IGNORECASE
    )

    # Remove duplicated header appearing without newline
    text = re.sub(
        r'MEDICATION SAFETY IN POLYPHARMACY'
        r'MEDICATION SAFETY IN POLYPHARMACY',
        'MEDICATION SAFETY IN POLYPHARMACY',
        text,
        flags=re.IGNORECASE
    )

    # Remove isolated page number at the end
    text = re.sub(
        r'\n\s*\d+\s*$',
        '',
        text
    )

    # Normalize spaces
    text = re.sub(
        r'[ \t]+',
        ' ',
        text
    )

    # Normalize excessive blank lines
    text = re.sub(
        r'\n{3,}',
        '\n\n',
        text
    )

    return text.strip()


# =========================================================
# 7. HEADING DETECTION
# =========================================================

IGNORED_HEADINGS = {
    "technical report",
    "contents",
    "table of contents",
    "abbreviations",
    "© world health organization 2019",
    "medication safety in polypharmacy",
}


def normalize_heading(heading):

    heading = re.sub(
        r'[*_`]',
        '',
        heading
    )

    heading = re.sub(
        r'\s+',
        ' ',
        heading
    )

    return heading.strip()


def is_real_section_heading(heading):

    heading = normalize_heading(
        heading
    )

    heading_lower = heading.lower()

    if not heading:
        return False

    if heading_lower in IGNORED_HEADINGS:
        return False

    if heading_lower.startswith(
        "figure"
    ):
        return False

    return True


# =========================================================
# 8. BUILD PAGE-LEVEL SECTIONS
# =========================================================

print("\n" + "=" * 60)
print("BUILDING PAGE-LEVEL SECTIONS")
print("=" * 60)

page_segments = []

current_section = "Front Matter"


for page_idx, doc in enumerate(
    documents
):

    page_number = page_idx + 1

    text = clean_text(
        doc.text
    )

    if not text:
        continue

    matches = []

    for match in re.finditer(
        r'^(#{1,6})\s+(.+)$',
        text,
        re.MULTILINE
    ):

        heading = normalize_heading(
            match.group(2)
        )

        if is_real_section_heading(
            heading
        ):

            matches.append(
                (
                    match.start(),
                    match.end(),
                    heading
                )
            )


    # -----------------------------------------------------
    # NO HEADINGS
    # -----------------------------------------------------

    if not matches:

        page_segments.append({

            "page_number":
                page_number,

            "section":
                current_section,

            "text":
                text,

            "source_doc_id":
                str(
                    getattr(
                        doc,
                        "id_",
                        ""
                    )
                ),

        })

        continue


    # -----------------------------------------------------
    # TEXT BEFORE FIRST HEADING
    # -----------------------------------------------------

    if matches[0][0] > 0:

        prefix = text[
            :matches[0][0]
        ].strip()

        if prefix:

            page_segments.append({

                "page_number":
                    page_number,

                "section":
                    current_section,

                "text":
                    prefix,

                "source_doc_id":
                    str(
                        getattr(
                            doc,
                            "id_",
                            ""
                        )
                    ),

            })


    # -----------------------------------------------------
    # BUILD SECTIONS
    # -----------------------------------------------------

    for j, (
        start,
        end,
        heading
    ) in enumerate(matches):

        current_section = heading

        if j + 1 < len(matches):

            next_start = (
                matches[j + 1][0]
            )

        else:

            next_start = len(text)


        segment_text = text[
            start:next_start
        ].strip()


        if segment_text:

            page_segments.append({

                "page_number":
                    page_number,

                "section":
                    current_section,

                "text":
                    segment_text,

                "source_doc_id":
                    str(
                        getattr(
                            doc,
                            "id_",
                            ""
                        )
                    ),

            })


print(
    "Section/page segments:",
    len(page_segments)
)


# =========================================================
# 9. CHUNKING
# =========================================================

print("\n" + "=" * 60)
print("CHUNKING")
print("=" * 60)

splitter = SentenceSplitter(

    chunk_size=CHUNK_SIZE,

    chunk_overlap=CHUNK_OVERLAP

)


cleaned_chunks = []


for segment in page_segments:

    temp_doc = LlamaDocument(
        text=segment["text"]
    )

    nodes = (
        splitter.get_nodes_from_documents(
            [temp_doc]
        )
    )


    for node in nodes:

        text = clean_text(
            node.text
        )

        if not text:
            continue


        cleaned_chunks.append({

            "text":
                text,

            "document":
                "WHO Medication Safety in Polypharmacy",

            "source_doc_id":
                segment[
                    "source_doc_id"
                ],

            "section":
                segment[
                    "section"
                ],

            "page_number":
                segment[
                    "page_number"
                ],

            "source_pdf":
                os.path.basename(
                    PDF_PATH
                ),

        })


print(
    "Total chunks:",
    len(cleaned_chunks)
)


# =========================================================
# 10. CREATE STABLE CHUNK IDS
# =========================================================

for i, chunk in enumerate(
    cleaned_chunks
):

    chunk["chunk_id"] = (

        f"who-2019-"

        f"p{chunk['page_number']:03d}-"

        f"chunk{i:04d}"

    )


print(
    "Chunk IDs created."
)


# =========================================================
# 11. LOAD EMBEDDING MODEL
# =========================================================

print("\n" + "=" * 60)
print("LOADING EMBEDDING MODEL")
print("=" * 60)

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)

print(
    "Embedding model loaded:",
    EMBEDDING_MODEL_NAME
)


# =========================================================
# 12. CREATE EMBEDDINGS
# =========================================================

print("\n" + "=" * 60)
print("CREATING EMBEDDINGS")
print("=" * 60)

texts = [

    chunk["text"]

    for chunk in cleaned_chunks

]


embeddings = embedding_model.encode(

    texts,

    normalize_embeddings=True,

    show_progress_bar=True

)


print(
    "Embedding shape:",
    embeddings.shape
)


# =========================================================
# 13. CONNECT TO CHROMADB
# =========================================================

print("\n" + "=" * 60)
print("CONNECTING TO CHROMADB")
print("=" * 60)

client = chromadb.PersistentClient(

    path=CHROMA_PATH

)


collection = client.get_or_create_collection(

    name=COLLECTION_NAME

)


print(
    "Collection:",
    collection.name
)

print(
    "Existing documents:",
    collection.count()
)


# =========================================================
# 14. PREPARE IDS
# =========================================================

ids = [

    chunk["chunk_id"]

    for chunk in cleaned_chunks

]


# =========================================================
# 15. PREPARE METADATA
# =========================================================

metadatas = [

    {

        "document":
            chunk["document"],

        "source_doc_id":
            str(
                chunk[
                    "source_doc_id"
                ] or ""
            ),

        "section":
            chunk["section"],

        "page_number":
            int(
                chunk[
                    "page_number"
                ]
            ),

        "source_pdf":
            chunk["source_pdf"],

    }

    for chunk in cleaned_chunks

]


# =========================================================
# 16. SAVE TO CHROMADB
# =========================================================

print("\n" + "=" * 60)
print("SAVING TO CHROMADB")
print("=" * 60)

collection.upsert(

    ids=ids,

    documents=texts,

    embeddings=embeddings.tolist(),

    metadatas=metadatas,

)


# =========================================================
# 17. FINAL VALIDATION
# =========================================================

print("\n" + "=" * 60)
print("DATABASE CREATED SUCCESSFULLY")
print("=" * 60)

print(
    "PDF:",
    os.path.basename(
        PDF_PATH
    )
)

print(
    "Collection:",
    collection.name
)

print(
    "Total chunks:",
    collection.count()
)

print(
    "ChromaDB location:",
    CHROMA_PATH
)

print("=" * 60)