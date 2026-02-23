from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return ROOT / path


def _upsert_env_var(
    values: list[dict[str, Any]],
    *,
    key: str,
    value: str,
    var_type: str = "default",
    enabled: bool = True,
) -> None:
    for item in values:
        if item.get("key") == key:
            item["value"] = value
            item["type"] = var_type
            item["enabled"] = enabled
            return

    values.append(
        {
            "key": key,
            "value": value,
            "type": var_type,
            "enabled": enabled,
        }
    )


def _build_demo_environment(
    base_environment: dict[str, Any],
    seed_snapshot: dict[str, Any],
    *,
    base_url: str,
) -> dict[str, Any]:
    demo_env = copy.deepcopy(base_environment)
    demo_env["name"] = "LMS Backend Demo (Seeded)"

    values = demo_env.setdefault("values", [])

    credentials = seed_snapshot.get("credentials", {})
    users = seed_snapshot.get("users", {})
    course = seed_snapshot.get("course", {})
    lessons = seed_snapshot.get("lessons", [])
    quiz = seed_snapshot.get("quiz", {})
    questions = seed_snapshot.get("questions", [])
    enrollment = seed_snapshot.get("enrollment", {})
    attempt = seed_snapshot.get("attempt") or {}
    certificate = seed_snapshot.get("certificate") or {}

    student_creds = credentials.get("student", {})
    instructor_creds = credentials.get("instructor", {})
    admin_creds = credentials.get("admin", {})

    first_lesson_id = ""
    if lessons:
        non_quiz = next((item for item in lessons if item.get("lesson_type") != "quiz"), None)
        first_lesson_id = (non_quiz or lessons[0]).get("id", "")

    first_question_id = questions[0]["id"] if questions else ""

    _upsert_env_var(values, key="base_url", value=base_url)
    _upsert_env_var(values, key="access_token", value="", var_type="secret")
    _upsert_env_var(values, key="refresh_token", value="", var_type="secret")
    _upsert_env_var(values, key="student_access_token", value="", var_type="secret")
    _upsert_env_var(values, key="student_refresh_token", value="", var_type="secret")
    _upsert_env_var(values, key="instructor_access_token", value="", var_type="secret")
    _upsert_env_var(values, key="instructor_refresh_token", value="", var_type="secret")
    _upsert_env_var(values, key="admin_access_token", value="", var_type="secret")
    _upsert_env_var(values, key="admin_refresh_token", value="", var_type="secret")
    _upsert_env_var(values, key="mfa_challenge_token", value="", var_type="secret")
    _upsert_env_var(values, key="verify_email_token", value="", var_type="secret")
    _upsert_env_var(values, key="reset_token", value="", var_type="secret")

    _upsert_env_var(values, key="email", value=student_creds.get("email", "student@lms.local"))
    _upsert_env_var(values, key="password", value=student_creds.get("password", "StudentPass123"), var_type="secret")
    _upsert_env_var(values, key="role", value="student")
    _upsert_env_var(values, key="student_email", value=student_creds.get("email", "student@lms.local"))
    _upsert_env_var(
        values,
        key="student_password",
        value=student_creds.get("password", "StudentPass123"),
        var_type="secret",
    )
    _upsert_env_var(values, key="instructor_email", value=instructor_creds.get("email", "instructor@lms.local"))
    _upsert_env_var(
        values,
        key="instructor_password",
        value=instructor_creds.get("password", "InstructorPass123"),
        var_type="secret",
    )
    _upsert_env_var(values, key="admin_email", value=admin_creds.get("email", "admin@lms.local"))
    _upsert_env_var(
        values,
        key="admin_password",
        value=admin_creds.get("password", "AdminPass123"),
        var_type="secret",
    )

    _upsert_env_var(values, key="course_id", value=str(course.get("id", "")))
    _upsert_env_var(values, key="lesson_id", value=str(first_lesson_id))
    _upsert_env_var(values, key="quiz_id", value=str(quiz.get("id", "")))
    _upsert_env_var(values, key="question_id", value=str(first_question_id))
    _upsert_env_var(values, key="enrollment_id", value=str(enrollment.get("id", "")))
    _upsert_env_var(values, key="attempt_id", value=str(attempt.get("id", "")))
    _upsert_env_var(values, key="instructor_id", value=str(users.get("instructor", {}).get("id", "")))
    _upsert_env_var(values, key="user_id", value=str(users.get("student", {}).get("id", "")))
    _upsert_env_var(values, key="student_id", value=str(users.get("student", {}).get("id", "")))
    _upsert_env_var(values, key="admin_id", value=str(users.get("admin", {}).get("id", "")))

    _upsert_env_var(values, key="file_id", value="")
    _upsert_env_var(values, key="certificate_id", value=str(certificate.get("id", "")))
    _upsert_env_var(values, key="certificate_number", value=str(certificate.get("certificate_number", "")))

    return demo_env


