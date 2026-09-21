# The OmniVision OV3660 camera on a Seeed XIAO ESP32-S3 Sense.
#
# The sensor itself is not driven from Python. Frames arrive over an 8-bit parallel bus at a
# pixel clock of 20MHz, which only the ESP32-S3's LCD_CAM peripheral and DMA can keep up with,
# so the actual driver is the C `camera` module in the firmware. Flash a build that has it:
#
#   https://github.com/cnadler86/micropython-camera-API
#
# which publishes a prebuilt binary for this board. Without it, importing this module fails
# with `ImportError: no module named 'camera'` and no amount of Python will fix that.
#
# What is left for Python is the two things the firmware does not know: which pins this
# particular board wires the sensor to, and the corrections an OV3660 wants that its OV2640
# sibling does not.
#
# ponytail: a pin map and three settings, not a register-level driver. The registers live in
# the C component; changing them means building firmware, not editing this file.

from camera import Camera, FrameSize, PixelFormat, GrabMode  # noqa: F401 - re-exported

# The DVP pins on the XIAO ESP32-S3 Sense. They are fixed in copper: the camera sits on the
# board-to-board connector under the expansion board, not on the header pins, so there is
# nothing to wire and nothing to change. Another board carrying an OV3660 needs its own map,
# which is what `pins` is for.
XIAO_ESP32S3_SENSE = {
    "data_pins": [15, 17, 18, 16, 14, 12, 11, 48],  # D0 first, D7 last
    "vsync_pin": 38,
    "href_pin": 47,
    "pclk_pin": 13,
    "xclk_pin": 10,
    "sda_pin": 40,   # the sensor's own I2C bus, not the Grove one
    "scl_pin": 39,
    "reset_pin": -1,      # -1 means not wired: the sensor resets when the board does
    "powerdown_pin": -1,
}


def camera(frame_size=FrameSize.SVGA, pixel_format=PixelFormat.JPEG, jpeg_quality=12,
           pins=XIAO_ESP32S3_SENSE, vflip=True, brightness=1, saturation=-2, **settings):
    """Starts the camera and hands it back, ready for `capture()`.

    `frame_size` runs from `FrameSize.QQVGA` to `FrameSize.QXGA`, the sensor's full three
    megapixels. Bigger frames need more PSRAM and take longer; QXGA at JPEG is about as far
    as this board goes. `jpeg_quality` is 0 to 63 and lower means better, which is backwards
    from every photo app but is what the sensor calls it.

    The last three are the picture's tuning knobs, and the defaults are a starting point
    rather than a measurement. Pass `None` for any of them to leave the sensor's own default
    alone. Anything else, `xclk_freq` or `fb_count` or `grab_mode`, passes straight through.
    """
    cam = Camera(frame_size=frame_size, pixel_format=pixel_format, jpeg_quality=jpeg_quality,
                 **pins, **settings)
    cam.init()

    # An OV3660 reads out the other way up from an OV2640, so a board built for one gives an
    # upside down picture with the other, and it comes out pale and oversaturated besides.
    # These three are what the esp32-camera component applies itself when it finds this
    # sensor. Lighting is not the same everywhere, so they are arguments, not constants.
    if vflip is not None:
        cam.set_vflip(vflip)
    if brightness is not None:
        cam.set_brightness(brightness)
    if saturation is not None:
        cam.set_saturation(saturation)
    return cam
