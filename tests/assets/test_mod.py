import multiprocessing

import tracklab


def mp_func():
    """Define at the module level to be pickle and send to the spawned process.

    Required for multiprocessing.
    """
    print("hello from the other side")


def main():
    tracklab.init()
    context = multiprocessing.get_context("spawn")
    p = context.Process(target=mp_func)
    p.start()
    p.join()
    tracklab.finish()
