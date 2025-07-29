from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
import cv2

class ImageProcessor:
    """Handles image processing operations for better PDF viewing and OCR"""
    
    def __init__(self):
        pass
    
    def adjust_contrast_brightness(self, image, contrast=1.0, brightness=1.0):
        """Adjust contrast and brightness of an image"""
        try:
            # Adjust brightness
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(brightness)
            
            # Adjust contrast
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(contrast)
            
            return image
            
        except Exception as e:
            print(f"Error adjusting contrast/brightness: {e}")
            return image
    
    def enhance_for_reading(self, image):
        """Apply enhancements specifically for better readability"""
        try:
            # Convert to grayscale if needed for processing
            if image.mode != 'L':
                gray_image = image.convert('L')
            else:
                gray_image = image.copy()
            
            # Apply histogram equalization for better contrast
            enhanced = ImageOps.equalize(gray_image)
            
            # Sharpen the image
            enhancer = ImageEnhance.Sharpness(enhanced)
            sharpened = enhancer.enhance(1.5)
            
            # Convert back to RGB if original was RGB
            if image.mode == 'RGB':
                # Convert grayscale back to RGB
                result = Image.new('RGB', sharpened.size)
                result.paste(sharpened)
                return result
            else:
                return sharpened
                
        except Exception as e:
            print(f"Error enhancing for reading: {e}")
            return image
    
    def darken_image(self, image, factor=0.8):
        """Darken an image by reducing brightness"""
        try:
            enhancer = ImageEnhance.Brightness(image)
            darkened = enhancer.enhance(factor)
            return darkened
            
        except Exception as e:
            print(f"Error darkening image: {e}")
            return image
    
    def increase_contrast(self, image, factor=1.5):
        """Increase contrast of an image"""
        try:
            enhancer = ImageEnhance.Contrast(image)
            high_contrast = enhancer.enhance(factor)
            return high_contrast
            
        except Exception as e:
            print(f"Error increasing contrast: {e}")
            return image
    
    def apply_threshold(self, image, threshold=128):
        """Apply binary threshold to image"""
        try:
            # Convert to grayscale
            gray_image = image.convert('L')
            
            # Apply threshold
            threshold_image = gray_image.point(lambda p: 255 if p > threshold else 0, mode='1')
            
            # Convert back to RGB
            result = Image.new('RGB', threshold_image.size, color='white')
            result.paste(threshold_image, mask=threshold_image)
            
            return result
            
        except Exception as e:
            print(f"Error applying threshold: {e}")
            return image
    
    def remove_noise(self, image):
        """Remove noise from image using filters"""
        try:
            # Apply median filter to remove noise
            filtered = image.filter(ImageFilter.MedianFilter(size=3))
            
            # Apply Gaussian blur for smoothing
            blurred = filtered.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            return blurred
            
        except Exception as e:
            print(f"Error removing noise: {e}")
            return image
    
    def auto_enhance(self, image):
        """Automatically enhance image for better visibility"""
        try:
            # Auto contrast
            enhanced = ImageOps.autocontrast(image)
            
            # Slight sharpening
            enhancer = ImageEnhance.Sharpness(enhanced)
            sharpened = enhancer.enhance(1.2)
            
            # Slight color enhancement if RGB
            if image.mode == 'RGB':
                enhancer = ImageEnhance.Color(sharpened)
                colored = enhancer.enhance(1.1)
                return colored
            
            return sharpened
            
        except Exception as e:
            print(f"Error auto-enhancing: {e}")
            return image
    
    def invert_colors(self, image):
        """Invert colors of the image (useful for dark backgrounds)"""
        try:
            inverted = ImageOps.invert(image.convert('RGB'))
            return inverted
            
        except Exception as e:
            print(f"Error inverting colors: {e}")
            return image
    
    def resize_image(self, image, max_width=1200, max_height=1600):
        """Resize image while maintaining aspect ratio"""
        try:
            original_width, original_height = image.size
            
            # Calculate resize ratio
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            resize_ratio = min(width_ratio, height_ratio, 1.0)  # Don't upscale
            
            if resize_ratio < 1.0:
                new_width = int(original_width * resize_ratio)
                new_height = int(original_height * resize_ratio)
                resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                return resized
            
            return image
            
        except Exception as e:
            print(f"Error resizing image: {e}")
            return image
    
    def crop_margins(self, image, margin_threshold=240):
        """Automatically crop white margins from image"""
        try:
            # Convert to grayscale for processing
            gray = image.convert('L')
            
            # Find bounding box of non-white content
            bbox = gray.getbbox()
            
            if bbox:
                # Add small margin back
                margin = 10
                left, top, right, bottom = bbox
                left = max(0, left - margin)
                top = max(0, top - margin)
                right = min(image.width, right + margin)
                bottom = min(image.height, bottom + margin)
                
                cropped = image.crop((left, top, right, bottom))
                return cropped
            
            return image
            
        except Exception as e:
            print(f"Error cropping margins: {e}")
            return image
