"""Internship Report Reviewer — application entry point.

A student finishes a placement and emails three PDFs: their internship report,
the employer's evaluation form, and an attendance record. This service reads
them, checks them against each other, and either tells the student exactly what
to correct or puts the package in front of a coordinator to sign.

Deterministic checks decide the outcome. The language model reads the report
and raises questions for the coordinator, and drafts the student's email — it
runs after the status is already fixed, and the service decides identically
with it switched off. See app/services/report_verification.py.
"""

from dotenv import load_dotenv

# Load .env so LLM_API_KEY reaches the OpenAI-compatible SDK, which reads
# os.environ directly — pydantic-settings does not populate it.
load_dotenv()

import logging

from app.core.logging_config import setup_logging

setup_logging()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import reports
from app.services import report_repository, report_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    report_repository.init_db()

    # The originality index lives in memory. Rebuilding it from the accepted
    # submissions on disk is what stops a restart from amnestying a report
    # copied from one accepted last week.
    indexed = report_service.load_corpus()
    logger.info("Originality index loaded with %d accepted report(s)", indexed)

    yield


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=__doc__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Backend is running"}


@app.get("/health")
def health_check():
    from app.core.health import get_health

    return get_health()


app.include_router(reports.router)
