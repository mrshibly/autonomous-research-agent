"""
API routes for research tasks.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.research import (
    ErrorResponse,
    ResearchCreated,
    ResearchHistoryResponse,
    ResearchReport,
    ResearchRequest,
    ResearchStatus,
    ChatRequest,
    ChatResponse,
)
from app.services import research_service
from app.utils.security import limiter

router = APIRouter(prefix="/research", tags=["Research"])


@router.post(
    "",
    response_model=ResearchCreated,
    status_code=201,
    summary="Submit a new research task",
    responses={
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit("5/minute")
async def create_research(
    request: Request,
    body: ResearchRequest,
    db: AsyncSession = Depends(get_db),
) -> ResearchCreated:
    """
    Submit a new research topic for investigation.

    The system will search for papers, analyze them, and generate
    a structured report. Use the returned task_id to check progress.
    """
    result = await research_service.create_research_task(
        db=db,
        topic=body.topic,
        max_papers=body.max_papers,
    )
    return result


@router.get(
    "/{task_id}/status",
    response_model=ResearchStatus,
    summary="Get research task status",
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
async def get_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchStatus:
    """Get the current progress and status of a research task."""
    status = await research_service.get_task_status(db, task_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Research task not found.")
    return status


@router.get(
    "/{task_id}/report",
    response_model=ResearchReport,
    summary="Get completed research report",
    responses={
        404: {"model": ErrorResponse, "description": "Task not found or not completed"},
    },
)
async def get_report(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResearchReport:
    """
    Get the final research report for a completed task.

    Returns 404 if the task doesn't exist or hasn't completed yet.
    """
    report = await research_service.get_report(db, task_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found. Task may not exist or may still be in progress.",
        )
    return report


@router.get(
    "/history",
    response_model=ResearchHistoryResponse,
    summary="Get research history",
)
async def get_history(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> ResearchHistoryResponse:
    """Get paginated list of all research tasks."""
    return await research_service.get_history(db, page=page, page_size=page_size)


@router.delete(
    "/{task_id}",
    status_code=204,
    summary="Delete a research task",
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
async def delete_research(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a research task and its associated data."""
    deleted = await research_service.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Research task not found.")


@router.post(
    "/{task_id}/chat",
    response_model=ChatResponse,
    summary="Chat with research documents",
)
@limiter.limit("20/minute")
async def chat_with_research(
    request: Request,
    task_id: str,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Chat with the AI about the specifics of the researched papers.
    Uses the task-specific RAG index for grounding.
    """
    try:
        result = await research_service.chat_with_task(db, task_id, body.message)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        if "429" in str(e) or "attempts" in str(e) or "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=429, 
                detail="LLM Provider Rate Limit exceeded. Please wait a minute and try again."
            )
        raise HTTPException(status_code=500, detail=f"Chat Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Chat Error: {str(e)}")


@router.get("/{task_id}/export/pdf", summary="Export report as PDF")
async def export_pdf(task_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and download a PDF version of the research report."""
    report = await research_service.get_report(db, task_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    
    from app.utils.export_utils import generate_pdf_report
    from fastapi.responses import FileResponse
    
    report_dict = report.model_dump()
    pdf_path = generate_pdf_report(report_dict, report.topic)
    
    if not pdf_path:
        raise HTTPException(status_code=500, detail="Failed to generate PDF.")
        
    safe_topic = "".join(c for c in report.topic if c.isalnum() or c in (" ", "-", "_")).strip()
    safe_topic = safe_topic.replace(" ", "_")[:30]
    filename = f"report_{safe_topic}_{task_id[:8]}.pdf"
    
    return FileResponse(
        pdf_path, 
        media_type="application/pdf", 
        filename=filename
    )


@router.get("/{task_id}/export/markdown", summary="Export report as Markdown")
async def export_markdown(task_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and download a Markdown version of the research report."""
    report = await research_service.get_report(db, task_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    
    from app.utils.export_utils import generate_markdown_report
    from fastapi.responses import Response
    
    report_dict = report.model_dump()
    md_content = generate_markdown_report(report_dict, report.topic)
    
    # Sanitize topic for filename
    safe_topic = "".join(c for c in report.topic if c.isalnum() or c in (" ", "-", "_")).strip()
    safe_topic = safe_topic.replace(" ", "_")[:30]
    filename = f"report_{safe_topic}_{task_id[:8]}.md"
    
    return Response(
        content=md_content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/{task_id}/export/bibtex", summary="Export citations as BibTeX")
async def export_bib(task_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and download a BibTeX file for all cited papers."""
    report = await research_service.get_report(db, task_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    
    from app.utils.export_utils import generate_bibtex
    from fastapi.responses import Response
    
    papers_dict = [p.model_dump() for p in report.papers]
    bib_content = generate_bibtex(papers_dict)
    
    filename = f"citations_{task_id[:8]}.bib"
    return Response(
        content=bib_content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
@router.get("/diag/storage", summary="Diagnostic: List storage contents")
async def diagnostic_storage():
    """Lists contents of the data directory for troubleshooting."""
    import os
    from app.config import get_settings
    settings = get_settings()
    
    diag_info = {
        "data_dir": settings.data_dir,
        "exists": os.path.exists(settings.data_dir),
        "contents": {}
    }
    
    if diag_info["exists"]:
        for root, dirs, files in os.walk(settings.data_dir):
            rel_path = os.path.relpath(root, settings.data_dir)
            diag_info["contents"][rel_path] = {
                "dirs": dirs,
                "files": files
            }
            
    return diag_info
