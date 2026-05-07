"""
test_vision.py — Unit tests for the VisionService.
LLM calls are mocked — no API keys required.
Run: pytest chefsnap-backend/tests/test_vision.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import MagicMock, patch
from guardrails import DetectionResponseDTO, IngredientDTO


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def canned_detection():
    """Pre-built detection response the mock LLM will return."""
    return DetectionResponseDTO(
        ingredients=[
            IngredientDTO(name="tomato", display_name="Tomato",
                          confidence=0.95, quantity_hint="3 pieces"),
            IngredientDTO(name="paneer", display_name="Paneer",
                          confidence=0.88, quantity_hint="~200g block"),
        ],
        unrecognized_regions=1,
        request_id="",  # will be overwritten by VisionService
    )


# ─────────────────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestVisionService:
    @patch("vision.ChatGoogleGenerativeAI")
    def test_detect_returns_detection_dto(self, MockLLM, canned_detection):
        """VisionService.detect_ingredients returns a valid DetectionResponseDTO."""
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = canned_detection
        MockLLM.return_value.with_structured_output.return_value = mock_structured

        from vision import VisionService
        svc = VisionService()
        result = svc.detect_ingredients(["base64encodeddata=="])

        assert isinstance(result, DetectionResponseDTO)
        assert len(result.ingredients) == 2
        assert result.request_id.startswith("req_")

    @patch("vision.ChatGoogleGenerativeAI")
    def test_multiple_images_all_passed_to_llm(self, MockLLM, canned_detection):
        """Each base64 image is added to the LLM message content."""
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = canned_detection
        MockLLM.return_value.with_structured_output.return_value = mock_structured

        from vision import VisionService
        svc = VisionService()
        images = ["img1_b64", "img2_b64", "img3_b64"]
        svc.detect_ingredients(images)

        # The invoke call should have received a list with one HumanMessage
        call_args = mock_structured.invoke.call_args[0][0]
        assert len(call_args) == 1  # one HumanMessage

        # The message content should have 1 text block + 3 image blocks = 4
        msg = call_args[0]
        assert len(msg.content) == 4

    @patch("vision.ChatGoogleGenerativeAI")
    def test_single_image_content_structure(self, MockLLM, canned_detection):
        """Content blocks: [text, image_url] for single image."""
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = canned_detection
        MockLLM.return_value.with_structured_output.return_value = mock_structured

        from vision import VisionService
        svc = VisionService()
        svc.detect_ingredients(["single_img_b64"])

        msg = mock_structured.invoke.call_args[0][0][0]
        assert msg.content[0]["type"] == "text"
        assert msg.content[1]["type"] == "image_url"
        assert "data:image/jpeg;base64,single_img_b64" in msg.content[1]["image_url"]["url"]

    @patch("vision.ChatGoogleGenerativeAI")
    def test_request_id_is_unique_per_call(self, MockLLM, canned_detection):
        """Each call generates a unique request_id."""
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = canned_detection
        MockLLM.return_value.with_structured_output.return_value = mock_structured

        from vision import VisionService
        svc = VisionService()

        id1 = svc.detect_ingredients(["img1"]).request_id
        id2 = svc.detect_ingredients(["img2"]).request_id
        assert id1 != id2

    @patch("vision.ChatGoogleGenerativeAI")
    def test_indian_locale_adds_hindi_names_instruction(self, MockLLM, canned_detection):
        """en-IN locale embeds Indian English name instruction in prompt."""
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = canned_detection
        MockLLM.return_value.with_structured_output.return_value = mock_structured

        from vision import VisionService
        svc = VisionService()
        svc.detect_ingredients(["img"], locale="en-IN")

        msg = mock_structured.invoke.call_args[0][0][0]
        prompt_text = msg.content[0]["text"]
        assert "Indian English" in prompt_text
        assert "Dhaniya" in prompt_text

    @patch("vision.ChatGoogleGenerativeAI")
    def test_non_indian_locale_uses_standard_names(self, MockLLM, canned_detection):
        """Non-IN locale uses standard English ingredient names in prompt."""
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = canned_detection
        MockLLM.return_value.with_structured_output.return_value = mock_structured

        from vision import VisionService
        svc = VisionService()
        svc.detect_ingredients(["img"], locale="en-US")

        msg = mock_structured.invoke.call_args[0][0][0]
        prompt_text = msg.content[0]["text"]
        assert "standard English" in prompt_text
        assert "Indian English" not in prompt_text
