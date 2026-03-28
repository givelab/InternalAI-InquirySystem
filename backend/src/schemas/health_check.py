from .base import ConfiguredBaseModel


class HealthCheck(ConfiguredBaseModel):
    status: str
