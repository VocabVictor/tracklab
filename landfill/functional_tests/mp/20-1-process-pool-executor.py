#!/usr/bin/env python
"""Simple example of using ProcessPoolExecutor with service.

This example is based on issue https://tracklab.atlassian.net/browse/WB-8733.
"""

from concurrent.futures import ProcessPoolExecutor

import yea

import tracklab


def worker(run, info):
    run.log(info)
    return info


def main():
    futures = []
    with tracklab.init() as run:
        with ProcessPoolExecutor() as executor:
            # log handler
            for i in range(3):
                future = executor.submit(worker, run, {"a": i})
                futures.append(future)
    print([future.result() for future in futures])


if __name__ == "__main__":
    yea.setup()  # Use ":yea:start_method:" to set mp.set_start_method()
    main()
