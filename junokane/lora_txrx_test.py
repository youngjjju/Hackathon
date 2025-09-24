import spidev
import RPi.GPIO as GPIO
import time
from SX127x.SX127x import SX127x

# SPI 초기화
spi = spidev.SpiDev()
spi.open(0, 0)              # SPI0, CS0
spi.max_speed_hz = 5000000  # 5 MHz

# 핀 번호 (BCM 기준)
NSS   = 8     # CS
RESET = 25    # RESET
DIO0  = 24    # RxDone

# LoRa 컨트롤러 객체
controller = SX127x(spi, GPIO, nss_pin=NSS, reset_pin=RESET, dio0_pin=DIO0)

def lora_init():
    controller.reset()
    version = controller.read_reg(0x42)
    print(f"Chip Version: 0x{version:02X}")
    if version != 0x12:
        print("LoRa chip not found!")
        return False

    controller.set_mode(SX127x.MODE_SLEEP)
    time.sleep(0.1)

    # 기본 파라미터 설정
    controller.set_freq(433E6)             # 433 MHz
    controller.set_spreading_factor(7)     # SF7
    controller.set_bandwidth(125E3)        # 125 kHz
    controller.set_coding_rate(5)          # CR 4/5

    # 연속 수신 모드
    controller.set_mode(SX127x.MODE_RXCONT)
    print("LoRa RX init done.")
    return True

# ✅ 수신 콜백 함수
def on_packet(channel):
    payload = controller.read_payload()
    msg = bytes(payload).decode("utf-8", errors="ignore")
    print("📩 Received:", msg)

    # IRQ 플래그 클리어 (RxDone)
    controller.clear_irq_flags(RxDone=1)

# ✅ 송신 함수
def lora_send(msg: str):
    controller.send_packet(list(msg.encode("utf-8")))
    print("📤 Sent:", msg)

    # 송신 끝나면 다시 RX 모드로 복귀
    controller.set_mode(SX127x.MODE_RXCONT)

# 실행부
if __name__ == "__main__":
    if lora_init():
        # 이벤트 감지: DIO0 핀 Rising → on_packet() 호출
        GPIO.add_event_detect(DIO0, GPIO.RISING, callback=on_packet)

        print("✨ LoRa 송수신기 준비 완료 (RX 대기 + 필요 시 TX)")

        try:
            while True:
                # 예시: 10초마다 메시지 송신
                lora_send("Hello from TXRX")
                time.sleep(10)

        except KeyboardInterrupt:
            print("\n프로그램 종료")
            GPIO.cleanup()
