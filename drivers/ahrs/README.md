---
driver: ahrs
author: Steven Slaa
---

# AHRS orientation filters

## What it is

An AHRS (attitude and heading reference system) works out which way a board is pointing from three
sensors. None of them can do it alone:

| Sensor | Gives | But |
| --- | --- | --- |
| Gyroscope | fast, smooth rotation | drifts, a few degrees a minute |
| Accelerometer | which way is down, so roll and pitch | shakes with every bump |
| Magnetometer | which way is north, so yaw | is bent by nearby iron until calibrated |

A filter blends them: the gyroscope moves the estimate, gravity and the magnetic field slowly pull
it back. This driver has the two filters from Adafruit_AHRS, ported line for line, so a MicroPython
board prints the same angles as the Arduino sketch.

| Filter | Pick it when |
| --- | --- |
| `Mahony` | You want the cheapest, most responsive filter. The best default. |
| `Madgwick` | You want slightly smoother output and can spare the extra maths. |

## Install

Install it from the Pulsar IoT library panel, or copy `ahrs.py` to `/lib` on the board. It reads
no sensors itself: feed it from whichever drivers your board uses.

## Usage

```python
from time import sleep_ms
from ahrs import Mahony

fusion = Mahony(sample_rate=100)

while True:
    ax, ay, az = ...  # accelerometer, any unit
    gx, gy, gz = ...  # gyroscope, degrees per second
    mx, my, mz = ...  # magnetometer, any unit
    fusion.update(gx, gy, gz, ax, ay, az, mx, my, mz)
    print(fusion.roll, fusion.pitch, fusion.yaw)
    sleep_ms(10)
```

- The gyro goes in as **degrees per second**. Got rad/s? Wrap it in `math.degrees()`.
- Leave out `mx, my, mz` for a 6-axis IMU: roll and pitch still work, yaw slowly drifts.
- `yaw` runs 0 to 360 and, exactly as in Adafruit_AHRS, reads 180 when the board points along
  the field. Subtract 180 if you want 0 at north.
- `quaternion` is `(w, x, y, z)`. Use it for your own maths; Euler angles flip near straight up.

## Calibration

A magnetometer needs a hard and soft iron correction before yaw is any good. The Pulsar IoT
compass calibration tool measures it and hands you an offset and a 3x3 matrix; apply them with
`calibrate_magnetic`:

```python
from ahrs import calibrate_magnetic

MAG_OFFSET = (4.04, -15.64, -6.07)
MAG_MATRIX = ((1.048, -0.020, -0.008), (-0.020, 0.931, -0.056), (-0.008, -0.056, 1.028))
mx, my, mz = calibrate_magnetic((mx, my, mz), MAG_OFFSET, MAG_MATRIX)
```

Also measure the gyro bias once at start-up: average a couple of hundred readings with the board
still and subtract it, or the yaw creeps.

## Settings

| Setting | Default | Meaning |
| --- | --- | --- |
| `sample_rate` | 100 | How often you call `update()`, in Hz. Or pass `dt=` in seconds to each call. |
| `kp` (Mahony) | 0.5 | How hard it trusts the accelerometer and magnetometer. Higher settles faster, and is noisier. |
| `ki` (Mahony) | 0.0 | Learns a steady gyro bias. Leave at 0 unless yaw keeps creeping. |
| `beta` (Madgwick) | 0.1 | The same trade-off as `kp`. |

## Notes

- Call `update()` at a steady rate, and print less often than you update.
- All three sensors must use the same axes. If the magnetometer sits rotated on the board, swap
  and negate its axes before `update()`, or yaw goes wrong while roll and pitch look fine.
- The NXP Kalman filter from Adafruit_AHRS is not ported: it needs far more RAM and speed than a
  MicroPython board can give it at 100 Hz.

## Tests

`python3 -B drivers/ahrs/test_ahrs.py` holds a simulated board still in several poses and checks
both filters settle on the right roll, pitch and yaw.

## Credits

Ported from [Adafruit_AHRS](https://github.com/adafruit/Adafruit_AHRS) (BSD licence), which builds
on the open-source Mahony and Madgwick implementations by Sebastian Madgwick.
