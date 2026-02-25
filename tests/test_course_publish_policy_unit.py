from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ForbiddenException
from app.core.permissions import Role
from app.modules.courses.services.course_service import CourseService


def test_publish_requires_verified_instructor_profile():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    service = CourseService(db)
    repo = MagicMock()
    course = SimpleNamespace(id=uuid4(), instructor_id=uuid4())
    repo.get_by_id.return_value = course
    service.repo = repo

    current_user = SimpleNamespace(id=course.instructor_id, role=Role.INSTRUCTOR.value)

    with pytest.raises(ForbiddenException, match="Instructor verification is required before publishing courses"):
        service.publish_course(course.id, current_user)

    repo.update.assert_not_called()

