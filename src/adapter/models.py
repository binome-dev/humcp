from typing import Any, Optional

from pydantic import BaseModel, Field, create_model


def create_pydantic_model_from_schema(
    schema: dict,
    model_name: str,
    description: Optional[str] = None
) -> type[BaseModel]:
    if schema.get("type") != "object":
        # If not an object, create a simple wrapper
        return create_model(
            model_name,
            value=(Any, ...),
            __doc__=description
        )

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    fields = {}
    for field_name, field_schema in properties.items():
        field_type = _get_python_type(field_schema)
        field_description = field_schema.get("description")

        # Determine if field is required and set default
        if field_name in required:
            # Required field
            if field_description:
                fields[field_name] = (field_type, Field(..., description=field_description))
            else:
                fields[field_name] = (field_type, ...)
        else:
            # Optional field - use Optional[type] to accept None values
            optional_type = Optional[field_type]
            if field_description:
                fields[field_name] = (optional_type, Field(default=None, description=field_description))
            else:
                fields[field_name] = (optional_type, None)

    # Create the model with proper documentation
    model = create_model(model_name, **fields)
    if description:
        model.__doc__ = description

    return model


def _get_python_type(field_schema: dict) -> type:
    schema_type = field_schema.get("type")
    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    return type_mapping.get(schema_type, Any)


def sanitize_model_name(name: str) -> str:
    # Replace common separators with spaces
    name = name.replace("_", " ").replace("-", " ").replace(".", " ")
    # Title case and remove spaces
    name = "".join(word.capitalize() for word in name.split())
    # Ensure it starts with a letter
    if name and not name[0].isalpha():
        name = "Model" + name
    return name or "Model"
