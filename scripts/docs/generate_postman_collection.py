from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app

METHOD_ORDER = ["get", "post", "put", "patch", "delete"]


def _schema_by_ref(ref: str, components: dict[str, Any]) -> dict[str, Any]:
    name = ref.rsplit("/", 1)[-1]
    return components.get(name, {})


def _example_for_schema(
    schema: dict[str, Any] | None,
    components: dict[str, Any],
    *,
    depth: int = 0,
    seen_refs: set[str] | None = None,
) -> Any:
    if not schema:
        return {}

    if seen_refs is None:
        seen_refs = set()

    if depth > 6:
        return {}

    if "$ref" in schema:
        ref = schema["$ref"]
        if ref in seen_refs:
            return {}
        seen_refs.add(ref)
        return _example_for_schema(
            _schema_by_ref(ref, components),
            components,
            depth=depth + 1,
            seen_refs=seen_refs,
        )

    if "example" in schema:
        return schema["example"]

    if "anyOf" in schema:
        non_null = [item for item in schema["anyOf"] if item.get("type") != "null"]
        candidate = non_null[0] if non_null else schema["anyOf"][0]
        return _example_for_schema(candidate, components, depth=depth + 1, seen_refs=seen_refs)

    if "oneOf" in schema:
        return _example_for_schema(schema["oneOf"][0], components, depth=depth + 1, seen_refs=seen_refs)

    schema_type = schema.get("type")

    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]

    if schema_type == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        result: dict[str, Any] = {}
        for key, value in properties.items():
            result[key] = _example_for_schema(value, components, depth=depth + 1, seen_refs=seen_refs.copy())
        return result

    if schema_type == "array":
        item_schema = schema.get("items", {})
        return [_example_for_schema(item_schema, components, depth=depth + 1, seen_refs=seen_refs.copy())]

    if schema_type == "string":
        fmt = schema.get("format")
        if fmt == "email":
            return "user@example.com"
        if fmt == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        if fmt == "date-time":
            return "2026-01-01T10:00:00Z"
        if fmt == "date":
            return "2026-01-01"
        return "string"

    if schema_type == "integer":
        return 1

    if schema_type == "number":
        return 1

    if schema_type == "boolean":
        return False

    return {}


def _example_for_field(field_name: str, field_schema: dict[str, Any], components: dict[str, Any]) -> Any:
    lowered = field_name.lower()
    if lowered == "email":
        return "user@example.com"
    if lowered == "password":
        return "StrongPass123"
    if lowered == "full_name":
        return "Demo User"
    if lowered == "role":
        return "student"
    if lowered.endswith("_id"):
        return f"{{{{{field_name}}}}}"
    if lowered in {"course_id", "lesson_id", "quiz_id", "enrollment_id", "attempt_id", "question_id", "user_id"}:
        return f"{{{{{field_name}}}}}"

    value = _example_for_schema(field_schema, components)
    if value == "string" and lowered in {"status"}:
        if "enum" in field_schema and field_schema["enum"]:
            return field_schema["enum"][0]
    return value


def _build_json_body(request_body: dict[str, Any], components: dict[str, Any]) -> str:
    content = request_body.get("content", {})
    json_schema = content.get("application/json", {}).get("schema")
    payload = _example_for_schema(json_schema, components)

    if isinstance(payload, dict):
        for key in list(payload.keys()):
            payload[key] = _example_for_field(key, json_schema.get("properties", {}).get(key, {}), components)

    return json.dumps(payload, ensure_ascii=False, indent=2)


def _path_to_postman(path: str) -> str:
    return re.sub(r"\{([^}]+)\}", r"{{\1}}", path)


def _group_name(path: str) -> str:
    normalized = path
    if normalized.startswith("/api/v1/"):
        normalized = normalized[len("/api/v1/") :]

    first = normalized.strip("/").split("/", 1)[0] if normalized.strip("/") else "system"
    return first.replace("-", " ").title()


def _request_name(method: str, path: str, operation: dict[str, Any]) -> str:
    return operation.get("summary") or operation.get("operationId") or f"{method.upper()} {path}"


