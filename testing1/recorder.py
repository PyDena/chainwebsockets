import cv2
import numpy as np
import pygetwindow as gw
import pyautogui

# Define the codec and create VideoWriter object
def begin():
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    print(fourcc)
    out = cv2.VideoWriter('output.mp4', fourcc, 8.0, (1920, 1080))

    while True:
        # Capture the screen
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Write the frame into the file 'output.avi'
        out.write(frame)

        # Display the resulting frame
        cv2.imshow('frame', frame)

        # Quit when 'q' is pressed
        if cv2.waitKey(1) == ord('q'):
            break

    # Release everything when job is finished
    out.release()
    cv2.destroyAllWindows()