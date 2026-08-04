#!/usr/bin/env python3
"""Compatibility entrypoint for the run-level container resource supervisor.

The former per-process memory watchdog could not enforce aggregate cgroup
memory and is intentionally retired. Use ``container_resource_supervisor.py``
for the current command interface.
"""

from container_resource_supervisor import main

if __name__ == "__main__":
    raise SystemExit(main())
