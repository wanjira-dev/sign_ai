import cv2
import sys
from model import extract_hand_landmarks

def check_single_image(image_path):
    """
    Loads a single image and tries to detect landmarks. Provides clear visual feedback
    """
    print(f"--- Checked image: {image_path}")
    
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print("Could not load image check path")
        return
    
    # Run the landmark extraction
    landmarks, display_img = extract_hand_landmarks(image)
    
    # Report the result
    if landmarks:
        print("Success: MediaPipe detected hand landmarks!")
        cv2.putText(display_img, "SUCCESS!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
    else:
        print("MediaPipe did not detect any hands in this image.")
        cv2.putText(display_img, "FAILURE!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        print(" Check if the hand is clear, and fully visible.")
        
    # Shows visual results
    cv2.imshow("MediaPipe Detection Check", display_img)
    print("Press any key to close the image window...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_mediapipe.py <path_to_your_image>")
    else:
        check_single_image(sys.argv[1])