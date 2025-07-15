import asyncio
import random
import time

import aiohttp
from loguru import logger

from app.config import API_IP, API_PORT



URL = f"http://{API_IP}:{API_PORT}/new-transaction"
HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "x-token": "123"
}

request_counter = 0

def generate_transaction():
    """
    Generate a random transaction dict with sender_id, receiver_id and amount.
    """
    return {
        "sender_id": random.randint(1, 10),
        "receiver_id": random.randint(1, 10),
        "amount": round(random.uniform(1, 100), 2)
    }

async def send_transaction(session: aiohttp.ClientSession):
    """
    Send a transaction request to the specified URL.
    Increment the global counter if the request is successful.
    """
    global request_counter
    data = generate_transaction()
    try:
        async with session.post(URL, json=data, headers=HEADERS) as response:
            await response.text()
            if response.status == 200:
                request_counter += 1
    except Exception as e:
        logger.error(f"Request failed: {e}")

async def log_metrics():
    """
    Periodically log the number of successful requests every 10 seconds.
    Reset the counter after logging.
    """
    global request_counter
    while True:
        await asyncio.sleep(10)
        logger.info(f"Sent {request_counter} successful requests in the last 10 seconds.")
        request_counter = 0

async def stress_test(session: aiohttp.ClientSession):
    """
    Continuously send bursts of 100 transaction requests per second.
    Adjust sleep time to maintain roughly 1-second intervals.
    """
    while True:
        start = time.perf_counter()
        tasks = [send_transaction(session) for _ in range(100)]
        await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start
        await asyncio.sleep(max(0, 1.0 - elapsed))

async def main():
    """
    Run the stress test and metrics logger concurrently for 10 seconds,
    then gracefully cancel both tasks.
    """
    logger.info("Starting stress test for 10 seconds...")
    async with aiohttp.ClientSession() as session:
        stress_task = asyncio.create_task(stress_test(session))
        metrics_task = asyncio.create_task(log_metrics())

        await asyncio.sleep(10)

        stress_task.cancel()
        metrics_task.cancel()

        try:
            await stress_task
        except asyncio.CancelledError:
            logger.info("Stress test stopped.")

        try:
            await metrics_task
        except asyncio.CancelledError:
            logger.info("Metrics logging stopped.")

if __name__ == "__main__":
    asyncio.run(main())
