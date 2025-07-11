import argparse
import timeit

import tracklab


def main(size: int) -> None:
    run = tracklab.init(settings={"console": "off"})
    run.log({f"v_{i}": i for i in range(size)})
    run.finish()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--size",
        type=int,
        default=2 * 10**5,
        help="size of the logged data",
    )
    args = parser.parse_args()

    start = timeit.default_timer()

    main(args.size)
    stop = timeit.default_timer()
    print("Time: ", stop - start)
