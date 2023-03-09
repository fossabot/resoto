from resotolib.config import Config
from resoto_plugin_templates import InfrastructureAppsPlugin


def test_config():
    config = Config("dummy", "dummy")
    InfrastructureAppsPlugin.add_config(config)
    Config.init_default_config()
    assert Config.infrastructure.enabled is False
