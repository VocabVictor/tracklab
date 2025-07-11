#!/usr/bin/env python
"""Test sequential runs."""

import tracklab

run1 = tracklab.init()
run1.log(dict(r1a=1, r2a=2))
run1.finish()

run2 = tracklab.init()
run2.log(dict(r1a=11, r2b=22))
# run2 will get finished with the script
