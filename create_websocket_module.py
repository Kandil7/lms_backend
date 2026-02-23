from pathlib import Path

# Create websocket module directory structure
websocket_dir = Path("K:/business/projects/lms_backend/app/modules/websocket")
websocket_dir.mkdir(parents=True, exist_ok=True)

# Create subdirectories
(Path(websocket_dir) / "models").mkdir(exist_ok=True)
(Path(websocket_dir) / "services").mkdir(exist_ok=True)
(Path(websocket_dir) / "routers").mkdir(exist_ok=True)

# Create __init__.py files
for subdir in ["", "models", "services", "routers"]:
    path = Path(websocket_dir) / subdir / "__init__.py"
    path.write_text("# Empty init file for websocket module\n")

print("WebSocket module directory structure created successfully.")