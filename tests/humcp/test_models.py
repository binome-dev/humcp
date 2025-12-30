"""Tests for humcp model generation."""

from pydantic import BaseModel

from src.humcp.routes import _create_model, _pascal


class TestPascalCase:
    def test_simple_name(self):
        assert _pascal("calculator") == "Calculator"

    def test_underscore_separated(self):
        assert _pascal("my_model_name") == "MyModelName"

    def test_hyphen_separated(self):
        assert _pascal("my-model-name") == "MyModelName"

    def test_dot_separated(self):
        assert _pascal("my.model.name") == "MyModelName"

    def test_mixed_separators(self):
        assert _pascal("my_model-name.test") == "MyModelNameTest"

    def test_starts_with_number(self):
        result = _pascal("123model")
        assert result.startswith("Model")

    def test_empty_string(self):
        assert _pascal("") == "Model"


class TestCreateModel:
    def test_simple_object_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }

        Model = _create_model(schema, "TestModel")

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

        Model = _create_model(schema, "TestModel")

        assert Model.model_fields["required_field"].is_required()
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

        Model = _create_model(schema, "AllTypesModel")

        assert issubclass(Model, BaseModel)
        assert len(Model.model_fields) == 6

    def test_non_object_schema(self):
        schema = {"type": "string"}

        Model = _create_model(schema, "SimpleModel")

        assert issubclass(Model, BaseModel)
        assert "value" in Model.model_fields

    def test_empty_schema(self):
        schema = {}

        Model = _create_model(schema, "EmptyModel")

        assert issubclass(Model, BaseModel)
        assert "value" in Model.model_fields

    def test_model_instantiation(self):
        schema = {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
        }

        Model = _create_model(schema, "CalcInput")

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

        Model = _create_model(schema, "DumpModel")

        instance = Model(required_field="value", optional_field=None)
        dumped = instance.model_dump(exclude_none=True)

        assert dumped == {"required_field": "value"}
