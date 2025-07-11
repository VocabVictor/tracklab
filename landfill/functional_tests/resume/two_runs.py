#!/usr/bin/env python
import argparse
from typing import Optional

import tracklab


def run_first() -> str:
    with tracklab.init() as run:
        assert not run.resumed
        tracklab.log(dict(m1=1))
        tracklab.log(dict(m2=2))
        tracklab.log(dict(m3=3))
        run_id = run.id
        run_path = run.path
    return run_id, run_path


def run_again(run_id: str, resume: Optional[str]) -> None:
    kwargs = dict(id=run_id)
    if resume:
        kwargs["resume"] = resume
    with tracklab.init(**kwargs) as run:
        if run.resumed:
            print("RUN_STATE: run resumed")
        else:
            print("RUN_STATE: run not resumed")
        tracklab.log(dict(m1=11))
        tracklab.log(dict(m2=22))
        tracklab.log(dict(m4=44))


def delete_run(run_path: str) -> None:
    api = tracklab.Api()
    run = api.run(run_path)
    print(f"Deleting: {run_path}...")
    run.delete()
    print("done.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=str)
    parser.add_argument("--delete_run", action="store_true")
    args = parser.parse_args()

    run_id, run_path = run_first()
    if args.delete_run:
        delete_run(run_path)

    run_again(run_id=run_id, resume=args.resume)


if __name__ == "__main__":
    main()
