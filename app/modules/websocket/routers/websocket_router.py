from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter(prefix="/ws", tags=["WebSocket"])

# Simple in-memory storage for connected clients (for demo purposes)
connected_clients: List[WebSocket] = []

@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # Wait for messages from client (optional)
            data = await websocket.receive_text()
            # Handle client messages if needed
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        # Handle client disconnect


@router.websocket("/course-progress/{course_id}")
async def websocket_course_progress(websocket: WebSocket, course_id: str):
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # Wait for messages from client (optional)
            data = await websocket.receive_text()
            # Handle client messages if needed
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        # Handle client disconnect


@router.websocket("/quiz-attempts/{quiz_id}")
async def websocket_quiz_attempts(websocket: WebSocket, quiz_id: str):
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # Wait for messages from client (optional)
            data = await websocket.receive_text()
            # Handle client messages if needed
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        # Handle client disconnect