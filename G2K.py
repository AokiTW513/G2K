import sounddevice as sd
import numpy as np
import aubio
from pynput.keyboard import Controller
import time
import csv 

#印出所有的裝置，找到你要的裝置後把前面那個數字放到device_id就可以了，然後channel指你要錄幾個聲道(這個是從1開始算)，target_channels是你要讀取哪個聲道(這個是從0開始算)，後面寫1 in代表只有單聲道
device_list = sd.query_devices()
print(device_list)

keyboard = Controller()
Testing = False

device_id = 2
samplerate = 48000
blocksize = 1024
channels = 1
target_channel = 0

pitch_o = aubio.pitch("default", 2048, blocksize, samplerate)
pitch_o.set_unit("Hz")
pitch_o.set_silence(-40)

# 設定Hz多少(最小, 最大)會按什麼按鍵，可以設定多個按鍵
pitch_key_map = {}

reader = csv.DictReader(open('key_bind.csv', 'r', encoding='utf-8'))
for row in reader:
    min_pitch = float(row['min_pitch'])
    max_pitch = float(row['max_pitch'])
    keys = row['keys'].split('|')
    pitch_key_map[(min_pitch, max_pitch)] = keys


current_keys = set()

def audio_callback(indata, frames, time_, status):
    global current_keys
    if status:
        print(status)

    signal = indata[:, target_channel]
    pitch = pitch_o(signal.astype(np.float32))[0]

    if pitch > 0:
        print(f"偵測到音高：{pitch:.2f} Hz")
        if not Testing:
            new_keys = set()
            for freq_range, keys in pitch_key_map.items():
                if freq_range[0] <= pitch <= freq_range[1]:
                    new_keys.update(keys)  # 加入多個鍵 

            # 找出要放開的鍵
            keys_to_release = current_keys - new_keys
            # 找出要按下的新鍵
            keys_to_press = new_keys - current_keys

            for key in keys_to_release:
                print(f"釋放鍵盤鍵：{key}, 因為你現在是{pitch:.2f} Hz")
                keyboard.release(key)

            for key in keys_to_press:
                print(f"按下鍵盤鍵：{key}")
                keyboard.press(key)

            current_keys = new_keys
    else:
        if current_keys:
            for key in current_keys:
                print(f"無音高，釋放鍵盤鍵：{key}")
                keyboard.release(key)
            current_keys = set()

with sd.InputStream(channels=channels, callback=audio_callback,
                    blocksize=blocksize, samplerate=samplerate,
                    device=device_id):
    print("開始偵測吉他音高... 按 Ctrl+C 停止")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("停止偵測")
