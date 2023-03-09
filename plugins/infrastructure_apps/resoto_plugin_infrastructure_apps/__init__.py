from copy import deepcopy
from jinja2 import Template
from resotolib.baseplugin import BaseActionPlugin
from resotolib.logger import log
from resotolib.core.search import CoreGraph
from resotolib.config import Config
from resotolib.types import Json
from .config import InfrastructureAppsConfig, InfrastructureApp
from typing import Dict


class InfrastructureAppsPlugin(BaseActionPlugin):
    action = "all"

    def bootstrap(self) -> bool:
        return Config.infrastructure.enabled

    def run_app(self, cg: CoreGraph, app_name: str, app: InfrastructureApp, data: Json) -> None:
        log.debug(f"Running app {app_name}")
        template = Template(app.template)
        rendered_app = template.render(data=data, config=app.config)
        log.debug(f"Rendered infrastructure app {app_name}: {rendered_app}")
        commands = rendered_app.splitlines()
        for command in commands:
            log.debug(f"Running command: {command}")
            for response in cg.execute(command):
                log.debug(f"Response: {response}")

    def do_action(self, message: Json) -> None:
        log.debug(f"Infrastructure Apps Plugin called: {message}")
        apps: Dict[str, InfrastructureApp] = deepcopy(Config.infrastructure.apps)
        cg = CoreGraph(tls_data=self.tls_data)
        message_type = message.get("message_type")
        data = message.get("data")
        for app_name, app in apps.items():
            if message_type != app.on_event.value:
                continue
            try:
                self.run_app(cg, app_name, app, data)
            except Exception as e:
                log.error(f"Failed to run infrastructure app {app_name}: {e}")

    @staticmethod
    def add_config(config: Config) -> None:
        config.add_config(InfrastructureAppsConfig)
