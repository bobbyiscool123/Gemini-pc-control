"""Screenshot capture module."""

import base64
import os
import tempfile
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Dict

import mss
import mss.tools
from loguru import logger
from PIL import Image

from gemini_pc_control.config import default_config
from gemini_pc_control.logging_config import log_performance


class ScreenshotStore:
    """Store and manage screenshots."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the screenshot store."""
        self.storage_dir = storage_dir or os.path.join(default_config.app_dir, "screenshots")
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.debug(f"Initialized screenshot store at {self.storage_dir}")
    
    def store_screenshot(self, screenshot_data: bytes) -> str:
        """Store a screenshot and return its ID."""
        screenshot_id = str(uuid.uuid4())
        timestamp = int(time.time())
        filename = f"{timestamp}_{screenshot_id}.png"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(screenshot_data)
        
        logger.debug(f"Stored screenshot {screenshot_id} at {filepath}")
        return screenshot_id
    
    def get_screenshot(self, screenshot_id: str) -> Optional[bytes]:
        """Retrieve a screenshot by ID."""
        for filename in os.listdir(self.storage_dir):
            if screenshot_id in filename:
                filepath = os.path.join(self.storage_dir, filename)
                with open(filepath, "rb") as f:
                    return f.read()
        
        logger.warning(f"Screenshot {screenshot_id} not found")
        return None
    
    def cleanup_old_screenshots(self, max_age_days: int = 7) -> int:
        """Clean up screenshots older than the specified age."""
        deleted_count = 0
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith(".png"):
                continue
            
            try:
                timestamp_str = filename.split("_")[0]
                timestamp = int(timestamp_str)
                
                if current_time - timestamp > max_age_seconds:
                    filepath = os.path.join(self.storage_dir, filename)
                    os.remove(filepath)
                    deleted_count += 1
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing timestamp for file {filename}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} old screenshots")
        return deleted_count


class ScreenshotManager:
    """Manage screenshot capture and processing."""
    
    def __init__(self):
        """Initialize the screenshot manager."""
        self.screenshot_store = ScreenshotStore()
        logger.debug("Initialized screenshot manager")
    
    @log_performance
    def capture_screenshot(self, monitor_number: int = 1) -> Tuple[str, str]:
        """
        Capture a screenshot of the specified monitor.
        
        Returns:
            Tuple containing (screenshot_id, base64_encoded_data)
        """
        try:
            with mss.mss() as sct:
                # Get monitor information
                monitor = sct.monitors[monitor_number]
                logger.debug(f"Capturing screenshot of monitor {monitor_number}: {monitor}")
                
                # Capture screenshot
                sct_img = sct.grab(monitor)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                    mss.tools.to_png(sct_img.rgb, sct_img.size, output=tmp_file.name)
                    
                    # Read and encode the image
                    with open(tmp_file.name, "rb") as img_file:
                        img_bytes = img_file.read()
                    
                # Delete temporary file
                os.unlink(tmp_file.name)
                
                # Store the screenshot
                screenshot_id = self.screenshot_store.store_screenshot(img_bytes)
                
                # Encode to base64
                base64_data = base64.b64encode(img_bytes).decode('utf-8')
                
                logger.info(f"Screenshot captured successfully", screenshot_id=screenshot_id)
                return screenshot_id, base64_data
        
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}", exc_info=True)
            raise
    
    @log_performance
    def optimize_screenshot(
        self, 
        image_data: bytes, 
        max_size_kb: int = 1024, 
        max_dimension: int = 1920
    ) -> bytes:
        """
        Optimize a screenshot to reduce size while maintaining quality.
        
        Args:
            image_data: Raw image data
            max_size_kb: Maximum desired file size in KB
            max_dimension: Maximum dimension (width or height) in pixels
            
        Returns:
            Optimized image data
        """
        try:
            # Open image
            img = Image.open(BytesIO(image_data))
            original_size = len(image_data) / 1024  # Size in KB
            
            # Resize if needed
            width, height = img.size
            if width > max_dimension or height > max_dimension:
                scale = min(max_dimension / width, max_dimension / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Save with quality adjustments if needed
            quality = 95
            output = BytesIO()
            img.save(output, format="PNG", optimize=True)
            result_data = output.getvalue()
            result_size = len(result_data) / 1024  # Size in KB
            
            # Adjust quality if still too large (convert to JPEG if necessary)
            if result_size > max_size_kb and quality > 70:
                # Convert to JPEG for better compression
                output = BytesIO()
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                while quality > 70 and result_size > max_size_kb:
                    output = BytesIO()
                    img.save(output, format="JPEG", quality=quality, optimize=True)
                    result_data = output.getvalue()
                    result_size = len(result_data) / 1024
                    quality -= 5
                
                logger.debug(f"Compressed image to JPEG with quality {quality}")
            
            logger.info(f"Image optimized from {original_size:.1f}KB to {result_size:.1f}KB")
            return result_data
        
        except Exception as e:
            logger.error(f"Error optimizing screenshot: {e}", exc_info=True)
            return image_data  # Return original data if optimization fails 