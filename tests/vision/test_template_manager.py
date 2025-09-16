"""
Unit tests for template management module.
"""

import base64
import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import pytest
from PIL import Image

from src.vision.template_manager import (
    TemplateManager,
    TemplateRequest,
    TemplateSource,
    TemplateStrategy,
    TemplateValidationError,
    get_template_manager,
    set_template_manager,
)


class TestTemplateStrategy:
    """Tests for TemplateStrategy enum."""

    def test_strategy_values(self):
        """Test enum values are correct."""
        assert TemplateStrategy.BASE64.value == "base64"
        assert TemplateStrategy.LIBRARY.value == "library"
        assert TemplateStrategy.MULTI.value == "multi"


class TestTemplateSource:
    """Tests for TemplateSource dataclass."""

    def test_template_source_creation(self):
        """Test TemplateSource creation with required fields."""
        template = np.ones((20, 20), dtype=np.uint8)
        source = TemplateSource(strategy=TemplateStrategy.BASE64, template=template)

        assert source.strategy == TemplateStrategy.BASE64
        assert np.array_equal(source.template, template)
        assert source.metadata == {}
        assert source.confidence_weight == 1.0
        assert source.cache_key is not None

    def test_template_source_with_metadata(self):
        """Test TemplateSource with custom metadata."""
        template = np.ones((20, 20), dtype=np.uint8)
        metadata = {"name": "test", "category": "buttons"}

        source = TemplateSource(
            strategy=TemplateStrategy.LIBRARY,
            template=template,
            metadata=metadata,
            confidence_weight=0.8,
        )

        assert source.metadata == metadata
        assert source.confidence_weight == 0.8

    def test_cache_key_generation(self):
        """Test automatic cache key generation."""
        template = np.ones((20, 20), dtype=np.uint8)
        source1 = TemplateSource(TemplateStrategy.BASE64, template)
        source2 = TemplateSource(TemplateStrategy.BASE64, template)

        # Same template should generate same cache key
        assert source1.cache_key == source2.cache_key

    def test_different_templates_different_keys(self):
        """Test different templates generate different cache keys."""
        template1 = np.ones((20, 20), dtype=np.uint8)
        template2 = np.zeros((20, 20), dtype=np.uint8)

        source1 = TemplateSource(TemplateStrategy.BASE64, template1)
        source2 = TemplateSource(TemplateStrategy.BASE64, template2)

        assert source1.cache_key != source2.cache_key

    def test_custom_cache_key(self):
        """Test providing custom cache key."""
        template = np.ones((20, 20), dtype=np.uint8)
        custom_key = "custom_key_123"

        source = TemplateSource(TemplateStrategy.BASE64, template, cache_key=custom_key)

        assert source.cache_key == custom_key


class TestTemplateRequest:
    """Tests for TemplateRequest dataclass."""

    def test_template_request_creation(self):
        """Test TemplateRequest creation."""
        request = TemplateRequest(strategy=TemplateStrategy.BASE64, data="base64_string_here")

        assert request.strategy == TemplateStrategy.BASE64
        assert request.data == "base64_string_here"
        assert request.weight == 1.0
        assert request.required == True
        assert request.name is None

    def test_template_request_with_options(self):
        """Test TemplateRequest with optional parameters."""
        request = TemplateRequest(
            strategy=TemplateStrategy.LIBRARY,
            data={"id": "button", "category": "ui"},
            weight=0.75,
            required=False,
            name="login_button",
        )

        assert request.weight == 0.75
        assert request.required == False
        assert request.name == "login_button"


