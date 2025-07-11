#!/usr/bin/env python
import argparse

import yea

import tracklab


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-epochs", type=int, default=10)
    parser.add_argument("--num-scalers", type=int, default=10)
    args = parser.parse_args()

    run = tracklab.init()
    for i in range(args.num_epochs):
        data = {}
        for j in range(args.num_scalers):
            data[f"m-{j}"] = j * i
        tracklab.log(data)
    run.finish()


if __name__ == "__main__":
    yea.setup()
    main()
