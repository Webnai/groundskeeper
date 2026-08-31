"""Shared generation step: produces the exact same frozen dataset both the
baseline and the agent are evaluated against.

This exists as its own module (rather than being inlined into
`scripts/generate.py`) specifically so both comparison arms are guaranteed
to run against identical input — the hackathon brief's own fairness
requirement ("keep the comparison fair by giving the baseline and final
solution the same task and evaluation cases") is enforced by construction,
not by hoping two separate invocations happen to agree.

Chunk size is set deliberately small (150 tokens, vs. training_data_bot's
own default of 800) — these source documents are short policy/FAQ pages
where each paragraph covers one or two distinct facts. A large chunk would
let a grounding check "succeed" by matching against a broad passage that
contains many facts, only one of which the answer is actually about. Small,
precise chunks make the grounding check mean something.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from training_data_bot.core.logging import get_logger
from training_data_bot.models import Document, TaskType, TextChunk, TrainingExample
from training_data_bot.preprocessing import TextPreprocessor
from training_data_bot.sources import UnifiedLoader
from training_data_bot.tasks import TaskManager

from .ai_backends import get_ai_client
from .corruption import LabeledExample, inject_corruption

SOURCE_DOCS_DIR = Path(__file__).parent.parent.parent / "data" / "source_docs"
CHUNK_SIZE_TOKENS = 150
CHUNK_OVERLAP_TOKENS = 20

logger = get_logger("groundskeeper.pipeline")


async def generate_labeled_dataset(
    corruption_rate: float = 0.4,
    seed: int = 7,
    source_dir: Path | None = None,
) -> tuple[list[LabeledExample], dict[UUID, str], list[Document]]:
    """Load source docs, chunk, generate QA examples, inject known corruption.

    `source_dir` defaults to this project's own synthetic policy docs
    (`SOURCE_DOCS_DIR`) — pass any other directory to audit a different
    document set (e.g. a sibling project's own data) without touching the
    frozen PTO/rate-limits evidence this repo's submission docs reference.

    Returns (labeled_examples, source_lookup, documents) where source_lookup
    maps a chunk id (or document id, for chunks that don't survive — see
    note below) to the exact source text that chunk's examples were
    generated from.
    """
    loader = UnifiedLoader()
    documents = await loader.load_directory(source_dir or SOURCE_DOCS_DIR)
    logger.info("Loaded %d source document(s)", len(documents))

    preprocessor = TextPreprocessor(
        chunk_size_tokens=CHUNK_SIZE_TOKENS, chunk_overlap_tokens=CHUNK_OVERLAP_TOKENS
    )
    chunks: list[TextChunk] = await preprocessor.chunk_documents(documents)
    logger.info("Split into %d chunk(s)", len(chunks))

    source_lookup: dict[UUID, str] = {chunk.id: chunk.content for chunk in chunks}
    # Fall back to whole-document text for any example whose chunk id somehow
    # isn't in the lookup (shouldn't happen in practice, but a missing source
    # text would silently make every grounding check fail for the wrong reason).
    for document in documents:
        source_lookup.setdefault(document.id, document.content)

    ai_client = get_ai_client()
    try:
        task_manager = TaskManager(ai_client, max_concurrency=4)
        examples: list[TrainingExample] = await task_manager.run(chunks, [TaskType.QA_GENERATION])
        logger.info("Generated %d raw training example(s)", len(examples))
    finally:
        await ai_client.close()

    labeled = inject_corruption(examples, corruption_rate=corruption_rate, seed=seed)
    n_corrupted = sum(1 for item in labeled if item.label == "corrupted")
    logger.info(
        "Labeled dataset: %d clean, %d corrupted (rate=%.2f)",
        len(labeled) - n_corrupted,
        n_corrupted,
        corruption_rate,
    )
    return labeled, source_lookup, documents
