import asyncio
import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableSerializable
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from ...models.tools import (
    IngredientInput,
    NutriFacts,
    NutritionResult,
    ProcessedItem,
    RecipeAnalysisInput,
)


# ResourceLoader for RAG
class ResourceLoader:
    """
    Async singleton for managing connections.
    Centralizes configuration validation.
    Uses asyncio.to_thread to avoid blocking the event loop during init.
    """

    _retriever = None
    _extractor_llm = None
    _retriever_lock = asyncio.Lock()
    _extractor_lock = asyncio.Lock()

    @staticmethod
    def _validate_env_vars() -> None:
        """Validates critical credentials exist before connecting."""
        required_vars = ["PINECONE_API_KEY", "OPENAI_API_KEY", "PINECONE_INDEX_NAME"]
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            raise ConnectionError(
                f"""Missing configuration in Worker environment:
                 {", ".join(missing)}. """
                "Ensure environment variables are loaded."
            )

    @staticmethod
    def _init_retriever_sync() -> Any:
        """Blocking init — runs in thread pool via asyncio.to_thread."""
        ResourceLoader._validate_env_vars()
        index_name = os.getenv("PINECONE_INDEX_NAME", "")
        embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        try:
            embeddings = OpenAIEmbeddings(model=embedding_model)

            vector_store = PineconeVectorStore.from_existing_index(
                index_name=index_name, embedding=embeddings
            )
            return vector_store.as_retriever(search_kwargs={"k": 1})

        except Exception as e:
            raise ConnectionError(  # noqa: B904
                f"Error initializing Pinecone connection: {str(e)}"
            )

    @staticmethod
    def _init_extractor_sync() -> RunnableSerializable[dict, Any]:
        """Blocking init — runs in thread pool via asyncio.to_thread."""
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        prompt = ChatPromptTemplate.from_template(
            """Analyze the context. Extract data for: '{ingredient_name}'.
            Context: {context}
            If no match, return 0 and explain in notes."""
        )
        return prompt | llm.with_structured_output(NutriFacts)

    @classmethod
    async def get_retriever(cls) -> Any:
        """Get or create Pinecone retriever singleton (async, non-blocking)."""
        if cls._retriever is None:
            async with cls._retriever_lock:
                if cls._retriever is None:
                    cls._retriever = await asyncio.to_thread(cls._init_retriever_sync)
        return cls._retriever

    @classmethod
    async def get_extractor_chain(cls) -> RunnableSerializable[dict, Any]:
        """Get or create extraction chain singleton (async, non-blocking)."""
        if cls._extractor_llm is None:
            async with cls._extractor_lock:
                if cls._extractor_llm is None:
                    cls._extractor_llm = await asyncio.to_thread(
                        cls._init_extractor_sync
                    )
        return cls._extractor_llm


_pinecone_semaphore = asyncio.Semaphore(2)
_TRANSIENT_ERRORS = ("Session is closed", "Connection reset", "TimeoutError")
_MAX_RETRIES = 3
_BASE_DELAY = 0.5


async def _process_ingredient_task(ing: IngredientInput) -> ProcessedItem:
    """Atomic work unit for an ingredient with retry and concurrency control."""
    last_error: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            retriever = await ResourceLoader.get_retriever()
            extractor = await ResourceLoader.get_extractor_chain()

            # 1. Retrieval (concurrency-limited to protect Pinecone session)
            async with _pinecone_semaphore:
                docs = await retriever.ainvoke(ing.nombre)

            if not docs:
                return ProcessedItem(
                    input_name=ing.nombre,
                    matched_db_name="MISSING",
                    total_kcal=0,
                    notes="Not found in Knowledge Base.",
                )

            # 2. Extraction
            raw_data = await extractor.ainvoke(
                {"ingredient_name": ing.nombre, "context": docs[0].page_content}
            )

            # 3. Calculation
            factor = ing.peso_gramos / 100.0
            return ProcessedItem(
                input_name=ing.nombre,
                matched_db_name=raw_data.food_name,
                total_kcal=round(raw_data.calories_100g * factor, 1),
                notes=raw_data.notes,
            )

        except Exception as e:
            last_error = e
            is_transient = any(msg in str(e) for msg in _TRANSIENT_ERRORS)
            if is_transient and attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(_BASE_DELAY * (2**attempt))
                continue
            break

    return ProcessedItem(
        input_name=ing.nombre,
        matched_db_name="ERROR",
        total_kcal=0,
        notes=f"Internal exception: {str(last_error)}",
    )


@tool("calculate_recipe_nutrition", args_schema=RecipeAnalysisInput)  # type: ignore [misc]
async def calculate_recipe_nutrition(
    ingredientes: list[IngredientInput],
    _config: RunnableConfig | None = None,
) -> Any:
    """
    Queries the knowledge base (RAG) to obtain precise
    and consolidated nutritional values.

    Use this tool when you have the definitive list of ingredients
    and their weights from the plan.
    Performs vector search, scales values to the indicated weight,
    and reports substitutions or warnings if there's no exact match.
    """
    # Fail-fast if infrastructure doesn't respond
    try:
        await ResourceLoader.get_retriever()
    except ConnectionError as e:
        return {"system_error": str(e), "status": "failed"}

    # Parallel execution (Worker behavior)
    tasks = [_process_ingredient_task(ing) for ing in ingredientes]
    results = await asyncio.gather(*tasks)

    # Result consolidation
    clean_items = []
    total_kcal = 0.0
    warnings = []

    for item in results:
        clean_items.append(item)
        total_kcal += item.total_kcal

        if item.matched_db_name in ["MISSING", "ERROR"]:
            warnings.append(f"[{item.input_name}]: {item.notes}")

    output = NutritionResult(
        processed_items=clean_items,
        total_recipe_kcal=round(total_kcal, 1),
        warnings=" | ".join(warnings) if warnings else None,
    )

    return output.model_dump()
