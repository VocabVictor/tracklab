#!/usr/bin/env python
import yea


def main():
    # import here so we can profile how long it takes
    import tracklab

    run = tracklab.init()
    for _ in range(1000):
        tracklab.log(dict(this=2))
    run.finish()


if __name__ == "__main__":
    yea.setup()
    main()
