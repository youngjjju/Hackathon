import random
import smbus2

class MPU6050:
    def __init__(self, address=0x68, bus_num=1, test_mode=False):
        self.test_mode = test_mode
        self.address = address
        self.bus_num = bus_num

        if not self.test_mode:
            # ✅ 실제 센서 모드 → I2C 초기화
            self.bus = smbus2.SMBus(bus_num)
            self.bus.write_byte_data(self.address, 0x6B, 0)  # 슬립 모드 해제

    def read_word_2c(self, reg):
        high = self.bus.read_byte_data(self.address, reg)
        low = self.bus.read_byte_data(self.address, reg+1)
        val = (high << 8) + low
        if val >= 0x8000:
            val = -((65535 - val) + 1)
        return val

    def read_accel(self):
        if self.test_mode:
            # ✅ 테스트 모드: 50% 확률 사고, 50% 정상
            if random.random() < 0.5:
                accel_x = random.uniform(3, 5)
                accel_y = random.uniform(3, 5)
                accel_z = random.uniform(3, 5)
            else:
                accel_x = random.uniform(-2, 2)
                accel_y = random.uniform(-2, 2)
                accel_z = random.uniform(-2, 2)
            return accel_x, accel_y, accel_z
        else:
            # ✅ 실제 모드: 센서에서 데이터 읽기
            accel_x = self.read_word_2c(0x3B) / 16384.0
            accel_y = self.read_word_2c(0x3D) / 16384.0
            accel_z = self.read_word_2c(0x3F) / 16384.0
            return accel_x, accel_y, accel_z
