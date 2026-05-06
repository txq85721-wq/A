from __future__ import annotations

import argparse

from app.pipeline import run_daily_pipeline
from app.scheduler import run_scheduler


def main() -> None:
    parser = argparse.ArgumentParser(description="A-share local recommendation platform")
    parser.add_argument("--once", action="store_true", help="Run data update and recommendation once")
    parser.add_argument("--schedule", action="store_true", help="Run scheduler at 20:00 every day")
    args = parser.parse_args()

    if args.once:
        result = run_daily_pipeline()
        print(result)
    elif args.schedule:
        run_scheduler()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
