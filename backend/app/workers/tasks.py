import uuid
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.modules.generations.service import run_generation
from app.modules.publishing.service import run_publish


async def run_generation_task(ctx: dict[str, Any], request_id: str) -> None:
    del ctx
    with Session(engine) as session:
        run_generation(session, uuid.UUID(request_id))


async def enqueue_generation(request_id: uuid.UUID) -> None:
    if settings.TASKS_EAGER:
        with Session(engine) as session:
            run_generation(session, request_id)
        return
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    await redis.enqueue_job("run_generation_task", str(request_id))
    await redis.aclose()


async def publish_task(ctx: dict[str, Any], job_id: str) -> None:
    del ctx
    with Session(engine) as session:
        run_publish(session, uuid.UUID(job_id))


async def enqueue_publish(job_id: uuid.UUID) -> None:
    if settings.TASKS_EAGER:
        with Session(engine) as session:
            run_publish(session, job_id)
        return
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    await redis.enqueue_job("publish_task", str(job_id))
    await redis.aclose()


class WorkerSettings:
    functions = [run_generation_task, publish_task]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
