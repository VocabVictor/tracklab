#!/usr/bin/env python
import random

import tracklab

# Run this like:
# WANDB_RUN_ID=xxx WANDB_RESUME=allow python resume-empty.py


def main():
    run = tracklab.init()
    print("config", tracklab.config)
    print("resumed", run.resumed)
    config_len = len(tracklab.config.keys())
    conf_update = {}
    conf_update[str(config_len)] = random.random()
    tracklab.config.update(conf_update)


if __name__ == "__main__":
    main()
