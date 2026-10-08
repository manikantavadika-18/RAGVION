# rag/embeddings.py

from google import genai
from google.genai import errors

from config import GEMINI_API_KEY


client = genai.Client(
    api_key=GEMINI_API_KEY
)


# Try the current embedding model first.
# gemini-embedding-001 is kept as fallback.
EMBEDDING_MODELS = [
    "gemini-embedding-2",
    "gemini-embedding-001",
]


ACTIVE_EMBEDDING_MODEL = None


def _get_embedding(text, task_type=None):

    global ACTIVE_EMBEDDING_MODEL

    if not text or not text.strip():
        raise ValueError(
            "Cannot create embedding for empty text."
        )


    # If a model already worked, use it first.
    models = list(EMBEDDING_MODELS)

    if ACTIVE_EMBEDDING_MODEL in models:

        models.remove(
            ACTIVE_EMBEDDING_MODEL
        )

        models.insert(
            0,
            ACTIVE_EMBEDDING_MODEL
        )


    last_error = None


    for model in models:

        try:

            print(
                f"🔢 Embedding model: {model}"
            )


            config = None


            if task_type:

                from google.genai import types

                config = types.EmbedContentConfig(
                    task_type=task_type
                )


            if config:

                response = client.models.embed_content(
                    model=model,
                    contents=text,
                    config=config
                )

            else:

                response = client.models.embed_content(
                    model=model,
                    contents=text
                )


            if not response:

                raise ValueError(
                    f"{model} returned no response."
                )


            if not response.embeddings:

                raise ValueError(
                    f"{model} returned no embeddings."
                )


            embedding = response.embeddings[0].values


            if not embedding:

                raise ValueError(
                    f"{model} returned an empty vector."
                )


            ACTIVE_EMBEDDING_MODEL = model


            print(
                f"✅ Embedding created using {model}"
            )


            return embedding


        except errors.APIError as error:

            last_error = error

            code = getattr(
                error,
                "code",
                None
            )


            print(
                f"❌ Embedding model {model} "
                f"failed: {code}"
            )


            if code == 404:

                print(
                    f"⏭️ {model} is unavailable. "
                    f"Trying next embedding model..."
                )

                continue


            if code == 429:

                print(
                    f"⚠️ {model} quota/rate limit reached."
                )

                continue


            if code == 503:

                print(
                    f"⚠️ {model} temporarily unavailable."
                )

                continue


            raise


        except Exception as error:

            last_error = error

            print(
                f"❌ Embedding error: "
                f"{type(error).__name__}: {error}"
            )


    if last_error:

        raise last_error


    raise RuntimeError(
        "No Gemini embedding model is available."
    )


def embed_documents(texts):

    if not texts:

        return []


    embeddings = []


    for index, text in enumerate(texts):

        if not text or not text.strip():

            continue


        print(
            f"🔢 Creating document embedding "
            f"{index + 1}/{len(texts)}"
        )


        embedding = _get_embedding(
            text,
            task_type="RETRIEVAL_DOCUMENT"
        )


        embeddings.append(
            embedding
        )


    if not embeddings:

        raise ValueError(
            "No valid document embeddings were created."
        )


    return embeddings


def embed_query(text):

    if not text or not text.strip():

        return []


    return _get_embedding(
        text,
        task_type="RETRIEVAL_QUERY"
    )