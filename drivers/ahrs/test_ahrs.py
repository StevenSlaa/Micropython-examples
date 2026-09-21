# Run with: python3 -B drivers/ahrs/test_ahrs.py
# Holds a simulated board still in a known pose and checks both filters settle on it.
from math import cos, radians, sin

from ahrs import Madgwick, Mahony, calibrate_magnetic

G = 9.81
# Earth's field in the world frame: 20uT north (X), 40uT down.
NORTH, DOWN = 20.0, -40.0


def body(roll, pitch, yaw):
    """Accelerometer and magnetometer readings for a board at this pose (degrees, Z-Y-X order)."""
    r, p, y = radians(roll), radians(pitch), radians(yaw)
    cr, sr, cp, sp, cy, sy = cos(r), sin(r), cos(p), sin(p), cos(y), sin(y)
    # Rows of the world-to-body rotation.
    m = (
        (cp * cy, cp * sy, -sp),
        (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, sr * cp),
        (cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp),
    )
    up = (0.0, 0.0, G)
    field = (NORTH, 0.0, DOWN)
    to_body = lambda v: tuple(row[0] * v[0] + row[1] * v[1] + row[2] * v[2] for row in m)
    return to_body(up), to_body(field)


def settle(filter_, roll, pitch, yaw, seconds=60):
    accel, mag = body(roll, pitch, yaw)
    for _ in range(int(seconds * 100)):
        filter_.update(0.0, 0.0, 0.0, *accel, *mag)
    return filter_


def close(a, b, tolerance=1.0):
    return abs((a - b + 180) % 360 - 180) <= tolerance


for make in (lambda: Mahony(100, kp=2.0), lambda: Madgwick(100, beta=0.5)):
    # Yaw reads 180 more than the true heading, as Adafruit_AHRS does.
    for roll, pitch, yaw in ((0, 0, 0), (30, 0, 0), (0, -25, 90), (20, -15, 45), (-10, 30, 200)):
        f = settle(make(), roll, pitch, yaw)
        got = (f.roll, f.pitch, f.yaw - 180)
        assert all(close(a, b) for a, b in zip(got, (roll, pitch, yaw))), (type(f).__name__, roll, pitch, yaw, got)
    assert abs(sum(v * v for v in make().quaternion) - 1.0) < 1e-9

# A steady spin on the gyro alone integrates to the right angle: 90 deg/s for one second.
spin = Mahony(100, kp=0.0)
for _ in range(100):
    spin.update(0.0, 0.0, 90.0, 0.0, 0.0, 0.0)
assert close(spin.yaw - 180.0, 90.0, 0.5), spin.yaw

# Correction: subtract the offset, then apply the matrix.
assert calibrate_magnetic((12, 5, 3), (2, 1, 1), ((2, 0, 0), (0, 1, 0), (0, 0, 0.5))) == (20, 4, 1)

print("ahrs: ok")
