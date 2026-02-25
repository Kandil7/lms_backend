from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, status

from app.core.database import SessionLocal
from app.modules.websocket.middleware import authenticate_websocket

router = APIRouter(prefix="/ws", tags=["WebSocket"])

# Simple in-memory storage for connected clients (for demo purposes)
connected_clients: List[WebSocket] = []


async def _authenticate_connection(websocket: WebSocket) -> bool:
    db = SessionLocal()
    try:
        await authenticate_websocket(websocket=websocket, db=db)
        return True
    except WebSocketException as exc:
        await websocket.close(code=exc.code, reason=exc.reason)
        return False
    except Exception:
        await websocket.close(
            code=status.WS_1011_UNEXPECTED_ERROR,
            reason="Internal server error",
        )
        return False
    finally:
        db.close()

@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket):
    if not await _authenticate_connection(websocket):
        return

    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # Wait for messages from client (optional)
            data = await websocket.receive_text()
            # Handle client messages if needed
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        # Handle client disconnect


@router.websocket("/course-progress/{course_id}")
async def websocket_course_progress(websocket: WebSocket, course_id: str):
    _ = course_id
    if not await _authenticate_connection(websocket):
        return

    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # Wait for messages from client (optional)
            data = await websocket.receive_text()
            # Handle client messages if needed
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        # Handle client disconnect


@router.websocket("/quiz-attempts/{quiz_id}")
async def websocket_quiz_attempts(websocket: WebSocket, quiz_id: str):
    _ = quiz_id
    if not await _authenticate_connection(websocket):
        return

    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # Wait for messages from client (optional)
            data = await websocket.receive_text()
            # Handle client messages if needed
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        # Handle client disconnect
