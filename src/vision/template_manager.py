"""Template Management System

Core template resolution and management for UI element detection.
Handles multiple template sources: base64, library, and multi-template strategies.
"""

import base64
import hashlib
import io
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


class TemplateStrategy(Enum):
    """Template resolution strategies"""

    BASE64 = "base64"
    LIBRARY = "library"
    MULTI = "multi"


@dataclass
class TemplateSource:
    """Template source with metadata and caching info"""

    strategy: TemplateStrategy
    template: np.ndarray
    metadata: dict[str, any] = field(default_factory=dict)
    confidence_weight: float = 1.0
    cache_key: str | None = None

    def __post_init__(self):
        """Generate cache key if not provided"""
        if self.cache_key is None:
            self.cache_key = self._generate_cache_key()

    def _generate_cache_key(self) -> str:
        """Generate unique cache key for this template"""
        # Create hash from template array and metadata
        template_hash = hashlib.sha256(self.template.tobytes()).hexdigest()[:16]
        strategy_key = self.strategy.value
        metadata_key = str(sorted(self.metadata.items()))[:32]
        return f"{strategy_key}_{template_hash}_{hashlib.sha256(metadata_key.encode()).hexdigest()[:8]}"


@dataclass
class TemplateRequest:
    """Template request specification"""

    strategy: TemplateStrategy
    data: str | dict[str, any]  # base64 string or library specification
    weight: float = 1.0
    required: bool = True
    name: str | None = None


class TemplateValidationError(Exception):
    """Raised when template validation fails"""


