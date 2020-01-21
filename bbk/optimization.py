
# %% BayesianOptimization [https://github.com/fmfn/BayesianOptimization]
from bayes_opt import BayesianOptimization

def objective(x,y):
    f = x+0.5*y-2
    return -f

pbounds = {
    'x': (0,60),
    'y': (0,60),
}

optimizer = BayesianOptimization(
    f=objective,
    pbounds=pbounds,
    random_state=1,
    verbose=2,
)

optimizer.maximize(
    init_points=10,
    n_iter=10,
    alpha=1e-3,
    kappa=5
)

# %% Optuna [https://optuna.readthedocs.io/en/stable/index.html]

import optuna
def objective(trial):
    x = trial.suggest_int('x', 0, 60)
    y = trial.suggest_int('y', 0, 60)
    f = x+0.5*y-2
    return f

study = optuna.create_study()
study.optimize(objective, n_trials=10)

# %% Hyperopt [https://github.com/hyperopt/hyperopt]

import pickle
import time
from hyperopt import fmin, tpe, hp, STATUS_OK

space = [
    hp.uniform('x', 0, 10),
    hp.uniform('y', 0, 10)
]

def objective2(args): 
    return objective(*args)

def objective(*args):
    print(args)
    x = args[0]
    y = args[1]
    return x+y*2

best = fmin(objective2,
    space=space,
    algo=tpe.suggest,
    max_evals=10)

print(best)

# %%
