from datetime import timedelta
from typing import Tuple, List, Any

import pytest

from resotocore.dependencies import Dependencies, TenantDependencyCache, TenantDependencies
from resotocore.service import Service
from resotocore.system_start import parse_args
from resotocore.types import JsonElement


def test_parse_override() -> None:
    def parse(args: str) -> List[Tuple[str, JsonElement]]:
        return parse_args(args.split()).config_override  # type: ignore

    assert parse(f"--override a=foo") == [("a", "foo")]
    assert parse(f"--override a=foo,bla") == [("a", ["foo", "bla"])]
    assert parse(f"--override a=foo,bla b=a,b,c") == [("a", ["foo", "bla"]), ("b", ["a", "b", "c"])]
    assert parse(f'--override a="value,with,comma,in,quotes"') == [("a", "value,with,comma,in,quotes")]
    assert parse(f'--override a=some,value,"with,comma"') == [("a", ["some", "value", "with,comma"])]


class ExampleService(Service):
    def __init__(self, name: str) -> None:
        self.name = name
        self.started = False

    async def start(self) -> Any:
        self.started = True

    async def stop(self) -> None:
        self.started = False


@pytest.mark.asyncio
async def test_nested_dependencies() -> None:
    deps = Dependencies(a=ExampleService("a"), b=ExampleService("b"))
    async with deps.tenant_dependencies(a=ExampleService("na"), c=ExampleService("c")) as td:
        assert len(deps.services) == 2  # manages a and b
        assert len(td.services) == 2  # manages a and c
        # Deps has a and b, but not c
        a = deps.service("a", ExampleService)
        b = deps.service("b", ExampleService)
        assert a is not None
        assert b is not None
        assert a.started is False
        assert b.started is False
        assert a.name == "a"
        with pytest.raises(KeyError):
            deps.service("c", ExampleService)
        # Tenant deps have a, b and c; a is another one than in deps
        a = td.service("a", ExampleService)
        b = td.service("b", ExampleService)
        c = td.service("c", ExampleService)
        assert a is not None
        assert b is not None
        assert c is not None
        assert a.name == "na"
        assert a.started is True
        assert b.started is False
        assert c.started is True


@pytest.mark.asyncio
async def test_dependency_cache() -> None:
    time = 1
    created = 0
    deps = Dependencies(a=ExampleService("a"))

    async def tenant_deps() -> TenantDependencies:
        nonlocal created
        created += 1
        return deps.tenant_dependencies(b=ExampleService("b"))

    async with TenantDependencyCache(timedelta(seconds=1), timedelta(days=1), lambda: time) as cache:
        # getting the value from the cache will create a new value
        assert created == 0
        td_1 = await cache.get("a", tenant_deps)
        assert td_1 is not None
        assert td_1.service("b", ExampleService).started is True
        assert created == 1
        # getting it again will return the same value
        assert await cache.get("a", tenant_deps) is td_1
        assert created == 1
        # calling _expire will not remove the value from the cache
        await cache._expire()
        assert await cache.get("a", tenant_deps) is td_1
        assert created == 1
        # move in time forwards. The value will be removed from the cache and a new one is created
        time = 3
        await cache._expire()
        td_3 = await cache.get("a", tenant_deps)
        assert created == 2
        assert td_3 is not None and td_3 is not td_1
        # all services from td_1 are stopped, all services from td_3 are started
        assert td_1.service("b", ExampleService).started is False
        assert td_3.service("b", ExampleService).started is True
    # when the cache is stopped, all started services are stopped
    assert td_3.service("b", ExampleService).started is False
