import asyncio
import logging
import random

logger = logging.getLogger(__name__)

# Simulated transcription snippets
MOCK_TRANSCRIPTIONS = [
    "Welcome to today's podcast. We'll be discussing the latest trends in artificial intelligence and how they impact everyday life.",
    "In this recording, the speaker talks about climate change and its effects on coastal communities around the world.",
    "The meeting covered quarterly sales figures, upcoming product launches, and the new marketing strategy for Q3.",
    "This is a lecture on data structures, specifically covering binary trees, hash maps, and graph traversal algorithms.",
    "The interview discusses the candidate's experience with distributed systems, microservices architecture, and cloud deployments.",
]

MOCK_KEYWORD_SETS = [
    ["artificial intelligence", "trends", "technology", "podcast"],
    ["climate change", "coastal", "environment", "communities"],
    ["sales", "product launch", "marketing", "quarterly review"],
    ["data structures", "algorithms", "binary trees", "hash maps"],
    ["distributed systems", "microservices", "cloud", "architecture"],
]

FAILURE_RATE = 0.15  # 15% chance of simulated failure


async def process_audio(file_path: str) -> dict:
    """
    Mock external audio processing service.
    Simulates network latency and occasional failures.
    Returns transcription and extracted keywords.
    """
    # simulate processing delay (1-3 seconds)
    delay = random.uniform(1.0, 3.0)
    logger.info(f"Processing audio file: {file_path} (simulated delay: {delay:.1f}s)")
    await asyncio.sleep(delay)

    # simulate occasional failures
    if random.random() < FAILURE_RATE:
        raise RuntimeError("External processor unavailable — connection timed out")

    idx = random.randint(0, len(MOCK_TRANSCRIPTIONS) - 1)
    return {
        "transcription": MOCK_TRANSCRIPTIONS[idx],
        "keywords": MOCK_KEYWORD_SETS[idx],
    }
