from __future__ import annotations

import asyncio

from green_v2.bootstrap.ingress_runtime import run


def main() -> int:
    asyncio.run(run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
