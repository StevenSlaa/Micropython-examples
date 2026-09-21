# Orientation (AHRS) filters: Mahony and Madgwick, ported from Adafruit_AHRS.
# https://github.com/adafruit/Adafruit_AHRS
#
# Both fuse a gyroscope, an accelerometer and an optional magnetometer into one quaternion. The gyro
# gives fast rotation but drifts; gravity pulls roll and pitch back, the magnetic field pulls yaw
# back. Units match Adafruit_AHRS: gyro in degrees per second, accelerometer and magnetometer in
# any unit, since only their direction is used.

from math import asin, atan2, degrees, sqrt

_DEG_TO_RAD = 0.0174533


def _normalise(x, y, z):
    norm = sqrt(x * x + y * y + z * z)
    return (x / norm, y / norm, z / norm) if norm else (0.0, 0.0, 0.0)


def calibrate_magnetic(field, offset, matrix):
    """Hard and soft iron correction: subtract `offset`, then multiply by the 3x3 `matrix`.

    Both come from the Pulsar compass calibration tool, or any ellipsoid fit.
    """
    x, y, z = field[0] - offset[0], field[1] - offset[1], field[2] - offset[2]
    return tuple(row[0] * x + row[1] * y + row[2] * z for row in matrix)


class _Filter:
    def __init__(self, sample_rate):
        self.dt = 1.0 / sample_rate
        self.q = [1.0, 0.0, 0.0, 0.0]

    @property
    def quaternion(self):
        """(w, x, y, z). Prefer this over Euler angles in your own maths: it has no gimbal lock."""
        return tuple(self.q)

    @property
    def roll(self):
        """Degrees, rotation around X."""
        q0, q1, q2, q3 = self.q
        return degrees(atan2(q0 * q1 + q2 * q3, 0.5 - q1 * q1 - q2 * q2))

    @property
    def pitch(self):
        """Degrees, rotation around Y."""
        q0, q1, q2, q3 = self.q
        return degrees(asin(max(-1.0, min(1.0, -2.0 * (q1 * q3 - q0 * q2)))))

    @property
    def yaw(self):
        """Degrees, 0 to 360. Offset by 180 exactly like Adafruit_AHRS, so both print the same."""
        q0, q1, q2, q3 = self.q
        return degrees(atan2(q1 * q2 + q0 * q3, 0.5 - q2 * q2 - q3 * q3)) + 180.0

    def _integrate(self, gx, gy, gz, dt):
        q0, q1, q2, q3 = self.q
        gx *= 0.5 * dt
        gy *= 0.5 * dt
        gz *= 0.5 * dt
        q = (
            q0 + (-q1 * gx - q2 * gy - q3 * gz),
            q1 + (q0 * gx + q2 * gz - q3 * gy),
            q2 + (q0 * gy - q1 * gz + q3 * gx),
            q3 + (q0 * gz + q1 * gy - q2 * gx),
        )
        norm = sqrt(sum(v * v for v in q))
        self.q = [v / norm for v in q]


class Mahony(_Filter):
    """Mahony filter. Low cost and responsive; the best default on a microcontroller.

    `kp` pulls towards the accelerometer and magnetometer, `ki` removes a steady gyro bias.
    """

    def __init__(self, sample_rate=100, kp=0.5, ki=0.0):
        super().__init__(sample_rate)
        self.two_kp = 2.0 * kp
        self.two_ki = 2.0 * ki
        self._integral = [0.0, 0.0, 0.0]

    def update(self, gx, gy, gz, ax, ay, az, mx=0.0, my=0.0, mz=0.0, dt=None):
        """Feed one sample. Gyro in degrees per second. Leave out the magnetometer for IMU mode."""
        dt = self.dt if dt is None else dt
        gx *= _DEG_TO_RAD
        gy *= _DEG_TO_RAD
        gz *= _DEG_TO_RAD
        if ax or ay or az:
            ax, ay, az = _normalise(ax, ay, az)
            q0, q1, q2, q3 = self.q
            # Gravity as the current estimate expects to see it.
            vx = q1 * q3 - q0 * q2
            vy = q0 * q1 + q2 * q3
            vz = q0 * q0 - 0.5 + q3 * q3
            ex = ay * vz - az * vy
            ey = az * vx - ax * vz
            ez = ax * vy - ay * vx
            if mx or my or mz:
                mx, my, mz = _normalise(mx, my, mz)
                q0q0, q0q1, q0q2, q0q3 = q0 * q0, q0 * q1, q0 * q2, q0 * q3
                q1q1, q1q2, q1q3 = q1 * q1, q1 * q2, q1 * q3
                q2q2, q2q3, q3q3 = q2 * q2, q2 * q3, q3 * q3
                hx = 2.0 * (mx * (0.5 - q2q2 - q3q3) + my * (q1q2 - q0q3) + mz * (q1q3 + q0q2))
                hy = 2.0 * (mx * (q1q2 + q0q3) + my * (0.5 - q1q1 - q3q3) + mz * (q2q3 - q0q1))
                bx = sqrt(hx * hx + hy * hy)
                bz = 2.0 * (mx * (q1q3 - q0q2) + my * (q2q3 + q0q1) + mz * (0.5 - q1q1 - q2q2))
                # The earth's field as the current estimate expects to see it.
                wx = bx * (0.5 - q2q2 - q3q3) + bz * (q1q3 - q0q2)
                wy = bx * (q1q2 - q0q3) + bz * (q0q1 + q2q3)
                wz = bx * (q0q2 + q1q3) + bz * (0.5 - q1q1 - q2q2)
                ex += my * wz - mz * wy
                ey += mz * wx - mx * wz
                ez += mx * wy - my * wx
            if self.two_ki > 0.0:
                integral = self._integral
                integral[0] += self.two_ki * ex * dt
                integral[1] += self.two_ki * ey * dt
                integral[2] += self.two_ki * ez * dt
                gx += integral[0]
                gy += integral[1]
                gz += integral[2]
            else:
                self._integral = [0.0, 0.0, 0.0]
            gx += self.two_kp * ex
            gy += self.two_kp * ey
            gz += self.two_kp * ez
        self._integrate(gx, gy, gz, dt)


