from __future__ import annotations

from green_v2.bootstrap.db_writer_runtime import run


def main() -> int:
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
