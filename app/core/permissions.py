from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class Permission(str, Enum):
    CREATE_COURSE = "course:create"
    UPDATE_COURSE = "course:update"
    DELETE_COURSE = "course:delete"
    VIEW_ANALYTICS = "analytics:view"
    MANAGE_ENROLLMENTS = "enrollments:manage"
    MANAGE_USERS = "users:manage"
    MANAGE_QUIZZES = "quizzes:manage"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: {
        Permission.CREATE_COURSE,
        Permission.UPDATE_COURSE,
        Permission.DELETE_COURSE,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_ENROLLMENTS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_QUIZZES,
    },
    Role.INSTRUCTOR: {
        Permission.CREATE_COURSE,
        Permission.UPDATE_COURSE,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_QUIZZES,
    },
    Role.STUDENT: set(),
}


def has_permission(role: str, permission: Permission) -> bool:
    try:
        role_enum = Role(role)
    except ValueError:
        return False
    return permission in ROLE_PERMISSIONS.get(role_enum, set())
