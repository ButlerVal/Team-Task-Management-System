from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from typing import List, Optional
from sqlmodel import Session, select
from datetime import date

from models.task import Task, TaskStatus, TaskPriority, TaskAttachment
from database.connection import get_session
from services.task_service import TaskService
from services.file_service import FileService

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[Task])
async def get_tasks(
    project_id: Optional[int] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    assigned_to: Optional[int] = Query(None),
    due_date_start: Optional[date] = Query(None),
    due_date_end: Optional[date] = Query(None),
    session: Session = Depends(get_session)
):
    """Get tasks with advanced filtering"""
    return TaskService.get_tasks(
        session, 
        project_id, 
        status, 
        priority, 
        assigned_to,
        due_date_start,
        due_date_end
    )

@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: int, session: Session = Depends(get_session)):
    """Get task details by ID"""
    task = TaskService.get_task_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task: Task, session: Session = Depends(get_session)):
    """Create a new task"""
    return TaskService.create_task(session, task)

@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: int, task_data: Task, session: Session = Depends(get_session)):
    """Update an existing task"""
    task = TaskService.update_task(session, task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: Session = Depends(get_session)):
    """Delete a task"""
    if not TaskService.delete_task(session, task_id):
        raise HTTPException(status_code=404, detail="Task not found")

@router.post("/{task_id}/upload", response_model=TaskAttachment)
async def upload_file_to_task(
    task_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """Upload a file attachment to a task"""
    attachment = await TaskService.upload_attachment(session, task_id, file)
    if not attachment:
        raise HTTPException(status_code=404, detail="Task not found")
    return attachment

@router.get("/{task_id}/attachments", response_model=List[TaskAttachment])
async def get_task_attachments(task_id: int, session: Session = Depends(get_session)):
    """Get all attachments for a task"""
    return TaskService.get_task_attachments(session, task_id)

@router.post("/export/json")
async def export_tasks_to_json(
    filters: dict = None,
    session: Session = Depends(get_session)
):
    """Export tasks to JSON file"""
    return TaskService.export_tasks_to_json(session, filters)

@router.post("/export/csv")
async def export_tasks_to_csv(
    filters: dict = None,
    session: Session = Depends(get_session)
):
    """Export tasks to CSV file"""
    return TaskService.export_tasks_to_csv(session, filters)