class TemplateManager:
    """Central template management system"""

    def __init__(self, cache_enabled: bool = True, library_path: Path | None = None):
        """Initialize template manager

        Args:
            cache_enabled: Enable template caching
            library_path: Path to template library directory
        """
        self.cache_enabled = cache_enabled
        self.library_path = library_path or Path(__file__).parent
        self._template_cache: dict[str, TemplateSource] = {}
        self._library_index: dict[str, any] | None = None

    def resolve_templates(
        self, request: TemplateRequest | list[TemplateRequest]
    ) -> list[TemplateSource]:
        """Resolve template request(s) to actual template sources

        Args:
            request: Single template request or list of requests

        Returns:
            List of resolved template sources

        Raises:
            TemplateValidationError: If template resolution fails
        """
        # Normalize to list
        if isinstance(request, TemplateRequest):
            requests = [request]
        else:
            requests = request

        resolved_templates = []

        for req in requests:
            try:
                template_source = self._resolve_single_request(req)
                resolved_templates.append(template_source)
            except Exception as e:
                if req.required:
                    raise TemplateValidationError(
                        f"Failed to resolve required template '{req.name}': {e}"
                    )
                # Skip optional templates that fail
                continue

        if not resolved_templates:
            raise TemplateValidationError("No templates could be resolved")

        return resolved_templates

    def _resolve_single_request(self, request: TemplateRequest) -> TemplateSource:
        """Resolve a single template request"""
        if request.strategy == TemplateStrategy.BASE64:
            return self._resolve_base64_template(request)
        elif request.strategy == TemplateStrategy.LIBRARY:
            return self._resolve_library_template(request)
        else:
            raise TemplateValidationError(f"Unsupported template strategy: {request.strategy}")

    def _resolve_base64_template(self, request: TemplateRequest) -> TemplateSource:
        """Resolve base64 template"""
        if not isinstance(request.data, str):
            raise TemplateValidationError("Base64 template data must be string")

        # Check cache first
        cache_key = f"base64_{hashlib.sha256(request.data.encode()).hexdigest()[:16]}"
        if self.cache_enabled and cache_key in self._template_cache:
            cached = self._template_cache[cache_key]
            cached.confidence_weight = request.weight
            return cached

        # Decode base64 to template
        template_array = self._decode_base64_image(request.data)
        self._validate_template(template_array)

        template_source = TemplateSource(
            strategy=TemplateStrategy.BASE64,
            template=template_array,
            confidence_weight=request.weight,
            cache_key=cache_key,
            metadata={
                "name": request.name or "base64_template",
                "source": "base64",
                "size": template_array.shape,
            },
        )

        # Cache template
        if self.cache_enabled:
            self._template_cache[cache_key] = template_source

        return template_source

    def _resolve_library_template(self, request: TemplateRequest) -> TemplateSource:
        """Resolve library template"""
        if not isinstance(request.data, dict) or "id" not in request.data:
            raise TemplateValidationError("Library template data must contain 'id' key")

        template_id = request.data["id"]
        category = request.data.get("category", "common")

        # Check cache first
        cache_key = f"library_{category}_{template_id}"
        if self.cache_enabled and cache_key in self._template_cache:
            cached = self._template_cache[cache_key]
            cached.confidence_weight = request.weight
            return cached

        # Load from library
        template_array = self._load_library_template(template_id, category)
        self._validate_template(template_array)

        template_source = TemplateSource(
            strategy=TemplateStrategy.LIBRARY,
            template=template_array,
            confidence_weight=request.weight,
            cache_key=cache_key,
            metadata={
                "name": request.name or template_id,
                "source": "library",
                "id": template_id,
                "category": category,
                "size": template_array.shape,
            },
        )

        # Cache template
        if self.cache_enabled:
            self._template_cache[cache_key] = template_source

        return template_source

    def _decode_base64_image(self, base64_data: str) -> np.ndarray:
        """Decode base64 string to OpenCV image array"""
        try:
            # Remove data URL prefix if present
            if base64_data.startswith("data:image"):
                base64_data = base64_data.split(",", 1)[1]

            # Decode base64
            image_bytes = base64.b64decode(base64_data)

            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            # Convert to numpy array
            image_array = np.array(pil_image)

            # Convert RGB to BGR for OpenCV
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

            return image_bgr

        except Exception as e:
            raise TemplateValidationError(f"Failed to decode base64 image: {e}")

    def _load_library_template(self, template_id: str, category: str = "common") -> np.ndarray:
        """Load template from library"""
        # Build template path
        template_path = self.library_path / "templates" / category / f"{template_id}.png"

        if not template_path.exists():
            # Try without category subdirectory
            template_path = self.library_path / "templates" / f"{template_id}.png"

        if not template_path.exists():
            raise TemplateValidationError(f"Template '{template_id}' not found in library")

        # Load image
        template = cv2.imread(str(template_path))
        if template is None:
            raise TemplateValidationError(f"Failed to load template image: {template_path}")

        return template

    def _validate_template(self, template: np.ndarray) -> None:
        """Validate template image"""
        if template is None:
            raise TemplateValidationError("Template is None")

        if template.size == 0:
            raise TemplateValidationError("Template is empty")

        height, width = template.shape[:2]

        if height < 5 or width < 5:
            raise TemplateValidationError(f"Template too small: {width}x{height} (minimum 5x5)")

        if height > 1000 or width > 1000:
            raise TemplateValidationError(
                f"Template too large: {width}x{height} (maximum 1000x1000)"
            )

    def clear_cache(self) -> None:
        """Clear template cache"""
        self._template_cache.clear()

    def get_cache_stats(self) -> dict[str, any]:
        """Get cache statistics"""
        return {
            "cached_templates": len(self._template_cache),
            "cache_enabled": self.cache_enabled,
            "library_path": str(self.library_path),
        }


# Global template manager instance
_global_template_manager: TemplateManager | None = None


def get_template_manager() -> TemplateManager:
    """Get global template manager instance"""
    global _global_template_manager
    if _global_template_manager is None:
        _global_template_manager = TemplateManager()
    return _global_template_manager


def set_template_manager(manager: TemplateManager) -> None:
    """Set global template manager instance"""
    global _global_template_manager
    _global_template_manager = manager
