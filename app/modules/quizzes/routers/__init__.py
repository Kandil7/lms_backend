from app.modules.quizzes.routers.attempt_router import router as attempt_router
from app.modules.quizzes.routers.question_router import router as question_router
from app.modules.quizzes.routers.quiz_router import router as quiz_router

__all__ = ["quiz_router", "question_router", "attempt_router"]
