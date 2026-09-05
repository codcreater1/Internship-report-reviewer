"""End-of-internship report review API.

Anything acting on a specific submission takes its stable ``id`` under
``/by-id/``, never a list position: submissions arrive from n8n continuously
and the queue is newest-first, so an index captured when the dashboard loaded
points at a different student moments later — and a signature has to land on
the right one.

The route that matters is :func:`sign_certificate`. Everything else reports;
that one changes what the university has asserted about a student, so it is the
one with the interesting preconditions:

  * a **rejected** package can never be signed — no flag in the body changes
    that;
  * a package **held for clarification** can never be signed either — it must be
    corrected and resubmitted, and signing past a missing supervisor signature
    would produce a certificate resting on a document nobody signed;
  * a package at **pending** can be signed, but only with
    ``acknowledge_warnings``, and the acknowledged points are then printed on
    the certificate;
  * ``coordinator_name`` is required and rendered on the document.
"""

from __future__ import annotations

import base64
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import EmailStr

from app.core.config import settings
from app.core.exceptions import TaskNotFoundError
from app.core.report_constants import (
    STATUS_APPROVED,
    STATUS_CLARIFICATION,
    STATUS_PENDING,
    STATUS_REJECTED,
    STATUS_SIGNED,
)
from app.core.rules import rules
from app.core.security import require_api_key
from app.models.report import (
    ReportListItem,
    ReportSubmissionResponse,
    SignCertificateRequest,
)
from app.services import report_repository
from app.services.completion_certificate_service import CertificateService
from app.services.pdf_service import pdf_service
from app.services.report_service import Attachment, ReportService, report_service
from app.services.signature_image_service import SignatureImageService
from app.services.storage_service import storage_service
from app.services.token_service import create_download_token, verify_download_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


def get_report_service() -> ReportService:
    return report_service


def _require_by_id(submission_id: str) -> ReportSubmissionResponse:
    submission = report_repository.get_by_id(submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Report submission not found")
    return submission


async def _read_attachments(files: list[UploadFile]) -> list[Attachment]:
    """Read the uploads, refusing anything over the configured size limit."""
    attachments: list[Attachment] = []

    for upload in files:
        # Read one byte past the limit so an oversized file is detected without
        # buffering all of it.
        content = await upload.read(settings.max_pdf_bytes + 1)
        await upload.close()

        if len(content) > settings.max_pdf_bytes:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Attachment '{upload.filename}' exceeds the "
                    f"{settings.max_pdf_bytes // (1024 * 1024)} MB limit."
                ),
            )

        attachments.append(
            Attachment(filename=upload.filename or "unnamed.pdf", content=content)
        )

    return attachments


# --------------------------------------------------------------------------- #
# Intake
#
# Both intake routes hand the review to a worker thread. It is CPU work with
# blocking network calls inside it - PDF parsing, then up to four model calls -
# and awaiting nothing, so running it on the event loop stops the whole process
# for as long as one package takes: /health included, which is what a monitor
# reads to decide whether this service is alive. A slow review must be slow for
# one caller, not for every caller.
# --------------------------------------------------------------------------- #


