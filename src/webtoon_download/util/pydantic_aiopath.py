import typing
from pathlib import Path
from typing import Annotated, Any

from aiopath import AsyncPath
from pydantic_core import core_schema, PydanticCustomError, PydanticSerializationUnexpectedValue
from pydantic import (
    GenerateSchema,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ValidationError,
)


# see https://docs.pydantic.dev/latest/concepts/types/#handling-third-party-types (accessed 2025-11-17)
class _AsyncPathPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:

        origin = typing.get_origin(_source_type)
        path_constructor = origin
        strict_inner_schema = core_schema.str_schema(strict=True)
        lax_inner_schema = core_schema.str_schema()

        def path_validator(input_value: str):
            try:
                if not isinstance(input_value, str):
                    raise PydanticCustomError("path_type", "Input is not a valid path")
                return path_constructor(input_value)
            except TypeError as e:
                raise PydanticCustomError("path_type", "Input is not a valid path") from e

        def serialize_path(path: Any, info: core_schema.SerializationInfo):
            if not isinstance(path, (origin, str)):
                raise PydanticSerializationUnexpectedValue(
                    f"Expected `{origin}` but got `{type(path)}` with value `'{path}'` - serialized value may not be as expected."
                )
            if info.mode == "python":
                return path
            return str(path)

        instance_schema = core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_after_validator_function(path_validator, lax_inner_schema),
            python_schema=core_schema.is_instance_schema(origin),
        )

        schema = core_schema.lax_or_strict_schema(
            lax_schema=core_schema.union_schema(
                [
                    instance_schema,
                    core_schema.no_info_after_validator_function(path_validator, strict_inner_schema),
                ],
                custom_error_type="path_type",
                custom_error_message=f"Input is not a valid path for {origin}",
            ),
            strict_schema=instance_schema,
            serialization=core_schema.plain_serializer_function_ser_schema(serialize_path, info_arg=True, when_used="always"),
        )
        return schema
