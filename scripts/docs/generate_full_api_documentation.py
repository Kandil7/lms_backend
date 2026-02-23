from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

METHOD_ORDER = ["get", "post", "put", "patch", "delete", "options", "head"]
OUTPUT_PATH = ROOT / "docs" / "09-full-api-reference.md"
PRODUCTION_BASE_URL = "https://egylms.duckdns.org"
DEVELOPMENT_BASE_URL = "http://localhost:8000"


def _ref_name(schema: dict[str, Any] | None) -> str | None:
    if not schema:
        return None
    ref = schema.get("$ref")
    if isinstance(ref, str):
        return ref.rsplit("/", 1)[-1]
    return None


def _resolve_schema(schema: dict[str, Any] | None, components: dict[str, Any]) -> dict[str, Any]:
    if not schema:
        return {}
    ref = _ref_name(schema)
    if ref:
        return components.get(ref, {})
    return schema


def _schema_label(schema: dict[str, Any] | None, components: dict[str, Any]) -> str:
    if not schema:
        return "-"

    ref = _ref_name(schema)
    if ref:
        return ref

    if "anyOf" in schema:
        parts = [_schema_label(item, components) for item in schema["anyOf"]]
        return " | ".join(parts)

    if "oneOf" in schema:
        parts = [_schema_label(item, components) for item in schema["oneOf"]]
        return " | ".join(parts)

    if schema.get("type") == "array":
        item_schema = schema.get("items", {})
        return f"array[{_schema_label(item_schema, components)}]"

    schema_type = schema.get("type")
    if schema_type:
        return schema_type

    if "properties" in schema:
        return "object"

    return "unknown"


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

    ref = schema.get("$ref")
    if isinstance(ref, str):
        if ref in seen_refs:
            return {}
        seen_refs.add(ref)
        model_name = ref.rsplit("/", 1)[-1]
        return _example_for_schema(components.get(model_name, {}), components, depth=depth + 1, seen_refs=seen_refs)

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
        result: dict[str, Any] = {}
        for key, sub_schema in schema.get("properties", {}).items():
            result[key] = _example_for_schema(sub_schema, components, depth=depth + 1, seen_refs=seen_refs.copy())
        return result

    if schema_type == "array":
        return [_example_for_schema(schema.get("items", {}), components, depth=depth + 1, seen_refs=seen_refs.copy())]

    if schema_type == "string":
        fmt = schema.get("format")
        if fmt == "email":
            return "user@example.com"
        if fmt == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        if fmt == "date-time":
            return "2026-01-01T00:00:00Z"
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


def _render_operation(
    method: str,
    path: str,
    operation: dict[str, Any],
    components: dict[str, Any],
) -> list[str]:
    lines: list[str] = []
    summary = operation.get("summary") or operation.get("operationId") or f"{method.upper()} {path}"
    auth_required = "Yes" if operation.get("security") else "No"
    tags = ", ".join(operation.get("tags", [])) or "-"

    lines.append(f"### {method.upper()} `{path}`")
    lines.append(f"- Summary: {summary}")
    lines.append(f"- Tags: {tags}")
    lines.append(f"- Authentication Required: {auth_required}")

    description = operation.get("description")
    if description:
        lines.append("- Description:")
        lines.append(description.strip())

    params = operation.get("parameters", [])
    if params:
        lines.append("")
        lines.append("**Parameters**")
        lines.append("| Name | In | Required | Type | Description |")
        lines.append("|---|---|---|---|---|")
        for param in params:
            name = param.get("name", "-")
            where = param.get("in", "-")
            required = "Yes" if param.get("required") else "No"
            schema_label = _schema_label(param.get("schema"), components)
            desc = (param.get("description") or "").replace("\n", " ").strip()
            lines.append(f"| `{name}` | `{where}` | {required} | `{schema_label}` | {desc} |")

    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    if content:
        lines.append("")
        lines.append("**Request Body**")
        for content_type, media in content.items():
            schema = media.get("schema", {})
            schema_label = _schema_label(schema, components)
            lines.append(f"- Content-Type: `{content_type}`")
            lines.append(f"- Schema: `{schema_label}`")
            if content_type == "application/json":
                example = _example_for_schema(schema, components)
                lines.append("```json")
                lines.append(json.dumps(example, ensure_ascii=False, indent=2))
                lines.append("```")

    responses = operation.get("responses", {})
    if responses:
        lines.append("")
        lines.append("**Responses**")
        lines.append("| Status | Description | Content-Type | Schema |")
        lines.append("|---|---|---|---|")
        for status_code in sorted(responses.keys(), key=lambda x: (not str(x).isdigit(), int(x) if str(x).isdigit() else 999)):
            response = responses[status_code]
            desc = (response.get("description") or "").replace("\n", " ").strip()
            response_content = response.get("content", {})
            if not response_content:
                lines.append(f"| `{status_code}` | {desc} | - | - |")
                continue
            first = True
            for content_type, media in response_content.items():
                schema_label = _schema_label(media.get("schema"), components)
                if first:
                    lines.append(f"| `{status_code}` | {desc} | `{content_type}` | `{schema_label}` |")
                    first = False
                else:
                    lines.append(f"|  |  | `{content_type}` | `{schema_label}` |")

    lines.append("")
    return lines