def _build_request(
    method: str,
    path: str,
    operation: dict[str, Any],
    components: dict[str, Any],
) -> dict[str, Any]:
    headers: list[dict[str, str]] = []
    url = f"{{{{base_url}}}}{_path_to_postman(path)}"

    query_items = []
    for param in operation.get("parameters", []):
        if param.get("in") != "query":
            continue
        query_value = ""
        schema = param.get("schema", {})
        if "default" in schema:
            query_value = schema["default"]
        elif "enum" in schema and schema["enum"]:
            query_value = schema["enum"][0]
        else:
            query_value = f"{{{{{param['name']}}}}}"
        query_items.append(f"{param['name']}={query_value}")

    if query_items:
        url = f"{url}?{'&'.join(query_items)}"

    request: dict[str, Any] = {
        "method": method.upper(),
        "header": headers,
        "url": url,
    }

    request_body = operation.get("requestBody", {})
    if request_body:
        content = request_body.get("content", {})
        if "application/json" in content:
            headers.append({"key": "Content-Type", "value": "application/json"})
            request["body"] = {
                "mode": "raw",
                "raw": _build_json_body(request_body, components),
                "options": {"raw": {"language": "json"}},
            }
        elif "multipart/form-data" in content:
            schema = content["multipart/form-data"].get("schema", {})
            props = schema.get("properties", {})
            formdata = []
            for key, prop_schema in props.items():
                if key == "file":
                    formdata.append({"key": key, "type": "file", "src": ""})
                else:
                    formdata.append(
                        {
                            "key": key,
                            "type": "text",
                            "value": str(_example_for_field(key, prop_schema, components)),
                        }
                    )
            request["body"] = {"mode": "formdata", "formdata": formdata}

    if operation.get("security"):
        request["auth"] = {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}],
        }

    return request


def build_collection() -> tuple[dict[str, Any], dict[str, Any]]:
    schema = app.openapi()
    components = schema.get("components", {}).get("schemas", {})
    paths = schema.get("paths", {})

    grouped: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    all_path_vars: set[str] = set()

    for path in sorted(paths.keys()):
        operations = paths[path]
        group = _group_name(path)
        grouped.setdefault(group, [])

        path_vars = re.findall(r"\{([^}]+)\}", path)
        all_path_vars.update(path_vars)

        for method in METHOD_ORDER:
            if method not in operations:
                continue
            operation = operations[method]
            grouped[group].append(
                {
                    "name": _request_name(method, path, operation),
                    "request": _build_request(method, path, operation, components),
                    "response": [],
                }
            )

    collection = {
        "info": {
            "name": "LMS Backend API",
            "description": "Generated from FastAPI OpenAPI schema.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [{"name": group, "item": items} for group, items in grouped.items() if items],
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000"},
            {"key": "access_token", "value": ""},
            {"key": "refresh_token", "value": ""},
            {"key": "email", "value": "student@example.com"},
            {"key": "password", "value": "StrongPass123"},
            {"key": "role", "value": "student"},
            *[{"key": var, "value": ""} for var in sorted(all_path_vars)],
        ],
    }

    environment = {
        "name": "LMS Backend Local",
        "values": [
            {"key": "base_url", "value": "http://localhost:8000", "type": "default", "enabled": True},
            {"key": "access_token", "value": "", "type": "secret", "enabled": True},
            {"key": "refresh_token", "value": "", "type": "secret", "enabled": True},
            {"key": "email", "value": "student@example.com", "type": "default", "enabled": True},
            {"key": "password", "value": "StrongPass123", "type": "secret", "enabled": True},
            {"key": "role", "value": "student", "type": "default", "enabled": True},
            *[
                {"key": var, "value": "", "type": "default", "enabled": True}
                for var in sorted(all_path_vars)
            ],
        ],
        "_postman_variable_scope": "environment",
        "_postman_exported_at": "2026-02-17T00:00:00.000Z",
        "_postman_exported_using": "Codex",
    }

    return collection, environment


def main() -> None:
    collection, environment = build_collection()

    out_dir = ROOT / "postman"
    out_dir.mkdir(parents=True, exist_ok=True)

    collection_path = out_dir / "LMS Backend.postman_collection.json"
    environment_path = out_dir / "LMS Backend.postman_environment.json"

    collection_path.write_text(json.dumps(collection, ensure_ascii=False, indent=2), encoding="utf-8")
    environment_path.write_text(json.dumps(environment, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated: {collection_path}")
    print(f"Generated: {environment_path}")


if __name__ == "__main__":
    main()
