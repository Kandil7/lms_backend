from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class MyProgressSummary(BaseModel):
    student_id: UUID
    total_enrollments: int
    active_enrollments: int
    completed_enrollments: int
    average_progress: Decimal
    total_time_hours: Decimal
    total_lessons_completed: int
    quizzes_taken: int
    quizzes_passed: int
    average_quiz_score: Decimal


class CourseProgressItem(BaseModel):
    course_id: UUID
    course_title: str
    progress_percentage: Decimal
    completed_lessons: int
    total_lessons: int
    time_spent_hours: Decimal
    quizzes_completed: int
    average_quiz_score: Decimal


class DailyActivityItem(BaseModel):
    date: date
    lessons_completed: int
    time_spent_minutes: int
    quizzes_taken: int


class MyDashboardResponse(BaseModel):
    student_id: UUID
    summary: MyProgressSummary
    courses: list[CourseProgressItem]
    recent_activity: list[DailyActivityItem]


class CourseAnalyticsResponse(BaseModel):
    course_id: UUID
    course_title: str
    total_enrollments: int
    active_students: int
    completed_students: int
    completion_rate: Decimal
    average_progress: Decimal
    average_time_hours: Decimal
    average_rating: Decimal
    total_reviews: int


class InstructorOverviewResponse(BaseModel):
    instructor_id: UUID
    total_courses: int
    published_courses: int
    total_students: int
    total_enrollments: int
    average_course_rating: Decimal


class SystemOverviewResponse(BaseModel):
    total_users: int
    total_students: int
    total_instructors: int
    total_courses: int
    published_courses: int
    total_enrollments: int
    active_enrollments: int
