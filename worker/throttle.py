import asyncio
import random
from typing import Callable, TypeVar
import logging

T = TypeVar("T")

logger = logging.getLogger("rigradar.throttle")

DOMAIN_DELAY_SECONDS = 2.0
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0
MAX_JITTER_SECONDS = 2.0
BATCH_SIZE = 5

async def exponential_backoff_with_jitter(attempt: int) -> None:
    delay = BASE_BACKOFF_SECONDS * (2 ** attempt)
    jitter = random.uniform(0, MAX_JITTER_SECONDS)
    total_delay = delay + jitter
    logger.info(f"Backoff attempt {attempt + 1}: waiting {total_delay:.2f}s")
    await asyncio.sleep(total_delay)

async def throttled_request(
    func: Callable[..., T],
    *args,
    **kwargs,
) -> T:
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: func(*args, **kwargs)
            )
            return result
        except Exception as request_error:
            last_exception = request_error
            logger.warning(
                f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(request_error)}"
            )
            if attempt < MAX_RETRIES - 1:
                await exponential_backoff_with_jitter(attempt)

    raise last_exception

def group_items_by_domain(items: list[dict]) -> dict[str, list[dict]]:
    grouped = {}
    for item in items:
        store = item.get("store", "unknown")
        if store not in grouped:
            grouped[store] = []
        grouped[store].append(item)
    return grouped

async def process_domain_batch(
    domain_items: list[dict],
    processor: Callable[[dict], T],
) -> list[T]:
    results = []

    for index, item in enumerate(domain_items):
        if index > 0:
            inter_request_delay = DOMAIN_DELAY_SECONDS + random.uniform(0.5, 1.5)
            await asyncio.sleep(inter_request_delay)

        try:
            result = await throttled_request(processor, item)
            results.append(result)
        except Exception as processing_error:
            logger.error(
                f"Failed to process item {item.get('item_id', 'unknown')}: {str(processing_error)}"
            )
            results.append(None)

    return results

async def process_all_items(
    items: list[dict],
    processor: Callable[[dict], T],
) -> list[T]:
    grouped = group_items_by_domain(items)
    all_results = []

    domain_tasks = []
    for domain, domain_items in grouped.items():
        batches = [
            domain_items[i : i + BATCH_SIZE]
            for i in range(0, len(domain_items), BATCH_SIZE)
        ]
        for batch in batches:
            domain_tasks.append(process_domain_batch(batch, processor))

    batch_results = await asyncio.gather(*domain_tasks)

    for batch_result in batch_results:
        all_results.extend(batch_result)

    return all_results
