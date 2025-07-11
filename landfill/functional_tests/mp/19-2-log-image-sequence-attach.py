import multiprocessing as mp
import os

import numpy as np
import yea

import tracklab


def process_child(attach_id):
    run = tracklab.attach(attach_id=attach_id)
    rng = np.random.default_rng(os.getpid())
    height = width = 2

    media = [tracklab.Image(rng.random((height, width))) for _ in range(3)]
    run.log({"media": media})


def main():
    run = tracklab.init()
    # Start a new run in parallel in a child process
    processes = [
        mp.Process(target=process_child, kwargs=dict(attach_id=run._attach_id))
        for _ in range(2)
    ]

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    run.finish()


if __name__ == "__main__":
    yea.setup()  # Use ":yea:start_method:" to set mp.set_start_method()
    main()