class TestTemplateManager:
    """Tests for TemplateManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = TemplateManager(cache_enabled=True, library_path=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_manager_initialization(self):
        """Test TemplateManager initialization."""
        manager = TemplateManager()
        assert manager.cache_enabled == True
        assert isinstance(manager.library_path, Path)
        assert manager._template_cache == {}

    def test_manager_with_custom_settings(self):
        """Test TemplateManager with custom settings."""
        custom_path = Path("/custom/path")
        manager = TemplateManager(cache_enabled=False, library_path=custom_path)

        assert manager.cache_enabled == False
        assert manager.library_path == custom_path

    def create_test_base64_image(self):
        """Helper to create test base64 image."""
        # Create test image
        image = np.zeros((50, 50, 3), dtype=np.uint8)
        image[20:30, 20:30] = [255, 255, 255]  # White square

        # Convert to PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def test_resolve_single_base64_template(self):
        """Test resolving single base64 template."""
        manager = TemplateManager()
        base64_data = self.create_test_base64_image()

        request = TemplateRequest(
            strategy=TemplateStrategy.BASE64, data=base64_data, name="test_template"
        )

        sources = manager.resolve_templates(request)

        assert len(sources) == 1
        source = sources[0]
        assert source.strategy == TemplateStrategy.BASE64
        assert source.template.shape == (50, 50, 3)
        assert source.metadata["name"] == "test_template"

    def test_resolve_base64_with_data_url_prefix(self):
        """Test resolving base64 template with data URL prefix."""
        manager = TemplateManager()
        base64_data = self.create_test_base64_image()
        data_url = f"data:image/png;base64,{base64_data}"

        request = TemplateRequest(strategy=TemplateStrategy.BASE64, data=data_url)

        sources = manager.resolve_templates(request)
        assert len(sources) == 1
        assert sources[0].template.shape == (50, 50, 3)

    def test_resolve_invalid_base64(self):
        """Test resolving invalid base64 data."""
        manager = TemplateManager()

        request = TemplateRequest(strategy=TemplateStrategy.BASE64, data="invalid_base64_data")

        with pytest.raises(TemplateValidationError, match="Failed to decode base64 image"):
            manager.resolve_templates(request)

    def test_resolve_base64_non_string_data(self):
        """Test resolving base64 with non-string data."""
        manager = TemplateManager()

        request = TemplateRequest(
            strategy=TemplateStrategy.BASE64,
            data=123,  # Not a string
        )

        with pytest.raises(TemplateValidationError, match="Base64 template data must be string"):
            manager.resolve_templates(request)

    @patch("cv2.imread")
    def test_resolve_library_template_success(self, mock_imread):
        """Test successful library template resolution."""
        # Setup mock
        mock_template = np.ones((64, 64, 3), dtype=np.uint8) * 128
        mock_imread.return_value = mock_template

        manager = TemplateManager(library_path=Path("/fake/path"))

        request = TemplateRequest(
            strategy=TemplateStrategy.LIBRARY,
            data={"id": "button", "category": "ui"},
            name="submit_button",
        )

        sources = manager.resolve_templates(request)

        assert len(sources) == 1
        source = sources[0]
        assert source.strategy == TemplateStrategy.LIBRARY
        assert np.array_equal(source.template, mock_template)
        assert source.metadata["name"] == "submit_button"
        assert source.metadata["id"] == "button"
        assert source.metadata["category"] == "ui"

    def test_resolve_library_template_missing_id(self):
        """Test library template with missing id."""
        manager = TemplateManager()

        request = TemplateRequest(
            strategy=TemplateStrategy.LIBRARY,
            data={"category": "ui"},  # Missing 'id'
        )

        with pytest.raises(
            TemplateValidationError, match="Library template data must contain 'id' key"
        ):
            manager.resolve_templates(request)

    def test_resolve_library_template_non_dict_data(self):
        """Test library template with non-dict data."""
        manager = TemplateManager()

        request = TemplateRequest(strategy=TemplateStrategy.LIBRARY, data="not_a_dict")

        with pytest.raises(
            TemplateValidationError, match="Library template data must contain 'id' key"
        ):
            manager.resolve_templates(request)

    @patch("cv2.imread")
    def test_resolve_library_template_file_not_found(self, mock_imread):
        """Test library template when file not found."""
        mock_imread.return_value = None  # cv2.imread returns None when file not found

        manager = TemplateManager(library_path=Path("/fake/path"))

        request = TemplateRequest(strategy=TemplateStrategy.LIBRARY, data={"id": "nonexistent"})

        with pytest.raises(TemplateValidationError, match="Failed to load template image"):
            manager.resolve_templates(request)

    def test_resolve_multiple_templates(self):
        """Test resolving multiple templates."""
        manager = TemplateManager()
        base64_data = self.create_test_base64_image()

        requests = [
            TemplateRequest(strategy=TemplateStrategy.BASE64, data=base64_data, name="template1"),
            TemplateRequest(strategy=TemplateStrategy.BASE64, data=base64_data, name="template2"),
        ]

        sources = manager.resolve_templates(requests)

        assert len(sources) == 2
        assert sources[0].metadata["name"] == "template1"
        assert sources[1].metadata["name"] == "template2"

    def test_resolve_templates_with_optional_failure(self):
        """Test resolving templates where optional template fails."""
        manager = TemplateManager()
        base64_data = self.create_test_base64_image()

        requests = [
            TemplateRequest(
                strategy=TemplateStrategy.BASE64,
                data=base64_data,
                name="good_template",
                required=True,
            ),
            TemplateRequest(
                strategy=TemplateStrategy.BASE64,
                data="invalid_base64",
                name="bad_template",
                required=False,  # Optional
            ),
        ]

        sources = manager.resolve_templates(requests)

        # Should only return the successful template
        assert len(sources) == 1
        assert sources[0].metadata["name"] == "good_template"

    def test_resolve_templates_with_required_failure(self):
        """Test resolving templates where required template fails."""
        manager = TemplateManager()

        requests = [
            TemplateRequest(
                strategy=TemplateStrategy.BASE64,
                data="invalid_base64",
                name="required_template",
                required=True,  # Required
            )
        ]

        with pytest.raises(TemplateValidationError, match="Failed to resolve required template"):
            manager.resolve_templates(requests)

    def test_resolve_templates_all_fail(self):
        """Test resolving templates when all fail."""
        manager = TemplateManager()

        requests = [
            TemplateRequest(strategy=TemplateStrategy.BASE64, data="invalid1", required=False),
            TemplateRequest(strategy=TemplateStrategy.BASE64, data="invalid2", required=False),
        ]

        with pytest.raises(TemplateValidationError, match="No templates could be resolved"):
            manager.resolve_templates(requests)

    def test_unsupported_strategy(self):
        """Test unsupported template strategy."""
        manager = TemplateManager()

        # Create a request with an unsupported strategy
        request = TemplateRequest(
            strategy=TemplateStrategy.MULTI,  # Not implemented
            data={},
        )

        with pytest.raises(TemplateValidationError, match="Unsupported template strategy"):
            manager.resolve_templates(request)

    def test_template_caching(self):
        """Test template caching functionality."""
        manager = TemplateManager(cache_enabled=True)
        base64_data = self.create_test_base64_image()

        request = TemplateRequest(strategy=TemplateStrategy.BASE64, data=base64_data)

        # First resolution
        sources1 = manager.resolve_templates(request)
        cache_stats = manager.get_cache_stats()
        assert cache_stats["cached_templates"] == 1

        # Second resolution should use cache
        sources2 = manager.resolve_templates(request)
        assert len(sources2) == 1
        assert sources1[0].cache_key == sources2[0].cache_key

    def test_cache_disabled(self):
        """Test template manager with caching disabled."""
        manager = TemplateManager(cache_enabled=False)
        base64_data = self.create_test_base64_image()

        request = TemplateRequest(strategy=TemplateStrategy.BASE64, data=base64_data)

        sources = manager.resolve_templates(request)
        cache_stats = manager.get_cache_stats()

        assert len(sources) == 1
        assert cache_stats["cached_templates"] == 0
        assert cache_stats["cache_enabled"] == False

    def test_clear_cache(self):
        """Test clearing template cache."""
        manager = TemplateManager(cache_enabled=True)
        base64_data = self.create_test_base64_image()

        request = TemplateRequest(strategy=TemplateStrategy.BASE64, data=base64_data)

        # Add something to cache
        manager.resolve_templates(request)
        assert manager.get_cache_stats()["cached_templates"] == 1

        # Clear cache
        manager.clear_cache()
        assert manager.get_cache_stats()["cached_templates"] == 0

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        library_path = Path("/test/path")
        manager = TemplateManager(cache_enabled=True, library_path=library_path)

        stats = manager.get_cache_stats()

        assert "cached_templates" in stats
        assert "cache_enabled" in stats
        assert "library_path" in stats
        assert stats["cache_enabled"] == True
        assert stats["library_path"] == str(library_path)
        assert isinstance(stats["cached_templates"], int)

    def test_template_validation_none_template(self):
        """Test template validation with None template."""
        manager = TemplateManager()

        with patch.object(manager, "_decode_base64_image", return_value=None):
            request = TemplateRequest(strategy=TemplateStrategy.BASE64, data="fake_base64")

            with pytest.raises(TemplateValidationError, match="Template is None"):
                manager.resolve_templates(request)

    def test_template_validation_empty_template(self):
        """Test template validation with empty template."""
        manager = TemplateManager()
        empty_template = np.array([])  # Empty array

        with patch.object(manager, "_decode_base64_image", return_value=empty_template):
            request = TemplateRequest(strategy=TemplateStrategy.BASE64, data="fake_base64")

            with pytest.raises(TemplateValidationError, match="Template is empty"):
                manager.resolve_templates(request)

    def test_template_validation_too_small(self):
        """Test template validation with too small template."""
        manager = TemplateManager()
        small_template = np.ones((3, 3), dtype=np.uint8)  # Too small (< 5x5)

        with patch.object(manager, "_decode_base64_image", return_value=small_template):
            request = TemplateRequest(strategy=TemplateStrategy.BASE64, data="fake_base64")

            with pytest.raises(TemplateValidationError, match="Template too small"):
                manager.resolve_templates(request)

    def test_template_validation_too_large(self):
        """Test template validation with too large template."""
        manager = TemplateManager()
        large_template = np.ones((1500, 1500), dtype=np.uint8)  # Too large (> 1000x1000)

        with patch.object(manager, "_decode_base64_image", return_value=large_template):
            request = TemplateRequest(strategy=TemplateStrategy.BASE64, data="fake_base64")

            with pytest.raises(TemplateValidationError, match="Template too large"):
                manager.resolve_templates(request)


class TestGlobalTemplateManager:
    """Tests for global template manager functions."""

    def test_get_template_manager_singleton(self):
        """Test global template manager is singleton."""
        manager1 = get_template_manager()
        manager2 = get_template_manager()

        assert manager1 is manager2
        assert isinstance(manager1, TemplateManager)

    def test_set_template_manager(self):
        """Test setting custom global template manager."""
        custom_manager = TemplateManager(cache_enabled=False)

        set_template_manager(custom_manager)
        retrieved_manager = get_template_manager()

        assert retrieved_manager is custom_manager
        assert retrieved_manager.cache_enabled == False

    def teardown_method(self):
        """Reset global manager after each test."""
        # Reset global manager to avoid test interference
        import src.vision.template_manager as tm

        tm._global_template_manager = None


class TestTemplateValidationError:
    """Tests for TemplateValidationError exception."""

    def test_template_validation_error(self):
        """Test TemplateValidationError exception."""
        error_message = "Test validation error"

        with pytest.raises(TemplateValidationError) as exc_info:
            raise TemplateValidationError(error_message)

        assert str(exc_info.value) == error_message


if __name__ == "__main__":
    pytest.main([__file__])
