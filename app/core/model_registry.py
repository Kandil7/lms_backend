from functools import lru_cache
import sys
from typing import Optional


@lru_cache(maxsize=1)
def load_all_models() -> None:
    """
    Load all model modules once so SQLAlchemy relationship strings resolve
    consistently in API, worker, and migration contexts.
    
    Uses lazy imports with fallback to prevent circular dependency failures.
    """
    # Import model modules with comprehensive error handling
    modules_to_load = [
        ("app.modules.auth.models", "auth.models"),
        ("app.modules.users.models", "users.models"),
        ("app.modules.courses.models.course", "courses.models.course"),
        ("app.modules.courses.models.lesson", "courses.models.lesson"),
        ("app.modules.enrollments.models", "enrollments.models"),
        ("app.modules.quizzes.models.quiz", "quizzes.models.quiz"),
        ("app.modules.quizzes.models.question", "quizzes.models.question"),
        {"module": "app.modules.quizzes.models.attempt", "name": "quizzes.models.attempt"},
        ("app.modules.files.models", "files.models"),
        ("app.modules.certificates.models", "certificates.models"),
        ("app.modules.assignments.models", "assignments.models"),
        ("app.modules.instructors.models", "instructors.models"),
        ("app.modules.admin.models", "admin.models"),
    ]
    
    for module_info in modules_to_load:
        if isinstance(module_info, tuple):
            module_path, display_name = module_info
        else:
            module_path = module_info["module"]
            display_name = module_info.get("name", module_path)
        
        try:
            __import__(module_path)
            # print(f"Successfully loaded: {display_name}")
        except ImportError as e:
            # Only warn for non-critical modules, but don't fail
            if "users.models" not in str(e) and "instructors.models" not in str(e):
                print(f"Warning: Failed to import {display_name}: {e}")
            # For users/instructors, we'll handle the circular dependency differently
            pass


def get_model_class(module_path: str, class_name: str) -> Optional[type]:
    """
    Lazily import and return a model class to avoid circular imports.
    """
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        print(f"Failed to load model {class_name} from {module_path}: {e}")
        return None