import numpy as np
import time

class AccidentDetector:
    def __init__(self, threshold=2.5, min_duration=0.3, jerk_threshold=5.0):
        """
        threshold: 임계 가속도 (g 단위)
        min_duration: 지속시간 (초 단위)
        jerk_threshold: 가속도 변화율 (jerk) 임계값 (g/s 단위)
        """
        self.threshold = threshold
        self.min_duration = min_duration
        self.jerk_threshold = jerk_threshold

        self.start_time = None
        self.prev_accel = None
        self.prev_time = None

    def detect(self, accel_data):
        magnitude = np.linalg.norm(accel_data)
        now = time.time()

        # jerk 계산 (가속도 변화율)
        jerk = 0.0
        if self.prev_accel is not None:
            dt = now - self.prev_time
            if dt > 0:
                jerk = (np.linalg.norm(accel_data) - np.linalg.norm(self.prev_accel)) / dt

        # 이전 값 갱신
        self.prev_accel = accel_data
        self.prev_time = now

        # 사고 판정 로직
        if magnitude > self.threshold and abs(jerk) > self.jerk_threshold:
            if self.start_time is None:
                self.start_time = now
            elif (now - self.start_time) >= self.min_duration:
                return True, magnitude, jerk
        else:
            self.start_time = None

        return False, magnitude, jerk
