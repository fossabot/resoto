from resotolib.baseplugin import BaseActionPlugin
from resotolib.logger import log
from resotolib.core.search import CoreGraph
from resotolib.config import Config
from resotolib.types import Json
from .config import TemplatesConfig


class TemplatesPlugin(BaseActionPlugin):
    action = "cleanup_plan"

    def bootstrap(self):
        return Config.templates.enabled

    def do_action(self, message: Json) -> None:
        log.debug("Templates called")
        cg = CoreGraph(tls_data=self.tls_data)
        command = 'query /metadata.expires < "@NOW@" | clean "Resource is expired"'
        for response in cg.execute(command):
            if isinstance(response, Dict) and "type" in response and response["type"] == "node":
                pass

    @staticmethod
    def add_config(config: Config) -> None:
        config.add_config(TemplatesConfig)
