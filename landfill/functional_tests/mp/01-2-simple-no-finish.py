#!/usr/bin/env python
import torch

import tracklab

run = tracklab.init()
print("somedata")

run.log(dict(m1=torch.tensor(1.0)))

import jax.numpy as jnp  # noqa

run.log(dict(m2=jnp.array(2.0, dtype=jnp.float32)))