def _request(
    *,
    name: str,
    method: str,
    url: str,
    body_json: dict[str, Any] | None = None,
    bearer_var: str | None = None,
    test_script: str | None = None,
) -> dict[str, Any]:
    request_obj: dict[str, Any] = {
        "method": method.upper(),
        "header": [],
        "url": url,
    }

    if body_json is not None:
        request_obj["header"].append({"key": "Content-Type", "value": "application/json"})
        request_obj["body"] = {
            "mode": "raw",
            "raw": json.dumps(body_json, ensure_ascii=False, indent=2),
            "options": {"raw": {"language": "json"}},
        }

    if bearer_var:
        request_obj["auth"] = {
            "type": "bearer",
            "bearer": [{"key": "token", "value": f"{{{{{bearer_var}}}}}", "type": "string"}],
        }

    item: dict[str, Any] = {
        "name": name,
        "request": request_obj,
        "response": [],
    }

    if test_script:
        item["event"] = [
            {
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": test_script.splitlines(),
                },
            }
        ]

    return item


def _build_demo_quickstart_folder() -> dict[str, Any]:
    login_student_script = """
pm.test("Student login ok", function () {
  pm.response.to.have.status(200);
});
const data = pm.response.json();
if (data.tokens) {
  pm.environment.set("student_access_token", data.tokens.access_token);
  pm.environment.set("student_refresh_token", data.tokens.refresh_token);
  pm.environment.set("access_token", data.tokens.access_token);
  pm.environment.set("refresh_token", data.tokens.refresh_token);
}
""".strip()

    login_instructor_script = """
pm.test("Instructor login ok", function () {
  pm.response.to.have.status(200);
});
const data = pm.response.json();
if (data.tokens) {
  pm.environment.set("instructor_access_token", data.tokens.access_token);
  pm.environment.set("instructor_refresh_token", data.tokens.refresh_token);
}
""".strip()

    login_admin_script = """
pm.test("Admin login ok", function () {
  pm.response.to.have.status(200);
});
const data = pm.response.json();
if (data.tokens) {
  pm.environment.set("admin_access_token", data.tokens.access_token);
  pm.environment.set("admin_refresh_token", data.tokens.refresh_token);
}
""".strip()

    return {
        "name": "Demo Quickstart",
        "item": [
            _request(
                name="Ready Check",
                method="GET",
                url="{{base_url}}/api/v1/ready",
            ),
            _request(
                name="Login Student (Save Tokens)",
                method="POST",
                url="{{base_url}}/api/v1/auth/login",
                body_json={"email": "{{student_email}}", "password": "{{student_password}}"},
                test_script=login_student_script,
            ),
            _request(
                name="Login Instructor (Save Tokens)",
                method="POST",
                url="{{base_url}}/api/v1/auth/login",
                body_json={"email": "{{instructor_email}}", "password": "{{instructor_password}}"},
                test_script=login_instructor_script,
            ),
            _request(
                name="Login Admin (Save Tokens)",
                method="POST",
                url="{{base_url}}/api/v1/auth/login",
                body_json={"email": "{{admin_email}}", "password": "{{admin_password}}"},
                test_script=login_admin_script,
            ),
            _request(
                name="Seed Student Dashboard",
                method="GET",
                url="{{base_url}}/api/v1/analytics/my-dashboard",
                bearer_var="student_access_token",
            ),
            _request(
                name="Seed Course Analytics (Instructor)",
                method="GET",
                url="{{base_url}}/api/v1/analytics/courses/{{course_id}}",
                bearer_var="instructor_access_token",
            ),
            _request(
                name="Seed Quiz Attempts (Student)",
                method="GET",
                url="{{base_url}}/api/v1/quizzes/{{quiz_id}}/attempts/my-attempts",
                bearer_var="student_access_token",
            ),
            _request(
                name="Seed System Overview (Admin)",
                method="GET",
                url="{{base_url}}/api/v1/analytics/system/overview",
                bearer_var="admin_access_token",
            ),
            _request(
                name="Seed My Certificates (Student)",
                method="GET",
                url="{{base_url}}/api/v1/certificates/my-certificates",
                bearer_var="student_access_token",
            ),
            _request(
                name="Verify Seed Certificate (Public)",
                method="GET",
                url="{{base_url}}/api/v1/certificates/verify/{{certificate_number}}",
            ),
            _request(
                name="Download Seed Certificate (Student)",
                method="GET",
                url="{{base_url}}/api/v1/certificates/{{certificate_id}}/download",
                bearer_var="student_access_token",
            ),
        ],
    }


