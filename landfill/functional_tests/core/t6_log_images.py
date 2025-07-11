#!/usr/bin/env python
"""Log some images with interesting paths."""

import platform

import numpy as np

import tracklab

height = width = 2
image = np.random.rand(height, width)

with tracklab.init() as run:
    run.log({"normal": tracklab.Image(image)})
    run.log({"with/forward/slash": tracklab.Image(image)})
    try:
        run.log({"with\\backward\\slash": tracklab.Image(image)})
    except ValueError:
        assert platform.system() == "Windows", "only windows throw value error"
    else:
        assert platform.system() != "Windows", "windows should have thrown value error"
