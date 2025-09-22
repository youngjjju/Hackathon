import spidev
import RPi.GPIO as GPIO
import time

# SPI 초기화
spi = spidev.SpiDev()
spi.open(0, 0)   # bus 0, device 0 (CE0)
spi.max_speed_hz = 5000000  # 5MHz 정도 (SX1278는 10MHz까지 OK)
spi.mode = 0

# CS 핀은 하드웨어 CE0로 씀, RESET은 수동 GPIO 할당
RESET_PIN = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(RESET_PIN, GPIO.OUT)

# SX1278 RESET
GPIO.output(RESET_PIN, 0)
time.sleep(0.1)
GPIO.output(RESET_PIN, 1)
time.sleep(0.1)

def read_register(addr):
    # MSB=0 → read, MSB=1 → write
    resp = spi.xfer2([addr & 0x7F, 0x00])  # 첫 바이트: 주소, 두 번째는 dummy
    return resp[1]

def write_register(addr, value):
    spi.xfer2([addr | 0x80, value])

# 버전 레지스터(0x42) 읽기
version = read_register(0x42)
print(f"SX1278 version register: 0x{version:02X}")

if version == 0x12:
    print("✅ 모듈 살아있음 (SX1278 OK)")
else:
    print("❌ 응답 없음 (망가졌을 가능성 높음)")
