import os

import tracklab

# Clear network buffer setting (if set)
# this is temporary until we add an option in yea to allow this
os.environ.pop("WANDB_X_NETWORK_BUFFER", None)

run = tracklab.init()

for x in range(10):
    run.log(dict(a=x))
