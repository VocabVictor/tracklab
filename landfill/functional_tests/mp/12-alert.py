#!/usr/bin/env python

import tracklab

tracklab.setup()
run = tracklab.init()
run.log(dict(m1=1))
run.log(dict(m2=2))
run.alert("this-is-my-title", "and full text", "ERROR")
