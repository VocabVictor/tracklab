import numpy as np
import pandas as pd
import tracklab
import xgboost as xgb
from sklearn.datasets import fetch_california_housing
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from tracklab.integration.xgboost import WandbCallback

# load data
housing = fetch_california_housing()
data = pd.DataFrame(housing.data)
X, y = data.iloc[:, :-1], data.iloc[:, -1]
data_dmatrix = xgb.DMatrix(data=X, label=y)

# Train validation split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=123
)

run = tracklab.init(project="xgboost-housing")

# Define regressor
bst_params = dict(
    objective="reg:squarederror",
    colsample_bytree=0.3,
    learning_rate=0.1,
    max_depth=5,
    alpha=10,
    n_estimators=100,
    early_stopping_rounds=20,
    tree_method="hist",
    callbacks=[WandbCallback()],
)

xg_reg = xgb.XGBRegressor(**bst_params)

xg_reg.fit(
    X_train,
    y_train,
    eval_set=[(X_train, y_train), (X_test, y_test)],
    verbose=False,
)

# Evaluate
preds = xg_reg.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, preds))
tracklab.log({"RMSE": rmse})

run.finish()
