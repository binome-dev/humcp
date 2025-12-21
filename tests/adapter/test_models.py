from typing import Any

from pydantic import BaseModel

from src.humcp.models import (
    _get_python_type,
    create_pydantic_model_from_schema,
    sanitize_model_name,
)


class TestSanitizeModelName:
    def test_simple_name(self):
        assert sanitize_model_name("calculator") == "Calculator"

    def test_underscore_separated(self):
        assert sanitize_model_name("my_model_name") == "MyModelName"

    def test_hyphen_separated(self):
        assert sanitize_model_name("my-model-name") == "MyModelName"

    def test_dot_separated(self):
        assert sanitize_model_name("my.model.name") == "MyModelName"

    def test_mixed_separators(self):
        assert sanitize_model_name("my_model-name.test") == "MyModelNameTest"

    def test_starts_with_number(self):
        result = sanitize_model_name("123model")
        assert result.startswith("Model")
        assert result[0].isalpha()

    def test_empty_string(self):
        assert sanitize_model_name("") == "Model"

    def test_only_separators(self):
        assert sanitize_model_name("___") == "Model"

    def test_already_capitalized(self):
        assert sanitize_model_name("MyModel") == "Mymodel"


class TestGetPythonType:
    def test_string_type(self):
        assert _get_python_type({"type": "string"}) is str

    def test_integer_type(self):
        assert _get_python_type({"type": "integer"}) is int

    def test_number_type(self):
        assert _get_python_type({"type": "number"}) is float

    def test_boolean_type(self):
        assert _get_python_type({"type": "boolean"}) is bool

    def test_array_type(self):
        assert _get_python_type({"type": "array"}) is list

    def test_object_type(self):
        assert _get_python_type({"type": "object"}) is dict

    def test_unknown_type(self):
        assert _get_python_type({"type": "unknown"}) is Any

    def test_missing_type(self):
        assert _get_python_type({}) is Any

    def test_null_type(self):
        assert _get_python_type({"type": "null"}) is Any


class TestCreatePydanticModelFromSchema:
    def test_simple_object_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }

        Model = create_pydantic_model_from_schema(schema, "TestModel")

        assert issubclass(Model, BaseModel)
        assert "name" in Model.model_fields
        assert "age" in Model.model_fields

    def test_required_fields(self):
        schema = {
            "type": "object",
            "properties": {
                "required_field": {"type": "string"},
                "optional_field": {"type": "string"},
            },
            "required": ["required_field"],
        }

        Model = create_pydantic_model_from_schema(schema, "TestModel")

        # Required field should not have a default
        assert Model.model_fields["required_field"].is_required()
        # Optional field should have None as default
        assert not Model.model_fields["optional_field"].is_required()

    def test_all_types(self):
        schema = {
            "type": "object",
            "properties": {
                "str_field": {"type": "string"},
                "int_field": {"type": "integer"},
                "float_field": {"type": "number"},
                "bool_field": {"type": "boolean"},
                "list_field": {"type": "array"},
                "dict_field": {"type": "object"},
            },
            "required": [],
        }

        Model = create_pydantic_model_from_schema(schema, "AllTypesModel")

        assert issubclass(Model, BaseModel)
        assert len(Model.model_fields) == 6

    def test_non_object_schema(self):
        schema = {"type": "string"}

        Model = create_pydantic_model_from_schema(schema, "SimpleModel")

        assert issubclass(Model, BaseModel)
        assert "value" in Model.model_fields

    def test_empty_schema(self):
        schema = {}

        Model = create_pydantic_model_from_schema(schema, "EmptyModel")

        assert issubclass(Model, BaseModel)
        assert "value" in Model.model_fields

    def test_model_with_description(self):
        schema = {
            "type": "object",
            "properties": {
                "field": {"type": "string"},
            },
            "required": [],
        }

        Model = create_pydantic_model_from_schema(
            schema, "DescribedModel", description="A test model"
        )

        assert Model.__doc__ == "A test model"

    def test_field_with_description_required(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The user's name"},
            },
            "required": ["name"],
        }

        Model = create_pydantic_model_from_schema(schema, "FieldDescModel")

        assert "name" in Model.model_fields
        assert Model.model_fields["name"].description == "The user's name"

    def test_field_with_description_optional(self):
        schema = {
            "type": "object",
            "properties": {
                "nickname": {"type": "string", "description": "Optional nickname"},
            },
            "required": [],
        }

        Model = create_pydantic_model_from_schema(schema, "OptionalFieldModel")

        assert "nickname" in Model.model_fields
        assert Model.model_fields["nickname"].description == "Optional nickname"
        # Optional field should accept None
        instance = Model(nickname=None)
        assert instance.nickname is None

    def test_model_instantiation(self):
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
        }

        Model = create_pydantic_model_from_schema(schema, "CalcInput")

        instance = Model(a=5.0, b=3.0)
        assert instance.a == 5.0
        assert instance.b == 3.0

    def test_model_dump(self):
        schema = {
            "type": "object",
            "properties": {
                "required_field": {"type": "string"},
                "optional_field": {"type": "string"},
            },
            "required": ["required_field"],
        }

        Model = create_pydantic_model_from_schema(schema, "DumpModel")

        # Optional field can now accept None
        instance = Model(required_field="value", optional_field=None)
        dumped = instance.model_dump(exclude_none=True)

        assert dumped == {"required_field": "value"}

    def test_object_with_no_properties(self):
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        Model = create_pydantic_model_from_schema(schema, "NoPropsModel")

        assert issubclass(Model, BaseModel)
        assert len(Model.model_fields) == 0
