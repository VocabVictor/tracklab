#!/usr/bin/env python
"""Test multiple runs."""

import tracklab

run1 = tracklab.init()
run1.log(dict(r1a=1, r2a=2))

run2 = tracklab.init()
run2.log(dict(r1a=11, r2b=22))

run1.log(dict(r1a=3, r2a=4))

run2.finish()

run1.log(dict(r2a=5))
run1.finish()
