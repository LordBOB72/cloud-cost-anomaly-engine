import asyncio
import logging
from threading import Thread

log = logging.getLogger(__name__)


def start_scheduler():
    thread = Thread(target=_run_loop, daemon=True)
    thread.start()


def _run_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_schedule())


async def _schedule():
    import time
    from app.ingestion.pipeline import run_ingestion
    from app.anomaly.detector import run_detection

    while True:
        now = time.localtime()
        # run at 02:00 local time every day
        seconds_until_2am = (
            ((2 - now.tm_hour) % 24) * 3600
            - now.tm_min * 60
            - now.tm_sec
        )
        if seconds_until_2am <= 0:
            seconds_until_2am += 86400

        log.info("next ingestion in %.0f minutes", seconds_until_2am / 60)
        await asyncio.sleep(seconds_until_2am)

        try:
            await run_ingestion()
            await run_detection()
        except Exception as e:
            log.error("scheduled run failed: %s", e)