def _build_demo_collection(base_collection: dict[str, Any]) -> dict[str, Any]:
    demo_collection = copy.deepcopy(base_collection)
    info = demo_collection.setdefault("info", {})
    info["name"] = "LMS Backend API (Demo Seeded)"
    description = str(info.get("description", "")).strip()
    suffix = "Includes a Demo Quickstart folder and is preconfigured for seeded demo data."
    info["description"] = f"{description}\n\n{suffix}".strip()

    items = demo_collection.setdefault("item", [])
    items = [item for item in items if item.get("name") != "Demo Quickstart"]
    demo_collection["item"] = [_build_demo_quickstart_folder(), *items]
    return demo_collection


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Postman demo files from seeded data snapshot")
    parser.add_argument(
        "--seed-file",
        type=Path,
        default=Path("postman/demo_seed_snapshot.json"),
        help="Seed snapshot JSON path (generated by seed_demo_data.py --json-output)",
    )
    parser.add_argument(
        "--base-collection",
        type=Path,
        default=Path("postman/LMS Backend.postman_collection.json"),
        help="Base collection JSON path",
    )
    parser.add_argument(
        "--base-environment",
        type=Path,
        default=Path("postman/LMS Backend.postman_environment.json"),
        help="Base environment JSON path",
    )
    parser.add_argument(
        "--output-collection",
        type=Path,
        default=Path("postman/LMS Backend Demo.postman_collection.json"),
        help="Output demo collection JSON path",
    )
    parser.add_argument(
        "--output-environment",
        type=Path,
        default=Path("postman/LMS Backend Demo.postman_environment.json"),
        help="Output demo environment JSON path",
    )
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base API URL for demo environment")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    seed_path = _resolve_path(args.seed_file)
    base_collection_path = _resolve_path(args.base_collection)
    base_environment_path = _resolve_path(args.base_environment)
    out_collection_path = _resolve_path(args.output_collection)
    out_environment_path = _resolve_path(args.output_environment)

    if not seed_path.exists():
        raise SystemExit(f"Seed snapshot not found: {seed_path}")
    if not base_collection_path.exists():
        raise SystemExit(f"Base collection not found: {base_collection_path}")
    if not base_environment_path.exists():
        raise SystemExit(f"Base environment not found: {base_environment_path}")

    seed_snapshot = _load_json(seed_path)
    base_collection = _load_json(base_collection_path)
    base_environment = _load_json(base_environment_path)

    demo_collection = _build_demo_collection(base_collection)
    demo_environment = _build_demo_environment(base_environment, seed_snapshot, base_url=args.base_url)

    out_collection_path.parent.mkdir(parents=True, exist_ok=True)
    out_environment_path.parent.mkdir(parents=True, exist_ok=True)

    out_collection_path.write_text(json.dumps(demo_collection, ensure_ascii=False, indent=2), encoding="utf-8")
    out_environment_path.write_text(json.dumps(demo_environment, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated: {out_collection_path}")
    print(f"Generated: {out_environment_path}")


if __name__ == "__main__":
    main()
