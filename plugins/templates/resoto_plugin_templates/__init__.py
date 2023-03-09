from resotolib.baseplugin import BaseActionPlugin
from resotolib.logger import log
from resotolib.core.search import CoreGraph
from resotolib.config import Config
from resotolib.types import Json
from .config import TemplatesConfig
from typing import Dict


class TemplatesPlugin(BaseActionPlugin):
    action = "all"

    def bootstrap(self):
        return Config.templates.enabled

    def do_action(self, message: Json) -> None:
        log.debug(f"Templates Plugin called: {message}")

    @staticmethod
    def add_config(config: Config) -> None:
        config.add_config(TemplatesConfig)
