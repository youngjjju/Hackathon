# imu.py
import smbus2
import time

class MPU6050:
    def __init__(self, address=0x68, bus_num=1):
        # I2C 버스 열기
        self.bus = smbus2.SMBus(bus_num)
        self.address = address

        # 전원 관리 레지스터(0x6B) 초기화 → 센서 깨우기
        self.bus.write_byte_data(self.address, 0x6B, 0)

    def read_word(self, reg):
        """16비트(2바이트) 값 읽기"""
        high = self.bus.read_byte_data(self.address, reg)
        low = self.bus.read_byte_data(self.address, reg + 1)
        val = (high << 8) + low
        if val >= 0x8000:  # 2의 보수 처리 (음수 변환)
            val = -((65535 - val) + 1)
        return val

    def read_accel(self):
        """가속도 값 읽기 (x, y, z)"""
        accel_x = self.read_word(0x3B) / 16384.0
        accel_y = self.read_word(0x3D) / 16384.0
        accel_z = self.read_word(0x3F) / 16384.0
        return accel_x, accel_y, accel_z

        # imu.py (센서 없는 테스트용)
# imu.py (랜덤 테스트 버전)
# imu.py (테스트 전용)
import random

class MPU6050:
    def __init__(self, address=0x68, bus_num=1):
        pass

    def read_accel(self):
        # 80% 확률로 정상 범위 (-2~2), 20% 확률로 큰 충격 (3~5)
        if random.random() < 0.2:
            accel_x = random.uniform(3, 5)
            accel_y = random.uniform(3, 5)
            accel_z = random.uniform(3, 5)
        else:
            accel_x = random.uniform(-2, 2)
            accel_y = random.uniform(-2, 2)
            accel_z = random.uniform(-2, 2)
        return accel_x, accel_y, accel_z
