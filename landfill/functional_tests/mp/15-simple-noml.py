#!/usr/bin/env python

import tracklab

tracklab.init()
print("somedata")
tracklab.log(dict(m1=1))
tracklab.log(dict(m2=2))
tracklab.finish()
