#!/usr/bin/env python
"""WB-7940: test that we can change env vars after tracklab.login()."""

import os
from unittest import mock

import tracklab
from tracklab.sdk.lib import filesystem

if __name__ == "__main__":
    tracklab.login()
    test_dir = "test_dir"
    filesystem.mkdir_exists_ok(test_dir)
    with mock.patch.dict(os.environ, {"WANDB_DIR": test_dir}):
        run = tracklab.init(project="test-project")
        run.finish()

    assert os.path.exists(os.path.join("wandb", "debug.log"))
    assert not os.path.exists(os.path.join(test_dir, "wandb", "debug.log"))
