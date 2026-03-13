"""Pydantic output schemas for Google Forms tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse


class FormInfo(BaseModel):
    """Basic form information."""

    id: str = Field(..., description="Form ID")
    name: str = Field(..., description="Form name")
    modified: str = Field("", description="Last modified date")
    web_link: str = Field("", description="Web view link")


class FormQuestion(BaseModel):
    """Information about a form question."""

    id: str = Field("", description="Question ID")
    title: str = Field("", description="Question title")
    required: bool = Field(False, description="Whether the question is required")
    type: str = Field("unknown", description="Question type")
    paragraph: bool = Field(False, description="Whether it's a paragraph text question")
    options: list[str] = Field(default_factory=list, description="Choice options")
    low: int = Field(1, description="Scale low value")
    high: int = Field(5, description="Scale high value")


class FormDetailed(BaseModel):
    """Detailed form information."""

    id: str = Field(..., description="Form ID")
    title: str = Field("", description="Form title")
    description: str = Field("", description="Form description")
    document_title: str = Field("", description="Document title in Drive")
    responder_uri: str = Field("", description="Responder URI")
    questions: list[FormQuestion] = Field(
        default_factory=list, description="Form questions"
    )
    question_count: int = Field(0, description="Number of questions")


class FormCreated(BaseModel):
    """Information about a created form."""

    id: str = Field(..., description="Form ID")
    title: str = Field("", description="Form title")
    document_title: str = Field("", description="Document title")
    responder_uri: str = Field("", description="Responder URI")
    edit_uri: str = Field("", description="Edit URI")


class FormResponseSummary(BaseModel):
    """Summary of a form response."""

    id: str = Field("", description="Response ID")
    created: str = Field("", description="Creation time")
    last_submitted: str = Field("", description="Last submitted time")
    answer_count: int = Field(0, description="Number of answers")


class FormFileAnswer(BaseModel):
    """File upload answer in a form response."""

    id: str | None = Field(None, description="File ID")
    name: str | None = Field(None, description="File name")


class FormAnswer(BaseModel):
    """Answer in a form response."""

    question_id: str = Field(..., description="Question ID")
    type: str = Field("", description="Answer type (text, file)")
    values: list[str] = Field(default_factory=list, description="Text answer values")
    files: list[FormFileAnswer] = Field(
        default_factory=list, description="File upload answers"
    )


class FormResponseDetailed(BaseModel):
    """Detailed form response information."""

    response_id: str = Field("", description="Response ID")
    created: str = Field("", description="Creation time")
    last_submitted: str = Field("", description="Last submitted time")
    answers: list[FormAnswer] = Field(default_factory=list, description="Answers")


class FormsListData(BaseModel):
    """Output data for google_forms_list_forms tool."""

    forms: list[FormInfo] = Field(..., description="List of forms")
    total: int = Field(..., description="Total number of forms")


class FormsListResponsesData(BaseModel):
    """Output data for google_forms_list_responses tool."""

    responses: list[FormResponseSummary] = Field(..., description="List of responses")
    total: int = Field(..., description="Total number of responses")


# Forms Responses
class FormsListResponse(ToolResponse[FormsListData]):
    """Response for google_forms_list_forms tool."""

    pass


class FormsGetFormResponse(ToolResponse[FormDetailed]):
    """Response for google_forms_get_form tool."""

    pass


class FormsCreateFormResponse(ToolResponse[FormCreated]):
    """Response for google_forms_create_form tool."""

    pass


class FormsListResponsesResponse(ToolResponse[FormsListResponsesData]):
    """Response for google_forms_list_responses tool."""

    pass


class FormsGetResponseResponse(ToolResponse[FormResponseDetailed]):
    """Response for google_forms_get_response tool."""

    pass
