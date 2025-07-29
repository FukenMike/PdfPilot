import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

class OCRHandler:
    """Handles OCR text extraction from images"""
    
    def __init__(self):
        # Configure Tesseract for better accuracy
        self.tesseract_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,!?@#$%^&*()_+-=[]{}|;:\'\"<>/~`'
        
        # Config for handwriting detection
        self.handwriting_config = r'--oem 3 --psm 8'
    
    def preprocess_image(self, image):
        """Preprocess image for better OCR accuracy"""
        try:
            # Convert PIL image to numpy array
            img_array = np.array(image)
            
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up the image
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(cleaned)
            
            return processed_image
            
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return image
    
    def enhance_image_for_ocr(self, image):
        """Apply various enhancements to improve OCR accuracy"""
        try:
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(1.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = enhancer.enhance(2.0)
            
            # Apply unsharp mask filter
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
            
            return enhanced
            
        except Exception as e:
            print(f"Error enhancing image: {e}")
            return image
    
    def extract_text_from_image(self, image):
        """Extract text from image using OCR"""
        try:
            # Preprocess the image
            processed_image = self.preprocess_image(image)
            
            # Enhance the image
            enhanced_image = self.enhance_image_for_ocr(processed_image)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(enhanced_image, config=self.tesseract_config)
            
            # If no text found with standard config, try handwriting config
            if not text.strip():
                text = pytesseract.image_to_string(enhanced_image, config=self.handwriting_config)
            
            return text.strip()
            
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""
    
    def extract_text_with_confidence(self, image):
        """Extract text with confidence scores"""
        try:
            processed_image = self.preprocess_image(image)
            enhanced_image = self.enhance_image_for_ocr(processed_image)
            
            # Get detailed data including confidence scores
            data = pytesseract.image_to_data(enhanced_image, output_type=pytesseract.Output.DICT)
            
            # Filter out low confidence text
            min_confidence = 30
            filtered_text = []
            
            for i in range(len(data['text'])):
                confidence = int(data['conf'][i])
                text = data['text'][i].strip()
                
                if confidence > min_confidence and text:
                    filtered_text.append(text)
            
            return ' '.join(filtered_text)
            
        except Exception as e:
            print(f"Error extracting text with confidence: {e}")
            return ""
    
    def detect_handwriting(self, image):
        """Attempt to detect and extract handwritten text"""
        try:
            # Use specific config for handwriting
            text = pytesseract.image_to_string(image, config=self.handwriting_config)
            return text.strip()
            
        except Exception as e:
            print(f"Error detecting handwriting: {e}")
            return ""
    
    def get_text_boxes(self, image):
        """Get bounding boxes for detected text"""
        try:
            processed_image = self.preprocess_image(image)
            
            # Get bounding box data
            boxes = pytesseract.image_to_boxes(processed_image)
            
            text_boxes = []
            for box in boxes.splitlines():
                box_data = box.split(' ')
                if len(box_data) >= 6:
                    char = box_data[0]
                    x1, y1, x2, y2 = map(int, box_data[1:5])
                    text_boxes.append({
                        'char': char,
                        'bbox': (x1, y1, x2, y2)
                    })
            
            return text_boxes
            
        except Exception as e:
            print(f"Error getting text boxes: {e}")
            return []
