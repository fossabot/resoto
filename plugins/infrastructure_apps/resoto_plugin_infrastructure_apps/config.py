from attrs import define, field
from enum import Enum
from typing import ClassVar, Dict
from resotolib.types import Json


class InfrastructureAppEventTrigger(Enum):
    pre_collect = "pre_collect"
    collect = "collect"
    merge_outer_edges = "merge_outer_edges"
    post_collect = "post_collect"
    pre_cleanup_plan = "pre_cleanup_plan"
    cleanup_plan = "cleanup_plan"
    post_cleanup_plan = "post_cleanup_plan"
    pre_cleanup = "pre_cleanup"
    cleanup = "cleanup"
    post_cleanup = "post_cleanup"
    pre_generate_metrics = "pre_generate_metrics"
    generate_metrics = "generate_metrics"
    post_generate_metrics = "post_generate_metrics"
    undefined = "undefined"


@define
class InfrastructureApp:
    kind: ClassVar[str] = "infrastructure_app"
    enabled: bool = field(
        default=False,
        metadata={"description": "Enable infrastructure app?"},
    )
    description: str = field(default="", metadata={"description": "Description of the app"})
    on_event: InfrastructureAppEventTrigger = field(
        default=InfrastructureAppEventTrigger.undefined, metadata={"description": "Which action to run this app on"}
    )
    template: str = field(default="", metadata={"description": "The infrastructure app template"})
    config: Json = field(factory=dict, metadata={"description": "Configuration for the app"})


@define
class InfrastructureAppsConfig:
    kind: ClassVar[str] = "infrastructure"
    enabled: bool = field(
        default=False,
        metadata={"description": "Enable plugin?", "restart_required": True},
    )
    apps: Dict[str, InfrastructureApp] = field(factory=dict, metadata={"description": "Infrastructure Apps to run"})
