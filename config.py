import os
import sys
import yaml
import logging
from typing import Optional, Union, TypeVar

T = TypeVar("T")


def _parse_with_warning(var_name: str, default_value: T) -> Union[T, str]:
    if var_name in os.environ:
        return os.environ[var_name]
    else:
        logging.warning(f"{var_name} not found in environment variable, default value={default_value} will be used.")
        return default_value


# load settings from yaml
SETTINGS: dict = {}
try:
    with open("settings.yml") as f:
        SETTINGS = yaml.safe_load(f)
except (yaml.YAMLError, OSError) as e:
    logging.warning(e)
    logging.warning("Default settings will be applied.")

# SCVMM connection login
CONN_LOGIN: Optional[str] = _parse_with_warning("CONN_LOGIN", None)

# SCVMM connection password
CONN_PASSWORD: Optional[str] = _parse_with_warning("CONN_PASSWORD", None)

# SCVMM connection host
if "CONN_HOST" not in os.environ:
    logging.error("CONN_HOST not specified, exiting...")
    sys.exit(1)
CONN_HOST: Optional[str] = os.environ["CONN_HOST"]
