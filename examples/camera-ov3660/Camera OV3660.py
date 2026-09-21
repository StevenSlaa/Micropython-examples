from ov3660 import camera, FrameSize
from time import sleep

# --- Configuration ---------------------------------------------------------------------------
# Where the photo is written, on the board's own filesystem. The same file every time, so this
# cannot fill the flash up while it runs; open it from the file panel to look at it.
path = "/photo.jpg"

# QQVGA, QVGA, VGA, SVGA, XGA, HD, SXGA, UXGA, QXGA. QXGA is the sensor's full three
# megapixels and takes about a second; SVGA is 800x600 and feels instant.
size = FrameSize.SVGA

# Seconds between photos.
interval = 5
# ---------------------------------------------------------------------------------------------

cam = camera(frame_size=size)
print("Camera started")

# The first frames come out while the sensor is still finding its exposure and white balance,
# so they are darker and greener than the scene is. Throw a handful away before keeping one.
for _ in range(5):
    cam.capture()
    sleep(0.1)

try:
    while True:
        photo = cam.capture()
        with open(path, "wb") as file:
            file.write(photo)
        # A JPEG of a dark or a flat scene compresses smaller, so this number is a rough
        # measure of how much is going on in front of the lens.
        print("Bytes: %d" % len(photo))
        sleep(interval)
finally:
    # The firmware's camera driver outlives a soft reset. Without this, stopping the script and
    # running it again fails with the camera already in use, and only the reset button helps.
    cam.deinit()
