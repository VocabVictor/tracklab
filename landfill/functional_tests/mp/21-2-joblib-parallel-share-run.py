#!/usr/bin/env python

# based on issue https://tracklab.atlassian.net/browse/CLI-548
from math import sqrt

from joblib import Parallel, delayed

import tracklab


def f(run, x):
    # with tracklab.init() as run:
    run.config.x = x
    run.define_metric(f"step_{x}")
    for i in range(3):
        # Log metrics with wandb
        run.log({f"i_{x}": i * x, f"step_{x}": i})
    return sqrt(x)


def main():
    run = tracklab.init()
    res = Parallel(n_jobs=2)(delayed(f)(run, i**2) for i in range(4))
    print(res)


if __name__ == "__main__":
    main()
