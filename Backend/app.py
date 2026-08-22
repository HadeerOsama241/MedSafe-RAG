from flask import Flask, request, jsonify
from flask_cors import CORS

from rag import (
    run_pipeline,
    collection,
    OLLAMA_MODEL,
    RELEVANCE_TOP_K,
    DISTANCE_REFUSAL_THRESHOLD
)


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

# Allow requests from local React frontend
CORS(app)


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({

        "message":
            "HealthInsight RAG Backend is running",

        "status":
            "success",

        "service":
            "HealthInsight RAG",

        "database":
            "ChromaDB Cloud",

        "collection":
            collection.name,

        "documents":
            collection.count(),

        "embedding_model":
            "sentence-transformers/all-MiniLM-L6-v2",

        "llm":
            f"Ollama - {OLLAMA_MODEL}",

        "top_k":
            RELEVANCE_TOP_K,

        "distance_threshold":
            DISTANCE_REFUSAL_THRESHOLD,

        "chat_endpoint":
            "/api/chat",

        "health_endpoint":
            "/api/health"
    })


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():

    try:

        return jsonify({

            "status":
                "ok",

            "service":
                "HealthInsight RAG",

            "database":
                "connected",

            "collection":
                collection.name,

            "documents":
                collection.count(),

            "embedding_model":
                "sentence-transformers/all-MiniLM-L6-v2",

            "llm":
                "Ollama",

            "model":
                OLLAMA_MODEL,

            "top_k":
                RELEVANCE_TOP_K,

            "distance_threshold":
                DISTANCE_REFUSAL_THRESHOLD
        })

    except Exception as e:

        return jsonify({

            "status":
                "error",

            "service":
                "HealthInsight RAG",

            "database":
                "error",

            "error":
                str(e)

        }), 500


# =========================================================
# CHAT
# =========================================================

@app.route("/api/chat", methods=["POST"])
def chat():

    try:

        # -------------------------------------------------
        # GET JSON
        # -------------------------------------------------

        data = request.get_json(silent=True)

        if not data:

            return jsonify({

                "error":
                    "JSON body is required"

            }), 400

        # -------------------------------------------------
        # GET QUESTION
        #
        # Accept both:
        # {
        #   "question": "..."
        # }
        #
        # and:
        #
        # {
        #   "message": "..."
        # }
        # -------------------------------------------------

        question = data.get("question")

        if question is None:
            question = data.get("message", "")

        # -------------------------------------------------
        # VALIDATE QUESTION
        # -------------------------------------------------

        if not isinstance(question, str):

            return jsonify({

                "error":
                    "Question must be a string"

            }), 400

        question = question.strip()

        if not question:

            return jsonify({

                "error":
                    "Question is required"

            }), 400

        # -------------------------------------------------
        # LOG QUESTION
        # -------------------------------------------------

        print("\n====================================")
        print("HealthInsight RAG - New Question")
        print("====================================")
        print("Question:", question)

        # -------------------------------------------------
        # RUN RAG
        # -------------------------------------------------

        result = run_pipeline(question)

        # -------------------------------------------------
        # LOG RESPONSE
        # -------------------------------------------------

        print("\nRAG Response")
        print("------------------------------------")

        print(
            "Confidence:",
            result.get("confidence", "unknown")
        )

        print(
            "Refused:",
            result.get("refused", False)
        )

        print(
            "Top distance:",
            result.get("top_distance", "N/A")
        )

        results = result.get("results", [])

        print(
            "Results:",
            len(results)
        )

        # -------------------------------------------------
        # PRINT RETRIEVED RESULTS
        # -------------------------------------------------

        for index, item in enumerate(
            results,
            start=1
        ):

            print(
                f"#{index} | "
                f"Page: {item.get('page', 'N/A')} | "
                f"Section: {item.get('section', 'N/A')} | "
                f"Distance: {item.get('distance', 'N/A')} | "
                f"Similarity: {item.get('similarity_percent', 'N/A')}%"
            )

        # -------------------------------------------------
        # RETURN RAG RESULT
        # -------------------------------------------------

        return jsonify(result), 200

    except Exception as e:

        print("\n====================================")
        print("ERROR")
        print("====================================")
        print(str(e))

        return jsonify({

            "error":
                "An error occurred while processing the question.",

            "details":
                str(e)

        }), 500


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "error":
            "Endpoint not found",

        "available_endpoints": [
            "/",
            "/api/health",
            "/api/chat"
        ]

    }), 404


@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "error":
            "HTTP method not allowed"

    }), 405


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    print("\n====================================")
    print("       HealthInsight RAG Backend")
    print("====================================")

    print("Database: ChromaDB Cloud")

    print(
        f"Collection: {collection.name}"
    )

    print(
        f"Documents: {collection.count()}"
    )

    print(
        "Embedding: "
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    print(
        f"Top K: {RELEVANCE_TOP_K}"
    )

    print(
        f"Distance Threshold: "
        f"{DISTANCE_REFUSAL_THRESHOLD}"
    )

    print(
        f"LLM: Ollama - {OLLAMA_MODEL}"
    )

    print(
        "URL: http://127.0.0.1:5000"
    )

    print(
        "Chat endpoint: "
        "http://127.0.0.1:5000/api/chat"
    )

    print(
        "Health endpoint: "
        "http://127.0.0.1:5000/api/health"
    )

    print("====================================")
    print("Server is ready.")
    print("Press CTRL+C to stop.")
    print("====================================\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )