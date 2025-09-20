import time
from imu import MPU6050
from accident_detect import AccidentDetector

def main():
    imu = MPU6050()
    detector = AccidentDetector(threshold=2.5, min_duration=0.3, jerk_threshold=5.0)

    print("🚗 IMU 기반 사고 감지 프로그램 시작")

    while True:
        try:
            accel = imu.read_accel()
            accident, mag, jerk = detector.detect(accel)

            if accident:
                print(f"[⚠️ 사고 감지] 지속 충격, 크기: {mag:.2f}g, Jerk: {jerk:.2f} g/s, 값: {accel}")
            else:
                print(f"[정상] 크기: {mag:.2f}g, Jerk: {jerk:.2f} g/s")

            time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n프로그램 종료")
            break

if __name__ == "__main__":
    main()
