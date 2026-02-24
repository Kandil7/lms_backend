# Real-time Features & WebSockets

To provide a dynamic and interactive experience, the LMS supports real-time communication via WebSockets. This guide explains how we handle live connections and events.

---

## 📋 Table of Contents
1. [Why WebSockets?](#1-why-websockets)
2. [Connection Lifecycle](#2-connection-lifecycle)
3. [Client Registry](#3-client-registry)
4. [Security & Authentication](#4-security--authentication)
5. [Common Use Cases](#5-common-use-cases)

---

## 1. Why WebSockets?
While standard HTTP is great for fetching data, some features require immediate updates without polling the server:
- **Progress Sync**: Seeing progress bars update across multiple devices.
- **Notifications**: Instant alerts for new messages, grades, or course announcements.
- **Live Classroom**: Real-time interactions between students and instructors.

---

## 2. Connection Lifecycle
The connection flow follows these steps:
1. **Handshake**: The client initiates an HTTP request with an `Upgrade` header to switch to the WebSocket protocol.
2. **Authentication**: The server validates the user's session (usually via a token in the query string or a cookie).
3. **Establishment**: Once validated, the connection is kept open.
4. **Communication**: Data is exchanged in lightweight JSON frames.
5. **Termination**: Either the client or server closes the connection.

---

## 3. Client Registry
We manage active connections in `app/modules/websocket/services/client_registry.py`.

- **Tracking**: We keep track of which user is connected to which socket.
- **Grouping**: Connections can be grouped by `course_id` or `room_id`, allowing us to "broadcast" a message to all students in a specific course.
- **Cleanup**: The registry automatically removes stale or closed connections to prevent memory leaks.

---

## 4. Security & Authentication
WebSockets are subject to the same security risks as standard APIs:

- **Token Validation**: We use a `WebSocket` dependency to verify the user before accepting the connection.
- **CORS for Sockets**: We strictly limit which origins can initiate a WebSocket handshake.
- **Rate Limiting**: We limit the number of connections a single IP or User can have simultaneously.

---

## 5. Common Use Cases

### Notification Broadcast
When an instructor publishes a new lesson, the backend can push a notification to all enrolled students currently online:
```python
# Pseudo-code
await manager.broadcast_to_group(
    group_id=course_id,
    message={"type": "new_lesson", "title": lesson_title}
)
```

### Active User Tracking
Instructors can see which students are currently "online" in a course by querying the registry state.

---

## ⚠️ Developer Notes
- **State Management**: WebSockets are stateful. If the server restarts, all connections are dropped. Ensure your frontend can handle automatic reconnection (exponential backoff).
- **Concurrency**: Use `async` / `await` for all WebSocket operations to avoid blocking the event loop.
- **JSON Only**: Stick to JSON for message payloads to ensure compatibility across different frontend platforms.
