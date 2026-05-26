class LocadAdSimulatorError(Exception):
    """Base exception for the simulator."""


class ConfigError(LocadAdSimulatorError):
    """Raised when a config file is missing or invalid."""


class DataValidationError(LocadAdSimulatorError):
    """Raised when required data cannot be loaded or normalized."""
