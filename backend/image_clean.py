import cv2 as cv
import numpy as np


class ImageProcessor:

    def __init__(
        self,
        target_size=(768, 768),   # Desired output size for images
        jpeg_quality=80,          # JPEG compression quality (0–100)
        clahe_clip=2.0,           # Contrast limit for CLAHE
        clahe_grid=(8, 8)         # Grid size for CLAHE tiles
    ):
        # Store target size and JPEG quality
        self.target_size = target_size
        self.jpeg_quality = jpeg_quality

        self.clahe = cv.createCLAHE(
            clipLimit=clahe_clip,
            tileGridSize=clahe_grid
        )

    
    def load_image(self, img_input):
        # Load image from file path or numpy array
        if isinstance(img_input, str):
            img = cv.imread(img_input) 
        elif isinstance(img_input, np.ndarray):
            img = img_input
        else:
            raise ValueError(
                "Unsupported input type. "
                "Provide file path or numpy array."
            )
        
        # Ensure image was successfully loaded
        if img is None:
            raise ValueError("Could not load image.")
        return img

   
    def grayscale(self, img): 
        # Convert to grayscale
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
       
        # Apply noise reduction
        gray = cv.fastNlMeansDenoising(gray)

        # Apply clahe for contrast enhancement
        gray = self.clahe.apply(gray)
        return gray

    
    def resize(self, img):
        # Get original dimensions
        h, w = img.shape[:2]
        target_w, target_h = self.target_size

        # Compute scaling factor to fit within target size
        scale = min(target_w / w, target_h / h)

        # Prevent upscaling
        scale = min(scale, 1.0)

        # Compute new dimensions
        new_w = int(w * scale)
        new_h = int(h * scale)

        # Resize image
        resized = cv.resize(
            img,
            (new_w, new_h),
            interpolation=cv.INTER_AREA
        )
        return resized

   
    def sharpen(self, img):
        # Define sharpening kernel
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])
        # Apply filter to sharpen image
        sharp = cv.filter2D(img, -1, kernel)
        return sharp
    

    def process(self, img_input):
        img = self.load_image(img_input)
        resized = self.resize(img)
        gray = self.grayscale(resized)
        sharp = self.sharpen(gray)
        return sharp
    

    def save(self, img, output_path):
        # Save image as JPEG
        cv.imwrite(
            output_path,
            img,
            [cv.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
        )
        return output_path
