from __future__ import annotations

from uuid import uuid4

from app.modules.assignments.repositories.repositories import AssignmentRepository, SubmissionRepository
from app.utils import constants


def test_assignment_router_wrapper_exports_router() -> None:
    from app.modules.assignments.routers import router as package_router
    from app.modules.assignments import routers as wrapper_module

    assert wrapper_module.router is package_router


def test_assignment_repositories_delegate_to_session_scalar() -> None:
    captured: dict[str, object] = {}

    class FakeSession:
        def scalar(self, stmt):
            captured["stmt"] = stmt
            return "value"

    fake_db = FakeSession()
    assignment_value = AssignmentRepository(fake_db).get_by_id(uuid4())
    submission_value = SubmissionRepository(fake_db).get_by_id(uuid4())
    assert assignment_value == "value"
    assert submission_value == "value"
    assert "stmt" in captured


def test_constants_expected_values_present() -> None:
    assert "beginner" in constants.COURSE_DIFFICULTY_LEVELS
    assert "assignment" in constants.LESSON_TYPES
    assert "completed" in constants.ENROLLMENT_STATUSES
    assert "in_progress" in constants.PROGRESS_STATUSES
    assert "graded" in constants.QUIZ_TYPES
    assert "essay" in constants.QUESTION_TYPES
