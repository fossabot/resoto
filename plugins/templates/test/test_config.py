from resotolib.config import Config
from resoto_plugin_templates import TemplatesPlugin


def test_config():
    config = Config("dummy", "dummy")
    TemplatesPlugin.add_config(config)
    Config.init_default_config()
    assert Config.templates.enabled is False
