import spidev
import RPi.GPIO as GPIO
import time

# 핀 설정
RESET_PIN = 25
DIO0_PIN  = 24

# SPI 초기화
spi = spidev.SpiDev()
spi.open(0, 0)  # bus 0, CE0
spi.max_speed_hz = 5000000
spi.mode = 0

# GPIO 초기화
GPIO.setmode(GPIO.BCM)
GPIO.setup(RESET_PIN, GPIO.OUT)
GPIO.setup(DIO0_PIN, GPIO.IN)

# SX1278 레지스터 접근 함수
def write_reg(addr, val):
    spi.xfer2([addr | 0x80, val])

def read_reg(addr):
    val = spi.xfer2([addr & 0x7F, 0x00])
    return val[1]

# SX1278 리셋
def reset():
    GPIO.output(RESET_PIN, 0)
    time.sleep(0.1)
    GPIO.output(RESET_PIN, 1)
    time.sleep(0.1)

# 초기 설정
def lora_init():
    reset()
    version = read_reg(0x42)
    print(f"Version: 0x{version:02X}")
    if version != 0x12:
        print("LoRa chip not found!")
        return False
    
    # Sleep 모드
    write_reg(0x01, 0x80)  # LoRa mode + sleep
    time.sleep(0.1)
    
    # 주파수 설정 (예: 433 MHz)
    freq = 433E6
    frf = int((freq / 32e6) * (1 << 19))
    write_reg(0x06, (frf >> 16) & 0xFF)
    write_reg(0x07, (frf >> 8) & 0xFF)
    write_reg(0x08, frf & 0xFF)
    
    # 출력 파워
    write_reg(0x09, 0x8F)  # PA_BOOST, 17 dBm
    
    # FIFO TX base
    write_reg(0x0E, 0x80)
    write_reg(0x0F, 0x80)
    
    print("LoRa TX init done.")
    return True

# 송신 함수
def lora_send(data):
    # standby 모드
    write_reg(0x01, 0x81)
    
    # FIFO 포인터 설정
    write_reg(0x0D, 0x80)
    
    # 데이터 쓰기
    for b in data:
        write_reg(0x00, b)
    
    # 길이
    write_reg(0x22, len(data))
    
    # 송신 모드
    write_reg(0x01, 0x83)
    print("Sending packet...")
    
    # 송신 완료 대기 (DIO0 핀으로 확인)
    while GPIO.input(DIO0_PIN) == 0:
        time.sleep(0.01)
    
    print("Send done!")

# 실행
if __name__ == "__main__":
    if lora_init():
        while True:
            msg = "Hello LoRa!".encode('utf-8')
            lora_send(msg)
            time.sleep(2)
