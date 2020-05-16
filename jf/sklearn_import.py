import importlib
import sklearn
from itertools import chain
import logging

logger = logging.getLogger(__name__)

classes = "pipeline,feature_extraction,calibration,cluster,compose,covariance,cross_decomposition,datasets,decomposition,experimental,ensemble,feature_selection,gaussian_process,impute,inspection,linear_model,manifold,metrics,mixture,model_selection,neighbors,neural_network,preprocessing,svm,tree,util,base".split(
    ","
)
mods = []
for mod in classes:
    try:
        importlib.import_module(f"sklearn.{mod}")
        mods.append(mod)
    except ModuleNotFoundError:
        logger.debug(f"No such module: sklearn.%s", mod)
for mod in list(
    chain(
        *[
            [f"{x}.{y}" for y in dir(eval(f"sklearn.{x}")) if "_" != y[0]]
            for x in dir(sklearn)
            if "_" != x[0]
        ]
    )
):
    try:
        importlib.import_module(f"sklearn.{mod}")
        mods.append(mod)
        logger.debug(f"Found a new module: sklearn.%s", mod)
    except ModuleNotFoundError:
        pass


def import_from(obj_name, module_name):
    return getattr(importlib.import_module(module_name), obj_name)


def import_from_sklearn(obj_name):
    for mod in mods:
        try:
            cls = import_from(obj_name, f"sklearn.{mod}")
            return cls
        except ModuleNotFoundError:
            logger.debug("No such module: %s", mod)
            pass
        except AttributeError:
            pass
