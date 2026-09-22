from types import SimpleNamespace

from ai.routing import plan_route, translate_routed


class FakeResponses:
    def __init__(self, outputs):
        self.outputs = iter(outputs)

    def create(self, **_kwargs):
        text = next(self.outputs)
        usage = SimpleNamespace(input_tokens=10, output_tokens=4, total_tokens=14)
        return SimpleNamespace(output_text=text, usage=usage)


class FakeClient:
    def __init__(self, outputs):
        self.responses = FakeResponses(outputs)


def test_route_planning():
    assert plan_route("ja", "ko") == ("english_pivot", ["ja", "en", "ko"])
    assert plan_route("en", "fr") == ("direct", ["en", "fr"])
    assert plan_route("hi", "en") == ("direct", ["hi", "en"])
    assert plan_route("de", "de") == ("identity", ["de"])


def test_pivot_translation_aggregates_stages():
    result = translate_routed(
        source_text="こんにちは", source_language="Japanese", source_language_code="ja",
        target_language="Korean", target_language_code="ko",
        retry_count=1, retry_sleep=0, client=FakeClient(["Hello", "안녕하세요"]),
    )
    assert result.status == "success"
    assert result.route == ["ja", "en", "ko"]
    assert result.pivot_translation == "Hello"
    assert result.translated_text == "안녕하세요"
    assert len(result.stages) == 2
    assert result.total_tokens == 28


def test_identity_translation_uses_no_model_call():
    result = translate_routed(
        source_text="Hello", source_language="English", source_language_code="en",
        target_language="English", target_language_code="en",
    )
    assert result.translated_text == "Hello"
    assert result.total_tokens == 0
    assert result.stages == []
