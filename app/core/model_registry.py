from functools import lru_cache


@lru_cache(maxsize=1)
def load_all_models() -> None:
    # Import model modules once so SQLAlchemy relationship strings resolve
    # consistently in API, worker, and migration contexts.
    import app.modules.auth.models  # noqa: F401
    import app.modules.users.models  # noqa: F401
    import app.modules.courses.models.course  # noqa: F401
    import app.modules.courses.models.lesson  # noqa: F401
    import app.modules.enrollments.models  # noqa: F401
    import app.modules.quizzes.models.quiz  # noqa: F401
    import app.modules.quizzes.models.question  # noqa: F401
    import app.modules.quizzes.models.attempt  # noqa: F401
    import app.modules.files.models  # noqa: F401
    import app.modules.certificates.models  # noqa: F401
    import app.modules.assignments.models  # noqa: F401
