import cv2
import time
import os

class ImageLoader: 
    def __init__(self, image_path, imshow=False):
        self.capture = cv2.VideoCapture(image_path)
        self.imshow = imshow
        if not self.capture.isOpened():
            raise ValueError("Cannot open the image_path")
        
        if isinstance(image_path, str) and os.path.isfile(image_path):
            self.isVideo = True
            self.total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        else:
            self.isVideo = False
            self.total_frames = float('inf')
    
    def frame_generator(self):
        try:
            while True:
                ret, frame = self.capture.read()
                if not ret:
                    if self.isVideo:
                        current_frame = int(self.capture.get(cv2.CAP_PROP_POS_FRAMES))
                        if current_frame >= self.total_frames:
                            print("Reached end of Video, exiting.")
                            break
                        else:
                            print("Failed to read video file, continuing...")
                            continue
                    else:
                        print("Failed to read camera, continuing...")
                        continue
                if self.imshow:
                    cv2.imshow(f"Current Frame", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('s'):
                        while cv2.waitKey(1) & 0xFF != ord('s'):
                            pass
                if self.isVideo:
                    fps = self.capture.get(cv2.CAP_PROP_FPS)
                    if fps > 0:
                        time.sleep(1 / fps)

                yield frame
        
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        self.capture.release()
        cv2.destroyAllWindows()