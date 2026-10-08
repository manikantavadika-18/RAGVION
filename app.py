# app.py

import os
import json
import traceback

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    Response,
    stream_with_context
)

from dotenv import load_dotenv

from rag.ingest import ingest_file
from rag.retriever import retrieve
from rag.generator import stream_answer
from rag.vector_store import (
    get_collection,
    clear_collection
)
from synthetic.generator import generate_synthetic_qa


load_dotenv()


app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = (
    25 * 1024 * 1024
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx"
}


@app.route("/")
def index():

    return render_template(
        "index.html"
    )


@app.get("/api/health")
def health():

    try:

        count = get_collection().count()

        return jsonify({
            "status": "ok",
            "documents": count
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.post("/api/upload")
def upload():

    if "file" not in request.files:

        return jsonify({
            "error": "No file was uploaded."
        }), 400


    file = request.files["file"]


    if not file.filename:

        return jsonify({
            "error": "Please choose a file."
        }), 400


    ext = os.path.splitext(
        file.filename
    )[1].lower()


    if ext not in ALLOWED_EXTENSIONS:

        return jsonify({
            "error": (
                "Only PDF, TXT and DOCX "
                "files are supported."
            )
        }), 400


    try:

        result = ingest_file(file)

        return jsonify(result)


    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500


@app.post("/api/chat")
def chat():

    try:

        data = request.get_json(
            silent=True
        ) or {}


        message = (
            data.get("message") or ""
        ).strip()


        history = (
            data.get("history") or []
        )


        if not message:

            return jsonify({
                "error": "Message cannot be empty."
            }), 400


        # Retrieve only 3 chunks for speed.
        results = retrieve(
            message,
            top_k=3
        )


        if results is None:

            results = []


        sources = []


        for item in results:

            if not isinstance(
                item,
                dict
            ):

                continue


            score = item.get(
                "score"
            )


            if score is not None:

                try:

                    score = round(
                        float(score),
                        4
                    )

                except Exception:

                    pass


            sources.append({
                "filename": item.get(
                    "filename",
                    "Unknown"
                ),
                "page": item.get(
                    "page"
                ),
                "score": score
            })


        @stream_with_context
        def generate():

            try:

                # Send sources immediately.
                yield (
                    "data: "
                    + json.dumps({
                        "type": "sources",
                        "sources": sources
                    })
                    + "\n\n"
                )


                # Stream Gemini tokens.
                for event in stream_answer(
                    message,
                    results,
                    history
                ):

                    yield (
                        "data: "
                        + json.dumps(event)
                        + "\n\n"
                    )


            except Exception as error:

                traceback.print_exc()


                yield (
                    "data: "
                    + json.dumps({
                        "type": "error",
                        "message": str(error)
                    })
                    + "\n\n"
                )


        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive"
            }
        )


    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500


@app.post("/api/synthetic")
def synthetic():

    data = request.get_json(
        silent=True
    ) or {}


    try:

        count = int(
            data.get(
                "count",
                5
            )
        )

    except Exception:

        count = 5


    count = max(
        1,
        min(
            count,
            20
        )
    )


    try:

        results = generate_synthetic_qa(
            count
        )

        return jsonify({
            "items": results
        })


    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


@app.post("/api/clear")
def clear():

    try:

        clear_collection()

        return jsonify({
            "message": "Knowledge base cleared."
        })


    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({
            "error": "API endpoint not found.",
            "path": request.path,
            "method": request.method
        }), 404


    return (
        "404 Not Found",
        404
    )


@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({
        "error": "Method not allowed.",
        "path": request.path,
        "method": request.method
    }), 405


if __name__ == "__main__":

    print("")
    print("=" * 60)
    print("🚀 RAGVION FAST STREAMING SERVER")
    print("=" * 60)
    print("🌐 http://127.0.0.1:5000")
    print("❤️  /api/health")
    print("📤 /api/upload")
    print("💬 /api/chat")
    print("=" * 60)
    print("")


    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000,
        threaded=True
    )