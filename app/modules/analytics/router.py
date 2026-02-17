from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.analytics.schemas import (
    CourseAnalyticsResponse,
    InstructorOverviewResponse,
    MyDashboardResponse,
    MyProgressSummary,
    SystemOverviewResponse,
)
from app.modules.analytics.services.course_analytics_service import CourseAnalyticsService
from app.modules.analytics.services.instructor_analytics_service import InstructorAnalyticsService
from app.modules.analytics.services.student_analytics_service import StudentAnalyticsService
from app.modules.analytics.services.system_analytics_service import SystemAnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/my-progress", response_model=MyProgressSummary)
def my_progress(current_user=Depends(get_current_user), db: Session = Depends(get_db)) -> MyProgressSummary:
    return StudentAnalyticsService(db).get_progress_summary(current_user.id)


@router.get("/my-dashboard", response_model=MyDashboardResponse)
def my_dashboard(current_user=Depends(get_current_user), db: Session = Depends(get_db)) -> MyDashboardResponse:
    return StudentAnalyticsService(db).get_dashboard(current_user.id)


@router.get("/courses/{course_id}", response_model=CourseAnalyticsResponse)
def course_analytics(
    course_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseAnalyticsResponse:
    return CourseAnalyticsService(db).get_course_analytics(course_id, current_user)


@router.get("/instructors/{instructor_id}/overview", response_model=InstructorOverviewResponse)
def instructor_overview(
    instructor_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InstructorOverviewResponse:
    return InstructorAnalyticsService(db).get_instructor_overview(instructor_id, current_user)


@router.get("/system/overview", response_model=SystemOverviewResponse)
def system_overview(current_user=Depends(get_current_user), db: Session = Depends(get_db)) -> SystemOverviewResponse:
    return SystemAnalyticsService(db).get_system_overview(current_user)
