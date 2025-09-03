"""PaddleOCR wrapper for text recognition in UI elements"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import paddleocr


@dataclass
class TextDetection:
    """Text detection and recognition result"""
    text: str
    confidence: float
    bbox: List[Tuple[int, int]]  # 4 corner points
    rect_bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]


class OCRReader:
    """PaddleOCR wrapper for text recognition"""
    
    def __init__(self, use_gpu: bool = False, lang: str = "en"):
        """Initialize PaddleOCR"""
        self.ocr = paddleocr.PaddleOCR(
            lang=lang
        )
        print(f"PaddleOCR initialized (GPU: {use_gpu}, Lang: {lang})")
    
    def read_text(self, image: np.ndarray, region: Optional[Tuple[int, int, int, int]] = None) -> List[TextDetection]:
        """
        Read text from image or specific region
        
        Args:
            image: Input image
            region: Optional region (x1, y1, x2, y2) to crop before OCR
        
        Returns:
            List of TextDetection objects
        """
        # Crop region if specified
        if region:
            x1, y1, x2, y2 = region
            cropped_image = image[y1:y2, x1:x2]
            offset_x, offset_y = x1, y1
        else:
            cropped_image = image
            offset_x, offset_y = 0, 0
        
        # Run OCR
        try:
            results = self.ocr.ocr(cropped_image, cls=True)
            
            if not results or not results[0]:
                return []
            
            text_detections = []
            
            for line in results[0]:
                if not line:
                    continue
                
                bbox_points, (text, confidence) = line
                
                if confidence < 0.5:  # Skip low confidence text
                    continue
                
                # Convert bbox points to absolute coordinates
                abs_bbox_points = [(int(x + offset_x), int(y + offset_y)) for x, y in bbox_points]
                
                # Calculate rectangular bounding box
                x_coords = [point[0] for point in abs_bbox_points]
                y_coords = [point[1] for point in abs_bbox_points]
                
                x1, y1 = min(x_coords), min(y_coords)
                x2, y2 = max(x_coords), max(y_coords)
                
                # Calculate center
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                text_detection = TextDetection(
                    text=text.strip(),
                    confidence=confidence,
                    bbox=abs_bbox_points,
                    rect_bbox=(x1, y1, x2, y2),
                    center=(center_x, center_y)
                )
                
                text_detections.append(text_detection)
            
            return text_detections
            
        except Exception as e:
            print(f"OCR error: {e}")
            return []
    
    def find_text(self, image: np.ndarray, target_text: str, threshold: float = 0.8) -> List[TextDetection]:
        """
        Find specific text in image
        
        Args:
            image: Input image
            target_text: Text to search for
            threshold: Similarity threshold (0-1)
        
        Returns:
            List of matching TextDetection objects
        """
        all_text = self.read_text(image)
        matches = []
        
        target_lower = target_text.lower().strip()
        
        for text_det in all_text:
            detected_lower = text_det.text.lower().strip()
            
            # Simple substring matching
            if target_lower in detected_lower or detected_lower in target_lower:
                matches.append(text_det)
            
            # Fuzzy matching could be added here for better accuracy
            # using libraries like fuzzywuzzy
        
        return matches
    
    def read_field_value(self, image: np.ndarray, field_region: Tuple[int, int, int, int]) -> Optional[str]:
        """
        Read text from a specific field region (e.g., input box)
        
        Args:
            image: Input image
            field_region: Region coordinates (x1, y1, x2, y2)
        
        Returns:
            Detected text or None
        """
        text_detections = self.read_text(image, field_region)
        
        if not text_detections:
            return None
        
        # Return the text with highest confidence
        best_detection = max(text_detections, key=lambda x: x.confidence)
        return best_detection.text
    
    def draw_text_detections(self, image: np.ndarray, text_detections: List[TextDetection]) -> np.ndarray:
        """Draw text detection results on image"""
        result_image = image.copy()
        
        for text_det in text_detections:
            # Draw bounding box
            bbox_points = np.array(text_det.bbox, dtype=np.int32)
            cv2.polylines(result_image, [bbox_points], True, (255, 0, 0), 2)
            
            # Draw text label
            x1, y1, x2, y2 = text_det.rect_bbox
            label = f"{text_det.text} ({text_det.confidence:.2f})"
            
            # Background for text
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(result_image, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (255, 0, 0), -1)
            
            # Text
            cv2.putText(result_image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return result_image
    
    def get_text_near_point(self, image: np.ndarray, point: Tuple[int, int], radius: int = 50) -> List[TextDetection]:
        """
        Get text detections near a specific point
        
        Args:
            image: Input image
            point: Center point (x, y)
            radius: Search radius in pixels
        
        Returns:
            List of nearby TextDetection objects
        """
        all_text = self.read_text(image)
        nearby_text = []
        
        px, py = point
        
        for text_det in all_text:
            tx, ty = text_det.center
            distance = ((tx - px) ** 2 + (ty - py) ** 2) ** 0.5
            
            if distance <= radius:
                nearby_text.append(text_det)
        
        return nearby_text