import spidev
import RPi.GPIO as GPIO
import time

RESET_PIN = 25
DIO0_PIN  = 24

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 5000000
spi.mode = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(RESET_PIN, GPIO.OUT)
GPIO.setup(DIO0_PIN, GPIO.IN)

def write_reg(addr, val):
    spi.xfer2([addr | 0x80, val])

def read_reg(addr):
    val = spi.xfer2([addr & 0x7F, 0x00])
    return val[1]

def reset():
    GPIO.output(RESET_PIN, 0)
    time.sleep(0.1)
    GPIO.output(RESET_PIN, 1)
    time.sleep(0.1)

def lora_init():
    reset()
    version = read_reg(0x42)
    print(f"Version: 0x{version:02X}")
    if version != 0x12:
        print("LoRa chip not found!")
        return False
    
    # Sleep 모드
    write_reg(0x01, 0x80)
    time.sleep(0.1)
    
    # 주파수 433 MHz
    freq = 433E6
    frf = int((freq / 32e6) * (1 << 19))
    write_reg(0x06, (frf >> 16) & 0xFF)
    write_reg(0x07, (frf >> 8) & 0xFF)
    write_reg(0x08, frf & 0xFF)
    
    # FIFO RX base
    write_reg(0x0F, 0x00)
    write_reg(0x0E, 0x00)
    
    # 연속 수신 모드
    write_reg(0x01, 0x85)
    
    print("LoRa RX init done.")
    return True

def lora_receive():
    if GPIO.input(DIO0_PIN) == 1:  # 패킷 수신 완료
        irq_flags = read_reg(0x12)
        write_reg(0x12, 0xFF)  # IRQ 클리어
        
        if irq_flags & 0x40:  # RxDone
            currentAddr = read_reg(0x10)
            bytesNb = read_reg(0x13)
            write_reg(0x0D, currentAddr)
            
            payload = []
            for i in range(bytesNb):
                payload.append(read_reg(0x00))
            
            print("Received:", bytes(payload).decode("utf-8", errors="ignore"))

# 실행
if __name__ == "__main__":
    if lora_init():
        while True:
            lora_receive()
            time.sleep(0.1)
