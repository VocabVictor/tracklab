#!/usr/bin/env python
"""Simple offline run."""

import tracklab

tracklab.init(mode="offline")
tracklab.log(dict(m1=1))
tracklab.log(dict(m2=2))
tracklab.finish()
