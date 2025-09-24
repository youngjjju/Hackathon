import random
import smbus2
import time
import numpy as np

class MPU6050:
    def __init__(self, address=0x68, bus_num=1, test_mode=False, calib_samples=100):
        self.test_mode = test_mode
        self.address = address
        self.bus_num = bus_num
        self.offset = np.array([0.0, 0.0, 0.0])  # 보정용 오프셋 저장

        if not self.test_mode:
            # ✅ 실제 센서 모드 → I2C 초기화
            self.bus = smbus2.SMBus(bus_num)
            self.bus.write_byte_data(self.address, 0x6B, 0)  # 슬립 모드 해제
            self.bus.write_byte_data(self.address, 0x19, 1)
            self.bus.write_byte_data(self.address, 0x1A, 0x03)
            self.bus.write_byte_data(self.address, 0x1C, 0x10)
            self.accel_scale = 16384.0
        else:
            self.accel_scale = 16384.0

        # ✅ 자동 보정 실행
        self.calibrate(samples=calib_samples)

    def read_word_2c(self, reg):
        high = self.bus.read_byte_data(self.address, reg)
        low = self.bus.read_byte_data(self.address, reg+1)
        val = (high << 8) + low
        if val >= 0x8000:
            val = -((65535 - val) + 1)
        return val

    def read_accel_raw(self):
        if self.test_mode:
            # ✅ 테스트 모드: 랜덤 데이터
            if random.random() < 0.5:
                accel_x = random.uniform(3, 5)
                accel_y = random.uniform(3, 5)
                accel_z = random.uniform(3, 5)
            else:
                accel_x = random.uniform(-2, 2)
                accel_y = random.uniform(-2, 2)
                accel_z = random.uniform(-2, 2)
            return (accel_x, accel_y, accel_z)
        else:
            accel_x = self.read_word_2c(0x3B) / self.accel_scale
            accel_y = self.read_word_2c(0x3D) / self.accel_scale
            accel_z = self.read_word_2c(0x3F) / self.accel_scale
            return (accel_x, accel_y, accel_z)

    def calibrate(self, samples=100):
        """초기 정지 상태에서 평균값을 구해 offset 저장"""
        print(f"📏 {samples}회 샘플링으로 IMU 자동 보정 중... 가만히 두세요.")
        data = []
        for _ in range(samples):
            data.append(self.read_accel_raw())
            time.sleep(0.01)  # 100Hz 기준 → 0.01s 간격
        self.offset = np.mean(data, axis=0)
        print(f"✅ 보정 완료, offset = {self.offset}")

    def read_accel(self):
        raw = np.array(self.read_accel_raw())
        corrected = raw - self.offset
        return tuple(corrected)
