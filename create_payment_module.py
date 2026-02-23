from pathlib import Path

# Create payment module directory structure
payment_dir = Path("K:/business/projects/lms_backend/app/modules/payments")
payment_dir.mkdir(parents=True, exist_ok=True)

# Create subdirectories
(Path(payment_dir) / "models").mkdir(exist_ok=True)
(Path(payment_dir) / "schemas").mkdir(exist_ok=True)
(Path(payment_dir) / "repositories").mkdir(exist_ok=True)
(Path(payment_dir) / "services").mkdir(exist_ok=True)
(Path(payment_dir) / "routers").mkdir(exist_ok=True)

# Create __init__.py files
for subdir in ["", "models", "schemas", "repositories", "services", "routers"]:
    path = Path(payment_dir) / subdir / "__init__.py"
    path.write_text("# Empty init file for payments module\n")

print("Payment module directory structure created successfully.")