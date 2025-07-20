import os
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageGrab
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ScreenCaptureService:
    """Service for capturing and analyzing screen activity"""
    
    def __init__(self, storage_path: str = "./screen_captures"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.capture_interval = 30  # seconds
        self.is_capturing = False
        
    async def start_capture_loop(self, user_id: str, analyze_callback=None):
        """Start continuous screen capture loop"""
        self.is_capturing = True
        
        while self.is_capturing:
            try:
                # Capture screen
                screenshot = self.capture_screen()
                
                # Analyze the screenshot
                analysis = await self.analyze_screenshot(screenshot, user_id)
                
                # Call the callback if provided
                if analyze_callback:
                    await analyze_callback(user_id, analysis)
                
                # Wait for next capture
                await asyncio.sleep(self.capture_interval)
                
            except Exception as e:
                logger.error(f"Error in screen capture loop: {str(e)}")
                await asyncio.sleep(self.capture_interval)
    
    def stop_capture(self):
        """Stop the capture loop"""
        self.is_capturing = False
    
    def capture_screen(self) -> np.ndarray:
        """Capture the current screen"""
        try:
            # Capture screen using PIL
            screenshot = ImageGrab.grab()
            
            # Convert to numpy array for OpenCV
            screenshot_np = np.array(screenshot)
            
            # Convert RGB to BGR for OpenCV
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            return screenshot_bgr
            
        except Exception as e:
            logger.error(f"Error capturing screen: {str(e)}")
            raise
    
    async def analyze_screenshot(self, screenshot: np.ndarray, user_id: str) -> Dict[str, Any]:
        """Analyze a screenshot for activity patterns"""
        timestamp = datetime.utcnow()
        
        # Generate hash for deduplication
        screenshot_hash = self._generate_hash(screenshot)
        
        # Basic analysis
        analysis = {
            "timestamp": timestamp.isoformat(),
            "screenshot_hash": screenshot_hash,
            "dimensions": screenshot.shape[:2],
            "dominant_colors": self._extract_dominant_colors(screenshot),
            "brightness": self._calculate_brightness(screenshot),
            "activity_regions": self._detect_activity_regions(screenshot),
            "text_regions": await self._extract_text_regions(screenshot),
            "window_detection": self._detect_windows(screenshot),
            "ui_elements": self._detect_ui_elements(screenshot)
        }
        
        # Application detection
        analysis["detected_applications"] = self._detect_applications(analysis)
        
        # Activity classification
        analysis["activity_type"] = self._classify_activity(analysis)
        
        # Save screenshot if significant
        if self._is_significant_change(screenshot_hash, user_id):
            screenshot_path = self._save_screenshot(screenshot, user_id, timestamp)
            analysis["screenshot_path"] = str(screenshot_path)
        
        return analysis
    
    def _generate_hash(self, image: np.ndarray) -> str:
        """Generate a hash for the image for deduplication"""
        # Resize to small size for faster hashing
        small = cv2.resize(image, (64, 64))
        
        # Convert to grayscale
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # Calculate hash
        return hashlib.md5(gray.tobytes()).hexdigest()
    
    def _extract_dominant_colors(self, image: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Extract dominant colors from the image"""
        # Reshape image to list of pixels
        pixels = image.reshape((-1, 3))
        
        # Sample pixels for performance
        sample_size = min(5000, len(pixels))
        sample_indices = np.random.choice(len(pixels), sample_size, replace=False)
        sample_pixels = pixels[sample_indices]
        
        # K-means clustering for dominant colors
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(sample_pixels)
        
        # Get color percentages
        labels = kmeans.labels_
        unique, counts = np.unique(labels, return_counts=True)
        
        colors = []
        for i, count in zip(unique, counts):
            color = kmeans.cluster_centers_[i]
            percentage = count / len(labels) * 100
            colors.append({
                "rgb": color.astype(int).tolist(),
                "percentage": round(percentage, 2)
            })
        
        return sorted(colors, key=lambda x: x["percentage"], reverse=True)
    
    def _calculate_brightness(self, image: np.ndarray) -> float:
        """Calculate average brightness of the image"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate mean brightness
        brightness = np.mean(gray) / 255.0
        
        return round(brightness, 3)
    
    def _detect_activity_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect regions of high activity/change"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and sort contours by area
        regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Minimum area threshold
                x, y, w, h = cv2.boundingRect(contour)
                regions.append({
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h),
                    "area": int(area)
                })
        
        # Sort by area and return top regions
        regions.sort(key=lambda r: r["area"], reverse=True)
        return regions[:10]
    
    async def _extract_text_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Extract text regions using OCR"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Use pytesseract to get text regions
            data = pytesseract.image_to_data(binary, output_type=pytesseract.Output.DICT)
            
            text_regions = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                if int(data['conf'][i]) > 60:  # Confidence threshold
                    text = data['text'][i].strip()
                    if text:
                        text_regions.append({
                            "text": text[:50],  # Limit text length for privacy
                            "confidence": data['conf'][i],
                            "x": data['left'][i],
                            "y": data['top'][i],
                            "width": data['width'][i],
                            "height": data['height'][i]
                        })
            
            return text_regions[:20]  # Limit number of regions
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return []
    
    def _detect_windows(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect window-like structures in the screenshot"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect lines using HoughLines
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
        
        windows = []
        if lines is not None:
            # Group lines into potential windows
            # This is a simplified approach - real window detection would be more complex
            horizontal_lines = []
            vertical_lines = []
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                
                if angle < 10 or angle > 170:  # Horizontal
                    horizontal_lines.append((x1, y1, x2, y2))
                elif 80 < angle < 100:  # Vertical
                    vertical_lines.append((x1, y1, x2, y2))
            
            # Simple window detection based on line intersections
            # In practice, this would need more sophisticated logic
            if len(horizontal_lines) > 2 and len(vertical_lines) > 2:
                windows.append({
                    "type": "detected_window",
                    "confidence": 0.7,
                    "line_count": len(horizontal_lines) + len(vertical_lines)
                })
        
        return windows
    
    def _detect_ui_elements(self, image: np.ndarray) -> Dict[str, int]:
        """Detect common UI elements"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        ui_elements = {
            "buttons": 0,
            "text_fields": 0,
            "menus": 0,
            "icons": 0
        }
        
        # Simple heuristic-based detection
        # Look for rectangular regions with specific aspect ratios
        
        # Find contours
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            area = w * h
            
            # Button-like elements
            if 2 < aspect_ratio < 6 and 500 < area < 5000:
                ui_elements["buttons"] += 1
            
            # Text field-like elements
            elif 5 < aspect_ratio < 20 and 1000 < area < 10000:
                ui_elements["text_fields"] += 1
            
            # Icon-like elements
            elif 0.8 < aspect_ratio < 1.2 and 100 < area < 2000:
                ui_elements["icons"] += 1
        
        return ui_elements
    
    def _detect_applications(self, analysis: Dict[str, Any]) -> List[str]:
        """Detect applications based on visual features"""
        detected_apps = []
        
        # Check dominant colors for application hints
        colors = analysis.get("dominant_colors", [])
        
        # Simple heuristics based on color schemes
        for color in colors:
            rgb = color["rgb"]
            
            # Dark theme IDE/Code editor
            if all(c < 50 for c in rgb) and analysis.get("text_regions", []):
                detected_apps.append("code_editor")
            
            # Browser (usually lighter backgrounds)
            elif all(c > 200 for c in rgb) and len(analysis.get("text_regions", [])) > 10:
                detected_apps.append("web_browser")
            
            # Slack (purple tones)
            elif 100 < rgb[0] < 150 and rgb[2] > 150:
                detected_apps.append("slack")
        
        # Check UI elements
        ui_elements = analysis.get("ui_elements", {})
        
        if ui_elements.get("buttons", 0) > 5 and ui_elements.get("text_fields", 0) > 2:
            detected_apps.append("form_application")
        
        return list(set(detected_apps))
    
    def _classify_activity(self, analysis: Dict[str, Any]) -> str:
        """Classify the type of activity based on analysis"""
        detected_apps = analysis.get("detected_applications", [])
        text_regions = len(analysis.get("text_regions", []))
        brightness = analysis.get("brightness", 0.5)
        
        # Classification logic
        if "code_editor" in detected_apps:
            return "coding"
        elif "web_browser" in detected_apps:
            if text_regions > 20:
                return "reading"
            else:
                return "browsing"
        elif "slack" in detected_apps or "form_application" in detected_apps:
            return "communication"
        elif text_regions > 15:
            return "document_work"
        elif brightness < 0.2:
            return "idle_or_locked"
        else:
            return "other"
    
    def _is_significant_change(self, screenshot_hash: str, user_id: str) -> bool:
        """Check if this screenshot represents a significant change"""
        # Simple implementation - check if hash is different from last capture
        cache_file = self.storage_path / f"{user_id}_last_hash.txt"
        
        if cache_file.exists():
            last_hash = cache_file.read_text().strip()
            if last_hash == screenshot_hash:
                return False
        
        # Update cache
        cache_file.write_text(screenshot_hash)
        return True
    
    def _save_screenshot(self, image: np.ndarray, user_id: str, timestamp: datetime) -> Path:
        """Save screenshot to disk"""
        # Create user directory
        user_dir = self.storage_path / user_id
        user_dir.mkdir(exist_ok=True)
        
        # Create date-based subdirectory
        date_dir = user_dir / timestamp.strftime("%Y-%m-%d")
        date_dir.mkdir(exist_ok=True)
        
        # Save image
        filename = f"{timestamp.strftime('%H-%M-%S')}.jpg"
        filepath = date_dir / filename
        
        # Resize for storage efficiency
        height, width = image.shape[:2]
        if width > 1920:
            scale = 1920 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))
        
        # Save with compression
        cv2.imwrite(str(filepath), image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        return filepath
    
    async def get_activity_summary(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get summary of screen activity for the past N hours"""
        # This would query stored analysis data
        # For now, return a mock summary
        return {
            "total_captures": 0,
            "activity_breakdown": {
                "coding": 0,
                "browsing": 0,
                "reading": 0,
                "communication": 0,
                "document_work": 0,
                "other": 0
            },
            "active_hours": 0,
            "most_used_applications": []
        }