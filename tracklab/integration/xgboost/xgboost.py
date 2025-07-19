"""xgboost init!"""

import json
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, cast

import xgboost as xgb  # type: ignore
from xgboost import Booster

import tracklab
from tracklab.sdk.lib import telemetry as wb_telemetry

MINIMIZE_METRICS = [
    "rmse",
    "rmsle",
    "mae",
    "mape",
    "mphe",
    "logloss",
    "error",
    "error@t",
    "merror",
]

MAXIMIZE_METRICS = ["auc", "aucpr", "ndcg", "map", "ndcg@n", "map@n"]


if TYPE_CHECKING:
    from typing import Callable, List, NamedTuple

    class CallbackEnv(NamedTuple):
        evaluation_result_list: List


def wandb_callback() -> "Callable":
    """Old style callback that will be deprecated in favor of WandbCallback. Please try the new logger for more features."""
    warnings.warn(
        "wandb_callback will be deprecated in favor of WandbCallback. Please use WandbCallback for more features.",
        UserWarning,
        stacklevel=2,
    )

    with wb_telemetry.context() as tel:
        tel.feature.xgboost_old_wandb_callback = True

    def callback(env: "CallbackEnv") -> None:
        for k, v in env.evaluation_result_list:
            tracklab.log({k: v}, commit=False)
        tracklab.log({})

    return callback


class WandbCallback(xgb.callback.TrainingCallback):
    """`WandbCallback` automatically integrates XGBoost with tracklab.

    Args:
        log_model: (boolean) if True save and upload the model to Weights & Biases Artifacts
        log_feature_importance: (boolean) if True log a feature importance bar plot
        importance_type: (str) one of {weight, gain, cover, total_gain, total_cover} for tree model. weight for linear model.
        define_metric: (boolean) if True (default) capture model performance at the best step, instead of the last step, of training in your `tracklab.summary`.

    Passing `WandbCallback` to XGBoost will:

    - log the booster model configuration to Weights & Biases
    - log evaluation metrics collected by XGBoost, such as rmse, accuracy etc. to Weights & Biases
    - log training metric collected by XGBoost (if you provide training data to eval_set)
    - log the best score and the best iteration
    - save and upload your trained model to Weights & Biases Artifacts (when `log_model = True`)
    - log feature importance plot when `log_feature_importance=True` (default).
    - Capture the best eval metric in `tracklab.summary` when `define_metric=True` (default).

    Example:
        ```python
        bst_params = dict(
            objective="reg:squarederror",
            colsample_bytree=0.3,
            learning_rate=0.1,
            max_depth=5,
            alpha=10,
            n_estimators=10,
            tree_method="hist",
            callbacks=[WandbCallback()],
        )

        xg_reg = xgb.XGBRegressor(**bst_params)
        xg_reg.fit(
            X_train,
            y_train,
            eval_set=[(X_test, y_test)],
        )
        ```
    """

    def __init__(
        self,
        log_model: bool = False,
        log_feature_importance: bool = True,
        importance_type: str = "gain",
        define_metric: bool = True,
    ):
        self.log_model: bool = log_model
        self.log_feature_importance: bool = log_feature_importance
        self.importance_type: str = importance_type
        self.define_metric: bool = define_metric

        if tracklab.run is None:
            raise tracklab.Error("You must call tracklab.init() before WandbCallback()")

        with wb_telemetry.context() as tel:
            tel.feature.xgboost_wandb_callback = True

    def before_training(self, model: Booster) -> Booster:
        """Run before training is finished."""
        # Update W&B config
        config = model.save_config()
        tracklab.config.update(json.loads(config))

        return model

    def after_training(self, model: Booster) -> Booster:
        """Run after training is finished."""
        # Log the booster model as artifacts
        if self.log_model:
            self._log_model_as_artifact(model)

        if self.log_feature_importance:
            self._log_feature_importance(model)

        # Log the best score and best iteration
        if model.attr("best_score") is not None:
            tracklab.log(
                {
                    "best_score": float(cast(str, model.attr("best_score"))),
                    "best_iteration": int(cast(str, model.attr("best_iteration"))),
                }
            )

        return model

    def after_iteration(self, model: Booster, epoch: int, evals_log: dict) -> bool:
        """Run after each iteration. Return True when training should stop."""
        # Log metrics
        for data, metric in evals_log.items():
            for metric_name, log in metric.items():
                if self.define_metric:
                    self._define_metric(data, metric_name)
                    tracklab.log({f"{data}-{metric_name}": log[-1]}, commit=False)
                else:
                    tracklab.log({f"{data}-{metric_name}": log[-1]}, commit=False)

        tracklab.log({"epoch": epoch})

        self.define_metric = False

        return False

    def _log_model_as_artifact(self, model: Booster) -> None:
        model_name = f"{tracklab.run.id}_model.json"  # type: ignore
        model_path = Path(tracklab.run.dir) / model_name  # type: ignore
        model.save_model(str(model_path))

        model_artifact.add_file(str(model_path))

    def _log_feature_importance(self, model: Booster) -> None:
        fi = model.get_score(importance_type=self.importance_type)
        fi_data = [[k, fi[k]] for k in fi]
        table = tracklab.Table(data=fi_data, columns=["Feature", "Importance"])
        tracklab.log(
            {
                "Feature Importance": table
            }
        )

    def _define_metric(self, data: str, metric_name: str) -> None:
        if "loss" in str.lower(metric_name):
            tracklab.define_metric(f"{data}-{metric_name}", summary="min")
        elif str.lower(metric_name) in MINIMIZE_METRICS:
            tracklab.define_metric(f"{data}-{metric_name}", summary="min")
        elif str.lower(metric_name) in MAXIMIZE_METRICS:
            tracklab.define_metric(f"{data}-{metric_name}", summary="max")
        else:
            pass
