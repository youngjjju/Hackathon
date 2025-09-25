import time
import RPi.GPIO as GPIO
from LoRaRF import SX127x

# BCM 모드 사용
GPIO.setmode(GPIO.BCM)

# 핀 설정 (네 보드 연결에 맞게 수정!)
RESET = 25
DIO0  = 24   # IRQ 핀 (보통 DIO0 사용)
SPI_BUS = 0
SPI_CS  = 0

# LoRa 인스턴스 (전역으로 하나 생성)
lora = SX127x(resetPin=RESET, dio0Pin=DIO0, spiBus=SPI_BUS, spiSelect=SPI_CS)


def lora_init():
    # SPI 세부 설정 (필요시 조정)
    lora.spi.max_speed_hz = 7800000
    lora.spi.mode = 0

    # 초기화
    ok = lora.begin()
    if not ok:
        print("LoRa begin failed")
        return False
    print("LoRa begin success")

    # RF 설정
    lora.setFrequency(433_000_000)  # 433MHz
    lora.setLoRaModulation(sf=7, bw=125_000, cr=5, low_datarate_opt=False)
    lora.setTxPower(17, 1)   # (power, pa_boost) → 1=PA_BOOST
    lora.setRxGain(0)        # 자동 gain
    lora.setLoRaPacket(header_type=0, preamble=8, payload_len=255,
                       crc_enable=True, invert_iq=False)
    lora.setSyncWord(0x12)

    # 수신 콜백 등록
    lora.onReceive(on_packet)

    # 연속 수신 모드
    lora.request(lora.RX_CONTINUOUS)

    print("LoRa init OK, listening mode set")
    return True


def on_packet(data_bytes):
    try:
        msg = bytes(data_bytes).decode('utf-8', errors='ignore')
    except:
        msg = str(data_bytes)
    print("📩 Received:", msg)
    print("   RSSI:", lora.packetRssi(), "dBm | SNR:", lora.snr(), "dB")


def lora_send(msg: str):
    lora.beginPacket()
    lora.write(msg.encode('utf-8'))
    lora.endPacket()
    lora.wait()
    print("📤 Sent:", msg)

    # 송신 후 다시 수신 모드
    lora.request(lora.RX_CONTINUOUS)


if __name__ == '__main__':
    if not lora_init():
        exit(1)

    try:
        while True:
            lora_send("Hello LoRaRF")
            time.sleep(10)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Exit")