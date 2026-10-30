import cv2
import numpy as np

print("Inspecting cameras 0, 1, 2, 3...")
frames = []

for i in range(4):
    cap = cv2.VideoCapture(i)
    ret, frame = cap.read()
    if ret and frame is not None:
        small = cv2.resize(frame, (320, 240))
        cv2.putText(small, f"INDEX {i}", (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        frames.append(small)
    else:
        blank = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.putText(blank, f"INDEX {i} (OFF)", (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        frames.append(blank)
    cap.release()

# 2x2 grid of all 4 cameras
top_row = np.hstack([frames[0], frames[1]])
bot_row = np.hstack([frames[2], frames[3]])
grid = np.vstack([top_row, bot_row])

print("Showing Camera Inspector! Look at which index shows your live phone feed.")
print("Press ANY KEY on your keyboard to close the window.")
cv2.imshow("Camera Inspector (Look at which index shows your phone)", grid)
cv2.waitKey(0)
cv2.destroyAllWindows()