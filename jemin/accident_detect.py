import numpy as np
import time
import random

class AccidentDetector:
    def __init__(self, threshold=2.5, min_duration=0.3, jerk_threshold=5.0, test_mode=False):
        """
        threshold: 임계 가속도 (g 단위)
        min_duration: 지속시간 (초 단위)
        jerk_threshold: 가속도 변화율 (jerk) 임계값 (g/s 단위)
        test_mode: True면 duration을 랜덤으로 발생 (모의실험용)
        """
        self.threshold = threshold
        self.min_duration = min_duration
        self.jerk_threshold = jerk_threshold
        self.test_mode = test_mode

        self.start_time = None
        self.prev_accel = None
        self.prev_time = None

    def detect(self, accel_data):
        magnitude = np.linalg.norm(accel_data)
        now = time.time()

        # jerk 계산
        jerk = 0.0
        if self.prev_accel is not None and self.prev_time is not None:
            dt = now - self.prev_time
            if dt > 0:
                jerk = (np.linalg.norm(accel_data) - np.linalg.norm(self.prev_accel)) / dt

        self.prev_accel = accel_data
        self.prev_time = now

        # 사고 조건 확인
        in_event = (magnitude > self.threshold) and (abs(jerk) > self.jerk_threshold)
        duration = 0.0

        if in_event:
            if self.test_mode:
                # ✅ 테스트 모드 → duration을 랜덤으로 생성
                duration = random.uniform(0.2, 2.0)
            else:
                # ✅ 실제 모드 → 조건 지속시간 계산
                if self.start_time is None:
                    self.start_time = now
                duration = now - self.start_time

            if duration >= self.min_duration:
                return True, magnitude, jerk, duration
            else:
                return False, magnitude, jerk, duration
        else:
            self.start_time = None
            return False, magnitude, jerk, 0.0
