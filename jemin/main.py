import time
import argparse
from imu import MPU6050
from accident_detect import AccidentDetector

def main():
    # ✅ 터미널 옵션 처리
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="테스트 모드 실행 (랜덤 데이터 + 랜덤 duration)")
    args = parser.parse_args()

    # ✅ 옵션에 따라 imu/test_mode 결정
    imu = MPU6050(test_mode=args.test)
    detector = AccidentDetector(threshold=2.5, min_duration=0.3,
                                jerk_threshold=5.0, test_mode=args.test)

    mode = "테스트 모드" if args.test else "실제 모드"
    print(f"🚗 IMU 기반 사고 감지 프로그램 시작 ({mode})")

    while True:
        try:
            accel = imu.read_accel()
            accident, mag, jerk, duration = detector.detect(accel)

            if accident:
                print(f"[⚠️ 사고 감지] 지속 충격, 크기: {mag:.2f}g, "
                      f"Jerk: {jerk:.2f} g/s, 지속시간: {duration:.3f}s, 값: {accel}")
            else:
                print(f"[정상] 크기: {mag:.2f}g, Jerk: {jerk:.2f} g/s, 지속시간: {duration:.3f}s")

            time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n프로그램 종료")
            break

if __name__ == "__main__":
    main()
