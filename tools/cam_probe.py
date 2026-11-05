import cv2, time

for idx in range(6):
    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(idx, "not opened")
        continue
    frame = None
    for _ in range(10):
        ok, f = cap.read()
        if ok:
            frame = f
        time.sleep(0.05)
    cap.release()
    if frame is None:
        print(idx, "opened, no frame")
        continue
    if frame.ndim == 2:
        print(idx, frame.shape, "mean brightness %.0f" % frame.mean(), "GREYSCALE (IR?)")
        continue
    b, g, r = [frame[:, :, c].astype(int) for c in range(3)]
    grey = abs(b - g).mean() < 2 and abs(g - r).mean() < 2
    print(idx, frame.shape, "mean brightness %.0f" % frame.mean(), "GREYSCALE (IR?)" if grey else "colour")