class Madgwick(_Filter):
    """Madgwick filter. Smooth; a little more maths per sample than Mahony.

    `beta` is how hard it pulls towards the accelerometer and magnetometer.
    """

    def __init__(self, sample_rate=100, beta=0.1):
        super().__init__(sample_rate)
        self.beta = beta

    def update(self, gx, gy, gz, ax, ay, az, mx=0.0, my=0.0, mz=0.0, dt=None):
        """Feed one sample. Gyro in degrees per second. Leave out the magnetometer for IMU mode."""
        dt = self.dt if dt is None else dt
        gx *= _DEG_TO_RAD
        gy *= _DEG_TO_RAD
        gz *= _DEG_TO_RAD
        q0, q1, q2, q3 = self.q
        # Rate of change of the quaternion from the gyroscope alone.
        d0 = 0.5 * (-q1 * gx - q2 * gy - q3 * gz)
        d1 = 0.5 * (q0 * gx + q2 * gz - q3 * gy)
        d2 = 0.5 * (q0 * gy - q1 * gz + q3 * gx)
        d3 = 0.5 * (q0 * gz + q1 * gy - q2 * gx)
        if ax or ay or az:
            ax, ay, az = _normalise(ax, ay, az)
            # Gradient descent step towards the measured gravity (and field).
            fx = 2.0 * (q1 * q3 - q0 * q2) - ax
            fy = 2.0 * (q0 * q1 + q2 * q3) - ay
            fz = 2.0 * (0.5 - q1 * q1 - q2 * q2) - az
            s0 = -2.0 * q2 * fx + 2.0 * q1 * fy
            s1 = 2.0 * q3 * fx + 2.0 * q0 * fy - 4.0 * q1 * fz
            s2 = -2.0 * q0 * fx + 2.0 * q3 * fy - 4.0 * q2 * fz
            s3 = 2.0 * q1 * fx + 2.0 * q2 * fy
            if mx or my or mz:
                mx, my, mz = _normalise(mx, my, mz)
                hx = 2.0 * (mx * (0.5 - q2 * q2 - q3 * q3) + my * (q1 * q2 - q0 * q3) + mz * (q1 * q3 + q0 * q2))
                hy = 2.0 * (mx * (q1 * q2 + q0 * q3) + my * (0.5 - q1 * q1 - q3 * q3) + mz * (q2 * q3 - q0 * q1))
                bx = sqrt(hx * hx + hy * hy)
                bz = 2.0 * (mx * (q1 * q3 - q0 * q2) + my * (q2 * q3 + q0 * q1) + mz * (0.5 - q1 * q1 - q2 * q2))
                gx_ = bx * (0.5 - q2 * q2 - q3 * q3) + bz * (q1 * q3 - q0 * q2) - mx
                gy_ = bx * (q1 * q2 - q0 * q3) + bz * (q0 * q1 + q2 * q3) - my
                gz_ = bx * (q0 * q2 + q1 * q3) + bz * (0.5 - q1 * q1 - q2 * q2) - mz
                s0 += -bz * q2 * gx_ + (-bx * q3 + bz * q1) * gy_ + bx * q2 * gz_
                s1 += bz * q3 * gx_ + (bx * q2 + bz * q0) * gy_ + (bx * q3 - 2.0 * bz * q1) * gz_
                s2 += (-2.0 * bx * q2 - bz * q0) * gx_ + (bx * q1 + bz * q3) * gy_ + (bx * q0 - 2.0 * bz * q2) * gz_
                s3 += (-2.0 * bx * q3 + bz * q1) * gx_ + (-bx * q0 + bz * q2) * gy_ + bx * q1 * gz_
            norm = sqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3)
            if norm:
                d0 -= self.beta * s0 / norm
                d1 -= self.beta * s1 / norm
                d2 -= self.beta * s2 / norm
                d3 -= self.beta * s3 / norm
        q = (q0 + d0 * dt, q1 + d1 * dt, q2 + d2 * dt, q3 + d3 * dt)
        norm = sqrt(sum(v * v for v in q))
        self.q = [v / norm for v in q]
