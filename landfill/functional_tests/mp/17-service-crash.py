import shutil

import tracklab

# Triggers a FileNotFoundError from the internal process
# because the internal process reads/writes to the current run directory.
run = tracklab.init()
shutil.rmtree(run.dir)
run.log({"data": 5})
