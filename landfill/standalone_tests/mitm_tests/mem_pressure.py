#!/usr/bin/env python
import time

import yea

import tracklab


def main():
    run = tracklab.init()
    history = 20
    for i in range(history):
        if i % 10 == 0:
            print(i)
        run.log(dict(num=i))
        time.sleep(0.1)
    print("done")
    run.finish()


if __name__ == "__main__":
    yea.setup()
    main()
