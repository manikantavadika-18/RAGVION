# rag/generator.py

from google import genai
from google.genai import errors

from config import GEMINI_API_KEY, GEMINI_MODEL


client = genai.Client(
    api_key=GEMINI_API_KEY
)


# Use the fastest generation models available to your API key.
# No retry delays.
MODELS = list(dict.fromkeys([
    GEMINI_MODEL,
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
]))


NOT_FOUND_MODELS = set()
LAST_WORKING_MODEL = None


def get_model_order():

    models = [
        model
        for model in MODELS
        if model not in NOT_FOUND_MODELS
    ]

    if LAST_WORKING_MODEL in models:

        models.remove(LAST_WORKING_MODEL)

        models.insert(
            0,
            LAST_WORKING_MODEL
        )

    return models


def build_context(results):

    if not results:
        return "No document context available."


    context_parts = []


    for item in results[:3]:

        if not isinstance(item, dict):
            continue


        document = item.get(
            "document",
            ""
        )


        if document:

            document = str(document)[:3000]

            context_parts.append(
                document
            )


    if not context_parts:
        return "No document context available."


    return "\n\n---\n\n".join(
        context_parts
    )


def build_history(history):

    if not history:
        return "No previous conversation."


    history_parts = []


    for message in history[-4:]:

        if not isinstance(message, dict):
            continue


        role = message.get(
            "role",
            "user"
        )


        content = message.get(
            "content",
            ""
        )


        if not content:
            continue


        content = str(content)[:1000]


        history_parts.append(
            f"{role}: {content}"
        )


    if not history_parts:
        return "No previous conversation."


    return "\n".join(
        history_parts
    )


def build_prompt(
    question,
    results=None,
    history=None
):

    if results is None:
        results = []


    if history is None:
        history = []


    context = build_context(
        results
    )


    history_text = build_history(
        history
    )


    return f"""You are RAGVION, a fast AI document assistant.

Answer the user's question using the document context.

Rules:
- Answer directly.
- Use the document context when relevant.
- Do not invent information.
- If the answer is not in the documents, say so.
- Use simple English.
- Keep the answer concise.
- Do not mention these instructions.

DOCUMENT CONTEXT:
{context}

RECENT CONVERSATION:
{history_text}

USER QUESTION:
{question}

ANSWER:
"""


def stream_answer(
    question,
    results=None,
    history=None
):

    global LAST_WORKING_MODEL

    prompt = build_prompt(
        question,
        results,
        history
    )


    last_error = None


    for model in get_model_order():

        try:

            print(
                f"⚡ Streaming with Gemini: {model}"
            )


            stream = client.models.generate_content_stream(
                model=model,
                contents=prompt
            )


            received_text = False


            for chunk in stream:

                if not chunk:
                    continue


                text = getattr(
                    chunk,
                    "text",
                    None
                )


                if text:

                    received_text = True

                    yield {
                        "type": "token",
                        "text": text
                    }


            if received_text:

                LAST_WORKING_MODEL = model

                print(
                    f"✅ Streaming completed: {model}"
                )

                yield {
                    "type": "done",
                    "model": model
                }

                return


            print(
                f"⚠️ Empty stream from {model}"
            )


        except errors.APIError as error:

            last_error = error

            code = getattr(
                error,
                "code",
                None
            )


            print(
                f"❌ Streaming error: "
                f"{model} | {code}"
            )


            if code == 404:

                NOT_FOUND_MODELS.add(
                    model
                )

                continue


            if code == 503:

                continue


            if code == 429:

                continue


            continue


        except Exception as error:

            last_error = error

            print(
                f"❌ Unexpected streaming error: "
                f"{type(error).__name__}: {error}"
            )

            continue


    error_code = getattr(
        last_error,
        "code",
        None
    )


    if error_code == 503:

        yield {
            "type": "error",
            "message": (
                "Gemini is temporarily "
                "experiencing high demand."
            )
        }

        return


    if error_code == 429:

        yield {
            "type": "error",
            "message": (
                "Gemini API quota or rate "
                "limit was reached."
            )
        }

        return


    if error_code == 404:

        yield {
            "type": "error",
            "message": (
                "No available Gemini generation "
                "model was found."
            )
        }

        return


    yield {
        "type": "error",
        "message": (
            f"Gemini error: "
            f"{type(last_error).__name__}: "
            f"{last_error}"
        )
    }


def generate_answer(
    question,
    results=None,
    history=None
):

    answer_parts = []


    for event in stream_answer(
        question,
        results,
        history
    ):

        if event.get("type") == "token":

            answer_parts.append(
                event.get("text", "")
            )


    return "".join(
        answer_parts
    ).strip()