import math

class FeatureExtractor:
    def __init__(self, alpha=0.2):
        self.prev_lin_a = 0.0
        self.alpha = alpha
        self.ax_f = None
        self.ay_f = None
        self.az_f = None

    def _lpf(self, prev, x):
        if prev is None:
            return x
        return self.alpha * x + (1.0 - self.alpha) * prev

    def update(self, dt_s, ax, ay, az):
        # 1) 축별 LPF
        self.ax_f = self._lpf(self.ax_f, ax)
        self.ay_f = self._lpf(self.ay_f, ay)
        self.az_f = self._lpf(self.az_f, az)

        # 2) 크기 -> lin_a -> jerk
        a_mag = math.sqrt(self.ax_f**2 + self.ay_f**2 + self.az_f**2)
        lin_a = max(0.0, a_mag - 1.0)  # |a|-1g
        jerk_mps3 = ((lin_a - self.prev_lin_a) / dt_s) * 9.80665
        self.prev_lin_a = lin_a

        return {
            "a_mag": a_mag,
            "lin_a": lin_a,
            "jerk_mps3": jerk_mps3,
            "ax": self.ax_f, "ay": self.ay_f, "az": self.az_f
        }
