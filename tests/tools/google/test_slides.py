from unittest.mock import MagicMock, patch

import pytest

from src.tools.google.slides import (
    google_slides_add_slide,
    google_slides_add_text,
    google_slides_create_presentation,
    google_slides_get_presentation,
    google_slides_get_thumbnail,
    google_slides_list_presentations,
)


@pytest.fixture
def mock_slides_service():
    with patch("src.tools.google.slides.get_google_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


class TestListPresentations:
    @pytest.mark.asyncio
    async def test_list_presentations_success(self, mock_slides_service):
        mock_slides_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "pres1",
                    "name": "Q1 Review",
                    "modifiedTime": "2024-01-01T00:00:00Z",
                    "webViewLink": "https://docs.google.com/presentation/d/pres1",
                }
            ]
        }

        result = await google_slides_list_presentations()
        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["presentations"][0]["name"] == "Q1 Review"

    @pytest.mark.asyncio
    async def test_list_presentations_empty(self, mock_slides_service):
        mock_slides_service.files().list().execute.return_value = {"files": []}

        result = await google_slides_list_presentations()
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_presentations_error(self, mock_slides_service):
        mock_slides_service.files().list().execute.side_effect = Exception("API error")

        result = await google_slides_list_presentations()
        assert result["success"] is False


class TestGetPresentation:
    @pytest.mark.asyncio
    async def test_get_presentation_success(self, mock_slides_service):
        mock_slides_service.presentations().get().execute.return_value = {
            "presentationId": "pres1",
            "title": "My Presentation",
            "pageSize": {
                "width": {"magnitude": 720, "unit": "PT"},
                "height": {"magnitude": 405, "unit": "PT"},
            },
            "slides": [
                {
                    "objectId": "slide1",
                    "pageElements": [
                        {
                            "shape": {
                                "text": {
                                    "textElements": [
                                        {"textRun": {"content": "Title Slide"}}
                                    ]
                                }
                            }
                        }
                    ],
                }
            ],
        }

        result = await google_slides_get_presentation("pres1")
        assert result["success"] is True
        assert result["data"]["id"] == "pres1"
        assert result["data"]["title"] == "My Presentation"
        assert result["data"]["slide_count"] == 1

    @pytest.mark.asyncio
    async def test_get_presentation_error(self, mock_slides_service):
        mock_slides_service.presentations().get().execute.side_effect = Exception(
            "Not found"
        )

        result = await google_slides_get_presentation("invalid")
        assert result["success"] is False


class TestCreatePresentation:
    @pytest.mark.asyncio
    async def test_create_presentation_success(self, mock_slides_service):
        mock_slides_service.presentations().create().execute.return_value = {
            "presentationId": "new_pres",
            "title": "New Presentation",
            "slides": [{"objectId": "slide1"}],
        }

        result = await google_slides_create_presentation("New Presentation")
        assert result["success"] is True
        assert result["data"]["id"] == "new_pres"
        assert result["data"]["title"] == "New Presentation"
        assert "docs.google.com/presentation" in result["data"]["web_link"]

    @pytest.mark.asyncio
    async def test_create_presentation_error(self, mock_slides_service):
        mock_slides_service.presentations().create().execute.side_effect = Exception(
            "Creation failed"
        )

        result = await google_slides_create_presentation("Test")
        assert result["success"] is False


class TestAddSlide:
    @pytest.mark.asyncio
    async def test_add_slide_success(self, mock_slides_service):
        mock_slides_service.presentations().get().execute.return_value = {
            "masters": [{"layouts": []}]
        }
        mock_slides_service.presentations().batchUpdate().execute.return_value = {
            "replies": [{"createSlide": {"objectId": "new_slide"}}]
        }

        result = await google_slides_add_slide("pres1")
        assert result["success"] is True
        assert result["data"]["slide_id"] == "new_slide"
        assert result["data"]["presentation_id"] == "pres1"

    @pytest.mark.asyncio
    async def test_add_slide_with_layout(self, mock_slides_service):
        mock_slides_service.presentations().get().execute.return_value = {
            "masters": [{"layouts": []}]
        }
        mock_slides_service.presentations().batchUpdate().execute.return_value = {
            "replies": [{"createSlide": {"objectId": "new_slide"}}]
        }

        result = await google_slides_add_slide("pres1", layout="TITLE_AND_BODY")
        assert result["success"] is True
        assert result["data"]["layout"] == "TITLE_AND_BODY"

    @pytest.mark.asyncio
    async def test_add_slide_error(self, mock_slides_service):
        mock_slides_service.presentations().batchUpdate().execute.side_effect = (
            Exception("Presentation not found")
        )

        result = await google_slides_add_slide("invalid")
        assert result["success"] is False


class TestAddTextToSlide:
    @pytest.mark.asyncio
    async def test_add_text_to_slide_success(self, mock_slides_service):
        mock_slides_service.presentations().batchUpdate().execute.return_value = {}

        result = await google_slides_add_text("pres1", "slide1", "Hello, World!")
        assert result["success"] is True
        assert result["data"]["text"] == "Hello, World!"
        assert result["data"]["slide_id"] == "slide1"

    @pytest.mark.asyncio
    async def test_add_text_to_slide_with_position(self, mock_slides_service):
        mock_slides_service.presentations().batchUpdate().execute.return_value = {}

        result = await google_slides_add_text(
            "pres1", "slide1", "Positioned text", x=200, y=300, width=500, height=50
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_add_text_to_slide_error(self, mock_slides_service):
        mock_slides_service.presentations().batchUpdate().execute.side_effect = (
            Exception("Slide not found")
        )

        result = await google_slides_add_text("pres1", "invalid", "text")
        assert result["success"] is False


class TestGetSlideThumbnail:
    @pytest.mark.asyncio
    async def test_get_slide_thumbnail_success(self, mock_slides_service):
        mock_slides_service.presentations().pages().getThumbnail().execute.return_value = {
            "contentUrl": "https://example.com/thumbnail.png",
            "width": 800,
            "height": 450,
        }

        result = await google_slides_get_thumbnail("pres1", "slide1")
        assert result["success"] is True
        assert result["data"]["slide_id"] == "slide1"
        assert "thumbnail.png" in result["data"]["content_url"]

    @pytest.mark.asyncio
    async def test_get_slide_thumbnail_with_size(self, mock_slides_service):
        mock_slides_service.presentations().pages().getThumbnail().execute.return_value = {
            "contentUrl": "https://example.com/thumbnail_large.png",
            "width": 1600,
            "height": 900,
        }

        result = await google_slides_get_thumbnail("pres1", "slide1", size="LARGE")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_slide_thumbnail_error(self, mock_slides_service):
        mock_slides_service.presentations().pages().getThumbnail().execute.side_effect = Exception(
            "Slide not found"
        )

        result = await google_slides_get_thumbnail("pres1", "invalid")
        assert result["success"] is False