def build_full_api_markdown() -> str:
    openapi_schema = app.openapi()
    paths = openapi_schema.get("paths", {})
    components = openapi_schema.get("components", {}).get("schemas", {})
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    operations: list[tuple[str, str, dict[str, Any]]] = []
    for path in sorted(paths.keys()):
        path_item = paths[path]
        for method in METHOD_ORDER:
            if method in path_item:
                operations.append((method, path, path_item[method]))

    tags = sorted({tag for _, _, op in operations for tag in op.get("tags", [])})

    lines: list[str] = []
    lines.append("# Full API Documentation")
    lines.append("")
    lines.append(f"Generated from live FastAPI OpenAPI schema on {generated_at}.")
    lines.append("")
    lines.append("## Environment Base URLs")
    lines.append(f"- Production: `{PRODUCTION_BASE_URL}`")
    lines.append(f"- Development: `{DEVELOPMENT_BASE_URL}`")
    lines.append("")
    lines.append("## Authentication")
    lines.append("- Main auth method: Bearer JWT in `Authorization: Bearer <token>`.")
    lines.append("- Production auth flow also supports HTTP-only refresh-token cookies.")
    lines.append("- OAuth2 token endpoint (Swagger): `POST /api/v1/auth/token`.")
    lines.append("")
    lines.append("## Coverage")
    lines.append(f"- Paths: **{len(paths)}**")
    lines.append(f"- Operations: **{len(operations)}**")
    lines.append(f"- Tags: **{len(tags)}**")
    lines.append("")
    lines.append("## Endpoint Index")
    lines.append("| Method | Path | Summary | Tags | Auth |")
    lines.append("|---|---|---|---|---|")
    for method, path, op in operations:
        summary = (op.get("summary") or op.get("operationId") or "").replace("\n", " ").strip()
        op_tags = ", ".join(op.get("tags", [])) or "-"
        auth = "Yes" if op.get("security") else "No"
        lines.append(f"| `{method.upper()}` | `{path}` | {summary} | {op_tags} | {auth} |")

    lines.append("")
    lines.append("## Endpoints By Tag")
    for tag in tags:
        lines.append(f"## {tag}")
        lines.append("")
        tag_operations = [(m, p, o) for m, p, o in operations if tag in o.get("tags", [])]
        for method, path, op in tag_operations:
            lines.extend(_render_operation(method, path, op, components))

    lines.append("## Data Models")
    lines.append("")
    for model_name in sorted(components.keys()):
        model = components[model_name]
        required_fields = set(model.get("required", []))
        lines.append(f"### {model_name}")
        model_type = model.get("type", "object")
        lines.append(f"- Type: `{model_type}`")
        lines.append(f"- Required fields: {', '.join(f'`{f}`' for f in sorted(required_fields)) if required_fields else 'None'}")
        description = model.get("description")
        if description:
            lines.append(f"- Description: {description.strip()}")

        properties = model.get("properties", {})
        if properties:
            lines.append("")
            lines.append("| Field | Type | Required | Description |")
            lines.append("|---|---|---|---|")
            for field_name, field_schema in properties.items():
                field_type = _schema_label(field_schema, components)
                required = "Yes" if field_name in required_fields else "No"
                field_desc = (field_schema.get("description") or "").replace("\n", " ").strip()
                lines.append(f"| `{field_name}` | `{field_type}` | {required} | {field_desc} |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    markdown = build_full_api_markdown()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")
    print(f"Generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
