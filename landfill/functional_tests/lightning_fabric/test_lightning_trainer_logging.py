#!/usr/bin/env python
import os

import lightning as pl
from pl_base import BoringModel, RandomDataset
from torch.utils.data import DataLoader

from tracklab.integration.lightning.fabric import WandbLogger


def test_lightning_trainer_logging():
    # Use concurrency experiment
    print("PIDPID", os.getpid())

    # Set up data
    num_samples = 100000
    train = RandomDataset(32, num_samples)
    train = DataLoader(train, batch_size=32)
    val = RandomDataset(32, num_samples)
    val = DataLoader(val, batch_size=32)
    test = RandomDataset(32, num_samples)
    test = DataLoader(test, batch_size=32)
    # init model
    model = BoringModel()

    # set up wandb
    config = dict(some_hparam="Logged Before Trainer starts DDP")
    wandb_logger = WandbLogger(
        project="fabric-test_lightning_trainer_logging",
        config=config,
        log_model=True,
        save_code=True,
        checkpoint_name="test_model",
    )

    # Initialize a trainer
    trainer = pl.Trainer(
        max_epochs=1,
        devices=2,
        num_nodes=1,
        accelerator="cpu",
        strategy="ddp",
        logger=wandb_logger,
    )

    # Train the model
    trainer.fit(model, train, val)
    trainer.test(dataloaders=test)


if __name__ == "__main__":
    test_lightning_trainer_logging()
