#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import serial
import time
import requests

# ==============================
# 설정
# ==============================
SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 9600
SERVER_URL = 'http://192.168.200.162:8080/api/events'

# GPIO 핀 (BCM 기준)
BTN_GENERAL = 22
BTN_PLASTIC = 23
BTN_GLASS = 24
BTN_CAN = 25

buttons = [BTN_GENERAL, BTN_PLASTIC, BTN_GLASS, BTN_CAN]

command_map = {
    BTN_GENERAL: "GENERAL",
    BTN_PLASTIC: "PLASTIC",
    BTN_GLASS: "GLASS",
    BTN_CAN: "CAN"
}

# ==============================
# 초기화
# ==============================
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
for pin in buttons:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ==============================
# 시리얼 연결
# ==============================
try:
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(2)
    print("시리얼 연결 성공")
except Exception as e:
    print("시리얼 연결 실패:", e)
    ser = None

# ==============================
# 서버 전송 함수
# ==============================
def send_to_server(trash_type):
    try:
        data = {
            "deviceCode": "DEVICE_001",
            "binCode": "BIN_001_" + trash_type,
            "trashTypeCode": trash_type,
            "isDefective": False,
            "defectReason": "",
            "confidence": 1.0,
            "imageUrl": "",
            "fillPercent": 0
        }
        response = requests.post(SERVER_URL, json=data, timeout=3)
        print(f"[서버 전송 성공] {trash_type} → {response.status_code}")
    except Exception as e:
        print(f"[서버 전송 실패] {e}")

# ==============================
# 버튼 처리 함수
# ==============================
def send_command(pin):
    cmd = command_map.get(pin)
    if not cmd:
        return
    print(f"[버튼] {cmd}")

    # 아두이노로 전송
    if ser:
        try:
            ser.write((cmd + '\n').encode())
            print(f"[아두이노 전송] {cmd}")
        except Exception as e:
            print("아두이노 전송 실패:", e)
    else:
        print("⚠️ 시리얼 연결 안됨 (테스트 모드)")

    # 서버로 전송
    send_to_server(cmd)

# ==============================
# 메인 루프
# ==============================
prev_states = {pin: 1 for pin in buttons}
print("버튼 입력 대기 중... (Ctrl+C 종료)")

try:
    while True:
        for pin in buttons:
            current_state = GPIO.input(pin)
            if current_state == 0 and prev_states[pin] == 1:
                send_command(pin)
            prev_states[pin] = current_state
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n종료")
finally:
    GPIO.cleanup()
    if ser:
        ser.close()
    print("GPIO 정리 완료")
