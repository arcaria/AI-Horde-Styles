import json
import unittest
from typing import Any

from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGenerationInputPayload


class TestStyles(unittest.TestCase):
    def setUp(self):
        with open("styles.json", "r", encoding="utf-8") as file:
            self.styles: dict[str, dict[str, Any]] = json.load(file)

    @staticmethod
    def validate_request(request: dict[str, ImageGenerationInputPayload | Any]) -> None:
        ImageGenerateAsyncRequest.model_validate(request, strict=True)

    def style_to_request(self, style: dict[str, Any]) -> dict[str, ImageGenerationInputPayload | Any]:
        prompt = style.pop("prompt")
        if "###" not in prompt and "{np}" in prompt:
            prompt = prompt.replace("{np}", "###{np}")

        # The negative prompt is greedy
        positive_prompt, *negative_prompt = prompt.split("###")
        negative_prompt = "###".join(negative_prompt) or None
        del prompt

        self.assertIn("{p}", positive_prompt, msg="Positive prompt must contain {p}")
        self.assertNotIn("{np}", positive_prompt, msg="Positive prompt must not contain {np}")
        if negative_prompt is not None:
            self.assertIn("{np}", negative_prompt, msg="Negative prompt must contain {np}")
            self.assertNotIn("{p}", negative_prompt, msg="Negative prompt must not contain {p}")

        request = {
            "prompt": positive_prompt + (f"###{negative_prompt}" if negative_prompt else ""),
            "params": {},
        }
        if "model" in style:
            request["models"] = [style.pop("model")]

        request_fields = set(ImageGenerateAsyncRequest.model_fields.keys())
        params_fields = set(ImageGenerationInputPayload.model_fields.keys())
        for field, value in style.items():
            if field in params_fields:
                request["params"][field] = value
            elif field in request_fields:
                request[field] = value
            elif field == 'enhance':
                pass
            else:
                raise KeyError(f"Unknown field: {field}")

        if not request["params"]:
            del request["params"]

        return request

    def test_styles(self) -> None:
        for style_name, style in self.styles.items():
            with self.subTest(style=style_name):
                request = self.style_to_request(style)
                self.validate_request(request)