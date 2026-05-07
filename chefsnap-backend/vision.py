"""
vision.py — Gemini Vision detection service
Accepts Base64-encoded image data and returns DetectionResponseDTO.
Model name and temperature are read from config.py.
"""

import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from config import VISION_MODEL, VISION_TEMPERATURE
from guardrails import DetectionResponseDTO


class VisionService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=VISION_MODEL, temperature=VISION_TEMPERATURE
        )
        self.structured_llm = self.llm.with_structured_output(DetectionResponseDTO)

    def detect_ingredients(self, base64_images: list[str], locale: str = "en-IN") -> DetectionResponseDTO:
        """
        Accepts a list of Base64-encoded images (1–5 per session) and a BCP-47 locale.
        Returns merged ingredient detections with deduplicated names.
        The locale biases display_name language (e.g. 'en-IN' → 'Coriander (Dhaniya)').
        """
        locale_instruction = (
            "Use Indian English ingredient names where applicable "
            "(e.g. 'Coriander (Dhaniya)', 'Ginger (Adrak)'). "
            if locale.endswith("-IN") or locale.startswith("hi")
            else "Use standard English ingredient names. "
        )
        prompt_text = (
            "You are an expert culinary vision detection system. "
            "Examine the provided image(s) of a fridge or kitchen. "
            "List every edible ingredient you can see with confidence scores and quantity hints. "
            "Exclude non-food objects (shelves, containers, labels). "
            "Count regions you cannot identify as unrecognized_regions. "
            + locale_instruction
        )

        content: list[dict] = [{"type": "text", "text": prompt_text}]
        for b64 in base64_images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })

        message = HumanMessage(content=content)
        response: DetectionResponseDTO = self.structured_llm.invoke([message])
        response.request_id = f"req_{uuid.uuid4().hex[:8]}"
        return response


vision_service = VisionService()
