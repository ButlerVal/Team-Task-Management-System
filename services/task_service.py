from sqlmodel import Session, select
from models.task import Task, TaskStatus, TaskPriority, TaskAttachment
from services.file_service import FileService
from datetime import datetime, date
import pandas as pd
from fastapi import UploadFile, HTTPException
import os
from pathlib import Path

class TaskService:
    @staticmethod
    def get_tasks(session: Session, project_id=None, status=None, priority=None, 
                 assigned_to=None, due_date_start=None, due_date_end=None):
        query = select(Task)
        
        if project_id:
            query = query.where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assigned_to:
            query = query.where(Task.assigned_to == assigned_to)
        if due_date_start:
            query = query.where(Task.due_date >= due_date_start)
        if due_date_end:
            query = query.where(Task.due_date <= due_date_end)
            
        return session.exec(query).all()

    # ... (other methods from previous implementation)

    @staticmethod
    async def upload_attachment(session: Session, task_id: int, file: UploadFile):
        task = session.get(Task, task_id)
        if not task:
            return None
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads/task_attachments")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{task_id}_{datetime.utcnow().timestamp()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Save file
        await FileService.save_upload_file(file, file_path)
        
        # Create attachment record
        attachment = TaskAttachment(
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            mime_type=file.content_type,
            task_id=task_id
        )
        
        session.add(attachment)
        session.commit()
        session.refresh(attachment)
        return attachment

    @staticmethod
    def get_task_attachments(session: Session, task_id: int):
        task = session.get(Task, task_id)
        if not task:
            return []
        return task.attachments

    @staticmethod
    def export_tasks_to_json(session: Session, filters=None):
        tasks = TaskService.get_tasks(session, **(filters or {}))
        export_data = [task.dict() for task in tasks]
        
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        filename = f"tasks_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = export_dir / filename
        
        FileService.export_tasks_to_json(export_data, file_path)
        return {"filename": filename, "file_path": str(file_path)}

    @staticmethod
    def export_tasks_to_csv(session: Session, filters=None):
        tasks = TaskService.get_tasks(session, **(filters or {}))
        
        # Convert to DataFrame for easy CSV export
        df = pd.DataFrame([task.dict() for task in tasks])
        
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        filename = f"tasks_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = export_dir / filename
        
        df.to_csv(file_path, index=False)
        return {"filename": filename, "file_path": str(file_path)}