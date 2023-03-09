from attrs import define, field
from typing import ClassVar


@define
class TemplatesConfig:
    kind: ClassVar[str] = "templates"
    enabled: bool = field(
        default=False,
        metadata={"description": "Enable plugin?", "restart_required": True},
    )
