from unittest.mock import MagicMock, patch

import pytest

from src.tools.google.forms import (
    create_form,
    get_form,
    get_form_response,
    list_form_responses,
    list_forms,
)


@pytest.fixture
def mock_forms_service():
    with patch("src.tools.google.forms.get_google_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


class TestListForms:
    @pytest.mark.asyncio
    async def test_list_forms_success(self, mock_forms_service):
        mock_forms_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "form1",
                    "name": "Customer Survey",
                    "modifiedTime": "2024-01-01T00:00:00Z",
                    "webViewLink": "https://docs.google.com/forms/d/form1",
                }
            ]
        }

        result = await list_forms()
        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["forms"][0]["name"] == "Customer Survey"

    @pytest.mark.asyncio
    async def test_list_forms_empty(self, mock_forms_service):
        mock_forms_service.files().list().execute.return_value = {"files": []}

        result = await list_forms()
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_forms_error(self, mock_forms_service):
        mock_forms_service.files().list().execute.side_effect = Exception("API error")

        result = await list_forms()
        assert result["success"] is False


class TestGetForm:
    @pytest.mark.asyncio
    async def test_get_form_success(self, mock_forms_service):
        mock_forms_service.forms().get().execute.return_value = {
            "formId": "form1",
            "info": {
                "title": "Customer Survey",
                "description": "Please share your feedback",
                "documentTitle": "Customer Survey Form",
            },
            "responderUri": "https://docs.google.com/forms/d/form1/viewform",
            "items": [
                {
                    "itemId": "q1",
                    "title": "How satisfied are you?",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "scaleQuestion": {"low": 1, "high": 5},
                        }
                    },
                },
                {
                    "itemId": "q2",
                    "title": "Any comments?",
                    "questionItem": {
                        "question": {"required": False, "textQuestion": {"paragraph": True}}
                    },
                },
            ],
        }

        result = await get_form("form1")
        assert result["success"] is True
        assert result["data"]["id"] == "form1"
        assert result["data"]["title"] == "Customer Survey"
        assert result["data"]["question_count"] == 2
        assert result["data"]["questions"][0]["type"] == "scale"
        assert result["data"]["questions"][1]["type"] == "text"

    @pytest.mark.asyncio
    async def test_get_form_with_choice_question(self, mock_forms_service):
        mock_forms_service.forms().get().execute.return_value = {
            "formId": "form2",
            "info": {"title": "Poll"},
            "responderUri": "https://docs.google.com/forms/d/form2/viewform",
            "items": [
                {
                    "itemId": "q1",
                    "title": "Choose an option",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "Option A"},
                                    {"value": "Option B"},
                                    {"value": "Option C"},
                                ],
                            },
                        }
                    },
                }
            ],
        }

        result = await get_form("form2")
        assert result["success"] is True
        assert result["data"]["questions"][0]["type"] == "radio"
        assert len(result["data"]["questions"][0]["options"]) == 3

    @pytest.mark.asyncio
    async def test_get_form_error(self, mock_forms_service):
        mock_forms_service.forms().get().execute.side_effect = Exception("Not found")

        result = await get_form("invalid")
        assert result["success"] is False


class TestCreateForm:
    @pytest.mark.asyncio
    async def test_create_form_success(self, mock_forms_service):
        mock_forms_service.forms().create().execute.return_value = {
            "formId": "new_form",
            "info": {"title": "New Form", "documentTitle": "New Form"},
            "responderUri": "https://docs.google.com/forms/d/new_form/viewform",
        }

        result = await create_form("New Form")
        assert result["success"] is True
        assert result["data"]["id"] == "new_form"
        assert result["data"]["title"] == "New Form"
        assert "edit" in result["data"]["edit_uri"]

    @pytest.mark.asyncio
    async def test_create_form_with_document_title(self, mock_forms_service):
        mock_forms_service.forms().create().execute.return_value = {
            "formId": "new_form",
            "info": {"title": "Survey Title", "documentTitle": "Survey Doc"},
            "responderUri": "https://docs.google.com/forms/d/new_form/viewform",
        }

        result = await create_form("Survey Title", document_title="Survey Doc")
        assert result["success"] is True
        assert result["data"]["document_title"] == "Survey Doc"

    @pytest.mark.asyncio
    async def test_create_form_error(self, mock_forms_service):
        mock_forms_service.forms().create().execute.side_effect = Exception(
            "Creation failed"
        )

        result = await create_form("Test")
        assert result["success"] is False


class TestListFormResponses:
    @pytest.mark.asyncio
    async def test_list_form_responses_success(self, mock_forms_service):
        mock_forms_service.forms().responses().list().execute.return_value = {
            "responses": [
                {
                    "responseId": "resp1",
                    "createTime": "2024-01-10T10:00:00Z",
                    "lastSubmittedTime": "2024-01-10T10:05:00Z",
                    "answers": {"q1": {}, "q2": {}},
                },
                {
                    "responseId": "resp2",
                    "createTime": "2024-01-11T10:00:00Z",
                    "lastSubmittedTime": "2024-01-11T10:03:00Z",
                    "answers": {"q1": {}},
                },
            ]
        }

        result = await list_form_responses("form1")
        assert result["success"] is True
        assert result["data"]["total"] == 2
        assert result["data"]["responses"][0]["id"] == "resp1"
        assert result["data"]["responses"][0]["answer_count"] == 2

    @pytest.mark.asyncio
    async def test_list_form_responses_empty(self, mock_forms_service):
        mock_forms_service.forms().responses().list().execute.return_value = {
            "responses": []
        }

        result = await list_form_responses("form1")
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_form_responses_error(self, mock_forms_service):
        mock_forms_service.forms().responses().list().execute.side_effect = Exception(
            "Not found"
        )

        result = await list_form_responses("invalid")
        assert result["success"] is False


class TestGetFormResponse:
    @pytest.mark.asyncio
    async def test_get_form_response_success(self, mock_forms_service):
        mock_forms_service.forms().responses().get().execute.return_value = {
            "responseId": "resp1",
            "createTime": "2024-01-10T10:00:00Z",
            "lastSubmittedTime": "2024-01-10T10:05:00Z",
            "answers": {
                "q1": {"textAnswers": {"answers": [{"value": "Great product!"}]}},
                "q2": {"textAnswers": {"answers": [{"value": "5"}]}},
            },
        }

        result = await get_form_response("form1", "resp1")
        assert result["success"] is True
        assert result["data"]["response_id"] == "resp1"
        assert len(result["data"]["answers"]) == 2
        assert result["data"]["answers"][0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_get_form_response_with_file_upload(self, mock_forms_service):
        mock_forms_service.forms().responses().get().execute.return_value = {
            "responseId": "resp2",
            "createTime": "2024-01-10T10:00:00Z",
            "lastSubmittedTime": "2024-01-10T10:05:00Z",
            "answers": {
                "q1": {
                    "fileUploadAnswers": {
                        "answers": [{"fileId": "file1", "fileName": "document.pdf"}]
                    }
                }
            },
        }

        result = await get_form_response("form1", "resp2")
        assert result["success"] is True
        assert result["data"]["answers"][0]["type"] == "file"
        assert result["data"]["answers"][0]["files"][0]["name"] == "document.pdf"

    @pytest.mark.asyncio
    async def test_get_form_response_error(self, mock_forms_service):
        mock_forms_service.forms().responses().get().execute.side_effect = Exception(
            "Not found"
        )

        result = await get_form_response("form1", "invalid")
        assert result["success"] is False
