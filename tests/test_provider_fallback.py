import pytest
from jarvis.ai.base import BaseAIProvider, AIResponse
from jarvis.ai.cloud_provider import CloudAIProvider
from jarvis.ai.local_provider import LocalAIProvider
from jarvis.ai.hybrid_manager import HybridAIManager


class MockFailingCloudProvider(BaseAIProvider):
    def is_available(self) -> bool:
        return True

    def get_provider_name(self) -> str:
        return "Mock Failing Cloud"

    def generate(self, messages, target_language="en") -> AIResponse:
        return AIResponse(
            text="Simulated Cloud Failure",
            success=False,
            provider_name=self.get_provider_name(),
            language=target_language,
            error_message="Connection refused",
        )


def test_unconfigured_cloud_provider():
    cloud = CloudAIProvider(api_key="")
    assert cloud.is_available() is False
    resp = cloud.generate([{"role": "user", "content": "Hello"}])
    assert resp.success is False
    assert "not configured" in resp.text.lower()


def test_hybrid_fallback_on_unconfigured_cloud():
    cloud = CloudAIProvider(api_key="")
    local = LocalAIProvider()
    hybrid = HybridAIManager(cloud_provider=cloud, local_provider=local)

    resp = hybrid.generate([{"role": "user", "content": "How are you?"}], target_language="en")
    assert resp.success is True
    assert "Local" in resp.provider_name
    assert "Offline Mode" in resp.text or "JARVIS" in resp.text


def test_hybrid_fallback_on_failing_cloud():
    failing_cloud = MockFailingCloudProvider()
    local = LocalAIProvider()
    hybrid = HybridAIManager(cloud_provider=failing_cloud, local_provider=local)

    resp = hybrid.generate([{"role": "user", "content": "Explain AI"}], target_language="de")
    assert resp.success is True
    # Falls back to local provider and formats response in German template
    assert "Local" in resp.provider_name
    assert resp.language == "de"
    assert "Lokales JARVIS-System" in resp.text
