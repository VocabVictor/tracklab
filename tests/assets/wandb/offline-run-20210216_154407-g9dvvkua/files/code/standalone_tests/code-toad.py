import os

import tracklab

os.environ["WANDB_CODE_DIR"] = "."

tracklab.init(project="code-toad")

# tracklab.run.log_code()
