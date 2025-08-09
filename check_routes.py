#!/usr/bin/env python3
from cli.server import app

print("FastAPI Routes:")
print("=" * 40)
for r in app.routes:
    try:
        methods = getattr(r, 'methods', set())
        path = getattr(r, 'path', 'unknown')
        if methods:
            print(f"{methods} {path}")
        else:
            print(f"NO_METHODS {path}")
    except Exception as e:
        print(f"ERROR: {e}")
