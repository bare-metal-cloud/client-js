#!/usr/bin/env python3
"""Normalize the backend's swag output so openapi-generator accepts it.

swag (the backend's annotation->spec generator) emits three defects this
pipeline tolerates until the backend annotations are fixed:

1. Some operations have no `responses` section (8 known cases). The
   generator refuses those; we backfill an untyped 200.
2. Wildcard routes can declare a `{param}` in the path without defining it
   (1 known case: /clusters/{id}/k8s-watch/{proxyPath}). We backfill a
   required string path parameter.
3. No operation has an operationId, so the generator derives names from the
   route and can collide (it also emitted duplicate Go types for the two
   operations tagged "vault" AND "org", once per tag file). We assign every
   operation a deterministic operationId (method + route, e.g.
   postOrgsOrg_idVaultRotatePassword) and trim multi-tag operations to the
   first tag.

Usage: normalize-spec.py spec/swagger.json   (rewrites in place)
"""
import json
import re
import sys

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def operation_id(method: str, route: str) -> str:
    parts = []
    for seg in route.strip("/").split("/"):
        if seg.startswith("{") and seg.endswith("}"):
            inner = seg[1:-1]
            parts.append(inner[:1].upper() + inner[1:])
        else:
            parts.append(seg[:1].upper() + seg[1:])
    return method.capitalize() + "".join(parts)


def main() -> None:
    path = sys.argv[1]
    with open(path) as f:
        spec = json.load(f)

    fixes = []
    seen_ids = set()
    for route, item in spec.get("paths", {}).items():
        declared = {
            p.get("name")
            for p in item.get("parameters", [])
            if isinstance(p, dict) and p.get("in") == "path"
        }
        for method, op in item.items():
            if method.lower() not in HTTP_METHODS:
                continue
            if not op.get("responses"):
                op["responses"] = {"200": {"description": "OK"}}
                fixes.append(f"{method.upper()} {route} (+responses)")

            op_paths = {
                p.get("name")
                for p in op.get("parameters", [])
                if isinstance(p, dict) and p.get("in") == "path"
            }
            for name in sorted(
                set(re.findall(r"\{([^}]+)\}", route)) - declared - op_paths
            ):
                op.setdefault("parameters", []).append(
                    {
                        "type": "string",
                        "description": "Path segment (backfilled by normalize-spec)",
                        "name": name,
                        "in": "path",
                        "required": True,
                    }
                )
                fixes.append(f"{method.upper()} {route} (+param {name})")

            if not op.get("operationId"):
                candidate = operation_id(method, route)
                op["operationId"] = candidate
                seen_ids.add(candidate)
                fixes.append(f"{method.upper()} {route} (+operationId {candidate})")

            tags = op.get("tags")
            if tags and len(tags) > 1:
                op["tags"] = tags[:1]
                fixes.append(f"{method.upper()} {route} (tags {tags} -> {tags[:1]})")

    with open(path, "w") as f:
        json.dump(spec, f, indent=2)
        f.write("\n")

    print(f"normalize-spec: applied {len(fixes)} fix(es)")
    for f_ in fixes:
        print(f"  {f_}")


if __name__ == "__main__":
    main()
