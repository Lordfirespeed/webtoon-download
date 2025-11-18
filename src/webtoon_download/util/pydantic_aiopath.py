from pathlib import Path
from typing import Any, Annotated, get_origin

from aiopath import AsyncPath, AsyncPurePath
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


# see https://docs.pydantic.dev/latest/concepts/types/#handling-third-party-types (accessed 2025-11-17)
class _AsyncPathPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:

        path_constructor = get_origin(_source_type)
        if path_constructor is None:
            path_constructor = _source_type

        assert path_constructor in {AsyncPurePath, AsyncPath}

        def validate_from_path(value: Path) -> AsyncPath | AsyncPurePath:
            return path_constructor(value)

        from_path_schema = core_schema.no_info_after_validator_function(validate_from_path, _handler.generate_schema(Path))
        return core_schema.json_or_python_schema(
            json_schema=from_path_schema,
            python_schema=core_schema.union_schema(
                [
                core_schema.is_instance_schema(AsyncPath),
                from_path_schema,
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda instance: str(instance))
        )


type PydanticAsyncPath = Annotated[AsyncPath, _AsyncPathPydanticAnnotation]
type PydanticAsyncPurePath = Annotated[AsyncPurePath, _AsyncPathPydanticAnnotation]

__all__ = ("PydanticAsyncPath",)