@router.post("/", response_model=ReportSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_report_package(
    intern_email: EmailStr = Form(...),
    files: list[UploadFile] = File(...),
    application_id: str | None = Form(default=None),
    service: ReportService = Depends(get_report_service),
) -> ReportSubmissionResponse:
    """Review one submission: three PDFs and the address they came from.

    Attachment count is validated by the pipeline rather than here, so that
    "you sent two files, not three" comes back as an actionable finding in the
    student's email instead of an HTTP 422 the caller has to interpret.

    ``application_id`` is optional and opaque: a caller that already tracks the
    placement elsewhere can pass its own key and later fetch every attempt made
    against it. This service never resolves it.
    """
    return await run_in_threadpool(
        service.review,
        await _read_attachments(files),
        intern_email=str(intern_email),
        application_id=application_id,
    )


@router.post(
    "/from-n8n",
    response_model=ReportSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
async def submit_report_package_from_n8n(
    intern_email: EmailStr = Form(...),
    files: list[UploadFile] = File(...),
    application_id: str | None = Form(default=None),
    service: ReportService = Depends(get_report_service),
) -> ReportSubmissionResponse:
    """Same as POST /reports/, behind the shared n8n bearer token."""
    return await run_in_threadpool(
        service.review,
        await _read_attachments(files),
        intern_email=str(intern_email),
        application_id=application_id,
    )


# --------------------------------------------------------------------------- #
# Coordinator queue
# --------------------------------------------------------------------------- #


@router.get("/", response_model=list[ReportListItem])
def list_report_submissions(
    submission_status: str | None = Query(
        default=None,
        alias="status",
        description="Filter the queue, e.g. status=pending.",
    ),
) -> list[ReportListItem]:
    """The coordinator queue, newest first."""
    return [
        ReportListItem(
            id=s.id,
            created_at=s.created_at,
            student_name=s.student_name,
            student_id=s.student_id,
            company=s.company,
            status=s.status,
            counted_working_days=s.counted_working_days,
            evaluation_score=s.evaluation_score,
            clarification_count=len(s.clarifications),
            warning_count=len(s.warnings),
            signed_by=s.signed_by,
        )
        for s in report_repository.list_all(status=submission_status)
    ]


@router.get("/for-application/{application_id}", response_model=list[ReportSubmissionResponse])
def list_for_application(application_id: str) -> list[ReportSubmissionResponse]:
    """Every completion attempt made against one application, newest first.

    A student may be asked to correct something and resend; each attempt is its
    own row, and the dashboard shows the whole arc rather than only the latest.
    """
    return report_repository.list_for_application(application_id)


@router.get("/rules")
def get_rules() -> dict:
    """The thresholds this service is actually enforcing.

    The dashboard draws every figure against the line it is measured against,
    and a line it had hardcoded would keep drawing the old one after a
    department changed the file. Published rather than duplicated.
    """
    return rules.as_dict()


@router.get("/by-id/{submission_id}", response_model=ReportSubmissionResponse)
def get_report_submission(submission_id: str) -> ReportSubmissionResponse:
    return _require_by_id(submission_id)


@router.get("/by-id/{submission_id}/audit")
def get_report_audit(submission_id: str) -> list[dict]:
    """Everything recorded against one submission, oldest first.

    The submission itself only carries its current state — signing rewrites the
    row — so this is where "who signed this, when, and what did they take on"
    lives. A certificate is a claim about a real person and somebody will
    eventually ask how it came to be issued.
    """
    _require_by_id(submission_id)
    return report_repository.events_for(submission_id)


@router.delete("/by-id/{submission_id}", status_code=204)
def delete_report_submission(submission_id: str) -> None:
    if not report_repository.delete(submission_id):
        raise HTTPException(status_code=404, detail="Report submission not found")


@router.get("/by-id/{submission_id}/attachments/{role}")
def get_attachment(submission_id: str, role: str) -> FileResponse:
    """Serve one of the originally submitted documents for review."""
    submission = _require_by_id(submission_id)

    if not submission.certificate_task_id:
        raise HTTPException(status_code=404, detail="No stored attachments for this submission")

    try:
        task_dir = storage_service.task_dir(submission.certificate_task_id)
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Stored attachments have expired")

    matches = sorted(task_dir.glob(f"attachment_{role}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"No {role} attachment on this submission")

    return FileResponse(
        path=str(matches[0]),
        media_type="application/pdf",
        filename=matches[0].name.split("_", 2)[-1],
        headers={"Cache-Control": "no-store"},
    )


# --------------------------------------------------------------------------- #
# The signature gate
# --------------------------------------------------------------------------- #


@router.post("/by-id/{submission_id}/sign", response_model=ReportSubmissionResponse)
def sign_certificate(
    submission_id: str,
    request: SignCertificateRequest,
) -> ReportSubmissionResponse:
    """Issue and sign the completion certificate for a verified package."""
    submission = _require_by_id(submission_id)

    if submission.status == STATUS_REJECTED:
        raise HTTPException(
            status_code=409,
            detail=(
                "A rejected submission cannot be signed: "
                + "; ".join(f.message for f in submission.rejections)
            ),
        )

    if submission.status == STATUS_CLARIFICATION:
        raise HTTPException(
            status_code=409,
            detail=(
                "This submission is waiting on the student. Signing it would certify a "
                "record that is still incomplete. Outstanding: "
                + "; ".join(f.code for f in submission.clarifications)
            ),
        )

    if submission.status == STATUS_SIGNED:
        raise HTTPException(
            status_code=409,
            detail=f"Already signed by {submission.signed_by} at {submission.signed_at}.",
        )

    if submission.status == STATUS_PENDING and not request.acknowledge_warnings:
        raise HTTPException(
            status_code=409,
            detail=(
                "This submission has open points that need a decision. Review them and "
                "resend with acknowledge_warnings=true to sign anyway. Open points: "
                + "; ".join(f"{f.code}: {f.message}" for f in submission.warnings)
            ),
        )

    signature_bytes = _resolve_signature(request)

    task_id = submission.certificate_task_id
    if not task_id:
        raise HTTPException(status_code=409, detail="This submission has no working directory.")

    try:
        task_dir = storage_service.task_dir(task_id)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=409,
            detail="The working directory for this submission has expired; ask for a resubmission.",
        )

    certificate_path = task_dir / "certificate.pdf"
    signed_path = task_dir / "signed.pdf"

    try:
        CertificateService.create_certificate_pdf(
            submission,
            certificate_path,
            coordinator_name=request.coordinator_name,
            note=request.note,
        )
    except ValueError as exc:
        # The renderer refuses to produce a certificate that would state
        # nothing. Surface that as a 409, not a 500 — it is a fact about this
        # submission, not a fault in the service.
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    x, y, w, h = CertificateService.SIGNATURE_BOX
    pdf_service.embed_signature(
        certificate_path,
        signed_path,
        image_bytes=signature_bytes,
        page_index=0,
        x=x,
        y=y,
        w=w,
        h=h,
    )

    token = create_download_token(task_id)
    download_url = f"/reports/by-id/{submission.id}/certificate?token={token}"

    submission.status = STATUS_SIGNED
    submission.certificate_pdf_path = str(certificate_path)
    submission.signed_certificate_path = str(signed_path)
    submission.signed_certificate_download_url = download_url
    submission.signed_by = request.coordinator_name
    submission.signed_at = datetime.now(timezone.utc).isoformat()
    submission.coordinator_note = request.note
    submission.email_subject, submission.email_body = _signed_email(submission, download_url)
    submission.report = (
        f"{submission.report} Signed by {request.coordinator_name}."
    ).strip()

    report_repository.update(submission)

    # The submission row is rewritten by signing, so the state it was signed in
    # survives only here: who signed, and which open points they took on when
    # they did. That second part is the one somebody will ask about later.
    report_repository.add_event(
        submission.id,
        "signed",
        {
            "coordinator": request.coordinator_name,
            "note": request.note or "",
            "acknowledged": [f.code for f in submission.warnings],
        },
    )

    logger.info(
        "Completion certificate for %s signed by %s (%d open point(s) acknowledged)",
        submission_id,
        request.coordinator_name,
        len(submission.warnings),
    )
    return submission


def _resolve_signature(request: SignCertificateRequest) -> bytes:
    """Decode the coordinator's drawn signature, or fall back to the generated mark."""
    if not request.signature_image_base64:
        return SignatureImageService.create_company_signature()

    raw = request.signature_image_base64
    if "," in raw:
        raw = raw.split(",", 1)[1]

    try:
        return base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid signature image") from exc


def _signed_email(submission: ReportSubmissionResponse, download_url: str) -> tuple[str, str]:
    """The delivery email. Composed here because it needs the download link."""
    greeting = f"Dear {submission.student_name}," if submission.student_name else "Dear Student,"
    return (
        "Internship Completion Certificate",
        f"{greeting}\n\n"
        "Your internship has been approved and your completion certificate has been "
        f"signed by {submission.signed_by}.\n\n"
        f"  Host organisation     : {submission.company}\n"
        f"  Period                : {submission.start_date} to {submission.end_date}\n"
        f"  Verified working days : {submission.counted_working_days}\n"
        f"  Employer evaluation   : {submission.evaluation_score}/100\n\n"
        f"Download your certificate: {download_url}\n"
        "The link is time-limited; contact the office if it lapses.\n\n"
        "The certificate carries a hash of the three documents you submitted, so it can "
        "be checked against them at any time.\n\n"
        f"Reference: {submission.id}\n\n"
        "Congratulations, and best regards,\n"
        "Internship Coordination Team",
    )


# --------------------------------------------------------------------------- #
# Certificate delivery
# --------------------------------------------------------------------------- #


@router.get("/by-id/{submission_id}/certificate", response_class=FileResponse)
def download_certificate(submission_id: str, token: str) -> FileResponse:
    """Serve the signed certificate against a valid token.

    Unlike ``/pdf/download``, this does not delete the task on first read. A
    completion certificate is a record the student may fetch more than once, and
    destroying it after a single download would make a lost file unrecoverable.
    """
    submission = _require_by_id(submission_id)

    try:
        token_task_id = verify_download_token(token)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid or expired download token")

    if token_task_id != submission.certificate_task_id:
        raise HTTPException(status_code=403, detail="Token does not match this submission")

    if submission.status != STATUS_SIGNED or not submission.signed_certificate_path:
        raise HTTPException(status_code=404, detail="No signed certificate for this submission")

    return FileResponse(
        path=submission.signed_certificate_path,
        media_type="application/pdf",
        filename=f"internship-certificate-{submission.id[:8]}.pdf",
        headers={"Cache-Control": "no-store"},
    )
