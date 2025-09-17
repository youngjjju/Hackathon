#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
imu.py — model-car friendly impact detection with auto-threshold option
- 합성가속도(LPF), jerk, RMS 기반 투표식 판정
- hold 구간 비율 충족 시 EVENT 발생
- CSV 스냅샷 저장 (./snapshot)
- 옵션: --auto-threshold → 시작 시 캘리브레이션 후 임계값 자동 계산
"""

import argparse
import csv
import math
import os
import signal
import time
from collections import deque
from datetime import datetime

# ===== I2C / MPU-6050 =====
I2C_OK = True
try:
    from smbus2 import SMBus
except Exception:
    I2C_OK = False

MPU_ADDR       = 0x68
REG_PWR_MGMT_1 = 0x6B
REG_ACCEL_CFG  = 0x1C
REG_AX_H       = 0x3B

ACCEL_RANGE_BITS = {2:0x00, 4:0x08, 8:0x10, 16:0x18}
ACCEL_SENS       = {2:16384.0, 4:8192.0, 8:4096.0, 16:2048.0}

def now_ts(): return time.time()
def fmt_ts(ts=None):
    if ts is None: ts = now_ts()
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

# ===== FAKE 센서 =====
class FakeIMU:
    def __init__(self, seed=42):
        import random
        self.rng = random.Random(seed)
        self.t = 0
    def read_g(self):
        self.t += 1
        ax = self.rng.gauss(0.0, 0.02)
        ay = self.rng.gauss(0.0, 0.02)
        az = 1.0 + self.rng.gauss(0.0, 0.02)
        if self.t % 300 == 0:
            spike = self.rng.uniform(1.8, 3.5)
            which = self.rng.choice([0,1,2])
            if   which == 0: ax += spike
            elif which == 1: ay += spike
            else: az += spike
        return ax, ay, az

# ===== MPU-6050 드라이버 =====
class MPU6050:
    def __init__(self, bus=1, addr=MPU_ADDR, accel_range=8):
        self.addr = addr
        self.accel_range = accel_range if accel_range in ACCEL_RANGE_BITS else 8
        self.sens = ACCEL_SENS[self.accel_range]
        self.ok = False
        try:
            self.bus = SMBus(bus)
            self.bus.write_byte_data(self.addr, REG_PWR_MGMT_1, 0x00)
            self.bus.write_byte_data(self.addr, REG_ACCEL_CFG, ACCEL_RANGE_BITS[self.accel_range])
            self.ok = True
        except Exception:
            self.ok = False
    def _read_word_2c(self, reg):
        hi = self.bus.read_byte_data(self.addr, reg)
        lo = self.bus.read_byte_data(self.addr, reg+1)
        val = (hi<<8) + lo
        if val >= 0x8000: val = -((65535 - val) + 1)
        return val
    def read_g(self):
        try:
            ax = self._read_word_2c(REG_AX_H)     / self.sens
            ay = self._read_word_2c(REG_AX_H+2)   / self.sens
            az = self._read_word_2c(REG_AX_H+4)   / self.sens
            return ax, ay, az
        except Exception:
            return None

# ===== 간단 저역통과 =====
class LPF:
    def __init__(self, alpha=0.25):
        self.alpha = alpha
        self.y = None
    def step(self, x):
        if self.y is None: self.y = x
        else: self.y = self.alpha * x + (1 - self.alpha) * self.y
        return self.y

# ===== 이동 RMS =====
class RollingRMS:
    def __init__(self, n):
        self.n = max(1, n)
        self.buf = deque(maxlen=self.n)
        self.sum_sq = 0.0
    def step(self, x):
        if len(self.buf) == self.n:
            old = self.buf.popleft()
            self.sum_sq -= old*old
        self.buf.append(x)
        self.sum_sq += x*x
        return math.sqrt(self.sum_sq / len(self.buf))

# ===== 임팩트 검출기 =====
class ImpactDetector:
    def __init__(self, args):
        self.hz = args.hz
        self.dt = 1.0 / self.hz
        self.pre_n   = max(1, int(args.pre_ms  * self.hz / 1000.0))
        self.post_n  = max(1, int(args.post_ms * self.hz / 1000.0))
        self.hold_n  = max(1, int(args.hold_ms * self.hz / 1000.0))
        self.hold_hits_needed = max(1, int(self.hold_n * args.hold_ratio + 1e-9))
        self.vote_k = args.vote_k
        self.lockout_s = args.lockout_ms / 1000.0

        # thresholds
        self.threshold_g = args.threshold_g
        self.jerk_th = args.jerk_th
        self.rms_th  = args.rms_th

        self.rms = RollingRMS(n=max(1, int(args.rms_ms * self.hz / 1000.0)))
        self.lpf = LPF(alpha=args.lpf_alpha)

        self.buf = deque(maxlen=self.pre_n + self.post_n + 10)
        self.post_left = 0
        self.in_event = False
        self.lockout_until = 0.0
        self.prev_m = None

        # auto threshold
        self.auto_threshold = args.auto_threshold
        self.calib_left = int(args.calib_s * self.hz) if self.auto_threshold else 0
        self.std_k = args.std_k
        self._calib_buf_m = []
        self._calib_buf_jerk = []
        self._calib_buf_rms = []

    def _metric(self, ax, ay, az):
        return math.sqrt(ax*ax + ay*ay + az*az)

    def push(self, t, ax, ay, az):
        m_raw = self._metric(ax, ay, az)
        m = self.lpf.step(m_raw)

        if self.prev_m is None: jerk = 0.0
        else: jerk = abs(m - self.prev_m) / self.dt
        self.prev_m = m

        rms = self.rms.step(m - 1.0)  # baseline ~1g

        # auto threshold calibration
        if self.auto_threshold and self.calib_left > 0:
            self._calib_buf_m.append(m)
            self._calib_buf_jerk.append(jerk)
            self._calib_buf_rms.append(rms)
            self.calib_left -= 1
            if self.calib_left == 0:
                import statistics
                def calc_th(buf, base):
                    mu = statistics.mean(buf)
                    sigma = statistics.pstdev(buf) if len(buf) > 1 else 0.0
                    return mu + self.std_k * sigma if sigma > 0 else base
                self.threshold_g = calc_th(self._calib_buf_m, self.threshold_g)
                self.jerk_th    = calc_th(self._calib_buf_jerk, self.jerk_th)
                self.rms_th     = calc_th(self._calib_buf_rms, self.rms_th)
                print(f"[AUTO] threshold_g={self.threshold_g:.2f}, "
                      f"jerk_th={self.jerk_th:.2f}, rms_th={self.rms_th:.2f}")

        self.buf.append((t, ax, ay, az, m_raw, m, jerk, rms))
        return m, jerk, rms

    def _votes(self, m, jerk, rms):
        v = 0
        if m    >= self.threshold_g: v += 1
        if jerk >= self.jerk_th:     v += 1
        if rms  >= self.rms_th:      v += 1
        return v

    def want_trigger(self):
        if len(self.buf) < self.hold_n: return False
        tail = list(self.buf)[-self.hold_n:]
        hits = sum(1 for (_,_,_,_,_,m,jerk,rms) in tail if self._votes(m,jerk,rms) >= self.vote_k)
        return hits >= self.hold_hits_needed

    def want_release(self):
        n = max(1, int(0.2 * self.hz))
        if len(self.buf) < n: return False
        tail = list(self.buf)[-n:]
        ok = sum(1 for (_,_,_,_,_,m,jerk,rms) in tail if self._votes(m,jerk,rms) >= self.vote_k)
        return ok < max(1, int(0.3 * n))

# ===== CSV 스냅샷 =====
def save_snapshot(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp","ax_g","ay_g","az_g","metric_raw","metric_lpf","jerk_gps","rms_g"])
        for (t, ax, ay, az, m_raw, m, jerk, rms) in rows:
            w.writerow([fmt_ts(t),
                        f"{ax:.5f}", f"{ay:.5f}", f"{az:.5f}",
                        f"{m_raw:.5f}", f"{m:.5f}",
                        f"{jerk:.5f}", f"{rms:.5f}"])

# ===== 메인 =====
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hz", type=float, default=100.0)
    ap.add_argument("--pre_ms", type=int, default=1500)
    ap.add_argument("--post_ms", type=int, default=1500)
    ap.add_argument("--threshold_g", type=float, default=2.5)
    ap.add_argument("--jerk_th", type=float, default=8.0)
    ap.add_argument("--rms_ms", type=int, default=100)
    ap.add_argument("--rms_th", type=float, default=0.35)
    ap.add_argument("--hold_ms", type=int, default=40)
    ap.add_argument("--hold_ratio", type=float, default=0.6)
    ap.add_argument("--vote_k", type=int, default=2)
    ap.add_argument("--lockout_ms", type=int, default=1000)
    ap.add_argument("--lpf_alpha", type=float, default=0.25)
    # auto-threshold
    ap.add_argument("--auto-threshold", action="store_true")
    ap.add_argument("--calib_s", type=float, default=5.0)
    ap.add_argument("--std_k", type=float, default=3.0)
    # io
    ap.add_argument("--snapshot_dir", type=str, default="./snapshot")
    ap.add_argument("--bus", type=int, default=1)
    ap.add_argument("--addr", type=lambda x: int(x,0), default=MPU_ADDR)
    ap.add_argument("--accel_range", type=int, default=8, choices=[2,4,8,16])
    ap.add_argument("--fake", action="store_true")
    args = ap.parse_args()

    stop = {"flag": False}
    def _stop(*_):
        stop["flag"] = True
        print("\n[INFO] Stopping...")
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    if args.fake or not I2C_OK:
        imu = FakeIMU()
        print("[INFO] FAKE mode")
    else:
        dev = MPU6050(bus=args.bus, addr=args.addr, accel_range=args.accel_range)
        if not dev.ok:
            print("[INFO] I2C init failed → FAKE mode")
            imu = FakeIMU()
        else:
            imu = dev
            print("[INFO] I2C IMU ready")

    det = ImpactDetector(args)

    period = 1.0 / args.hz
    next_t = time.perf_counter()
    print(f"[INFO] Hz={args.hz}, TH={args.threshold_g}, jerk={args.jerk_th}, rms={args.rms_th}, "
          f"auto={args.auto_threshold}, calib_s={args.calib_s}")

    while not stop["flag"]:
        now = time.perf_counter()
        if now < next_t:
            time.sleep(max(0, next_t - now))
        next_t += period

        t = now_ts()
        r = imu.read_g()
        if r is None: continue
        ax, ay, az = r
        m, jerk, rms = det.push(t, ax, ay, az)

        if det.in_event:
            if det.post_left > 0:
                det.post_left -= 1
            elif det.want_release():
                rows = list(det.buf)[-(det.pre_n + det.post_n):]
                name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                path = os.path.join(args.snapshot_dir, name)
                save_snapshot(path, rows)
                det.in_event = False
                det.lockout_until = now_ts() + det.lockout_s
                print(f"[SNAPSHOT] saved: {path} rows={len(rows)}")
                print("[EVENT] end")
        else:
            if now_ts() < det.lockout_until:
                continue
            if det.want_trigger():
                det.in_event = True
                det.post_left = det.post_n
                print(f"[EVENT] start at {fmt_ts()} (m={m:.2f}, jerk={jerk:.1f}, rms={rms:.2f})")

    print("[INFO] Bye.")

if __name__ == "__main__":
    main()
