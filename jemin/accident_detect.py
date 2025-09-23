import numpy as np
import time
import random

class AccidentDetector:
    def __init__(self, threshold=0.8, min_duration=0.0, jerk_threshold=0.2, axis_delta_threshold=0.5, test_mode=False):
        """
        threshold: 전체 가속도 크기 임계값 (g 단위)
        min_duration: 지속시간 (초 단위)
        jerk_threshold: 가속도 변화율 (g/s 단위)
        axis_delta_threshold: 축별 순간 변화량 임계값 (g 단위)
        """
        self.threshold = threshold
        self.min_duration = min_duration
        self.jerk_threshold = jerk_threshold
        self.axis_delta_threshold = axis_delta_threshold
        self.test_mode = test_mode

        self.start_time = None
        self.prev_accel = None
        self.prev_time = None

    def detect(self, accel_data):
        magnitude = np.linalg.norm(accel_data)
        now = time.time()

        # jerk 계산
        jerk = 0.0
        axis_delta = (0.0, 0.0, 0.0)
        if self.prev_accel is not None and self.prev_time is not None:
            dt = now - self.prev_time
            if dt > 0:
                jerk = (np.linalg.norm(accel_data) - np.linalg.norm(self.prev_accel)) / dt
                axis_delta = tuple(abs(a - p) for a, p in zip(accel_data, self.prev_accel))

        self.prev_accel = accel_data
        self.prev_time = now

        # 사고 조건: 전체 크기 or jerk or 축별 변화량
        in_event = (
            (magnitude > self.threshold) or
            (abs(jerk) > self.jerk_threshold) or
            any(delta > self.axis_delta_threshold for delta in axis_delta)
        )

        duration = 0.0
        if in_event:
            if self.test_mode:
                duration = random.uniform(0.1, 1.0)
            else:
                if self.start_time is None:
                    self.start_time = now
                duration = now - self.start_time

            if duration >= self.min_duration:
                return True, magnitude, jerk, duration, axis_delta
            else:
                return False, magnitude, jerk, duration, axis_delta
        else:
            self.start_time = None
            return False, magnitude, jerk, 0.0, axis_delta
