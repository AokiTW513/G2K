import sounddevice as sd
import numpy as np
import aubio
from pynput.keyboard import Controller
import time

#印出所有的裝置，找到你要的裝置後把前面那個數字放到device_id就可以了，然後channel指你要錄幾個聲道(這個是從1開始算)，target_channels是你要讀取哪個聲道(這個是從0開始算)，後面寫1 in代表只有單聲道
device_list = sd.query_devices()
print(device_list)

keyboard = Controller()
Testing = False

normalMode = True
last_mode_switch_time = 0
mode_switch_cooldown = 1.0
switchModKey = ['Switch']

device_id = 3
samplerate = 48000
blocksize = 1024
channels = 1
target_channel = 0

pitch_o = aubio.pitch("default", 2048, blocksize, samplerate)
pitch_o.set_unit("Hz")
pitch_o.set_silence(-40)

# 設定Hz多少(最小, 最大)會按什麼按鍵，可以設定多個按鍵
pitch_key_map = {
    (261, 269): ['a'], #左 第3弦第5格
    (296, 300): ['d'], #右 第3弦第7格
    (280, 285): ['k'], #跳 第3弦第6格
    (351, 356): ['w'], #上 第2弦第6格
    (372, 379): ['l'], #爬 第2弦第7格
    (313, 319): ['d', 'j'], #右跳 第3弦第9格
    (331, 339): ['k', 'd'], #右衝 第3弦第8格
    (231, 238): ['a', 'k'], #左衝 第3弦第3格
    (248, 252): ['a', 'j'], #左跳 第3弦第4格
    (194, 201): ['a', 's', 'j'], #左下衝 第4弦第5格
    (221, 225): ['d', 's', 'j'], #右下衝 第4弦第7格
    (496, 501): ['d', 'w', 'j'], #右上衝 第1弦第7格
    (442, 447): ['a', 'w', 'j'], #左上衝 第1弦第5格
    (469, 474): ['h'], #對話 第1弦第6格
    (394, 402): ['q'], #暫停 第2弦第8格 (1/3)
    (526, 530): ['d', 's', 'j', 'k'], #右hyper 第1弦第8格
    (418, 421): ['a', 's', 'j', 'k'], #左hyper 第1弦第4格
    (209, 212): ['w', 'j'], #上衝 第4弦第6格
    (157, 162): ['s'], #下 第5弦第6格
    (166, 172): ['s', 'j'], #下衝 第5弦第7格
    (558, 564): switchModKey, #切換模式 第1弦第9格
}

pitch_key_map_feather = {
    (261, 269): ['a'], #左 第3弦第5格
    (296, 300): ['d'], #右 第3弦第7格
    (280, 285): ['k'], #跳 第3弦第6格
    (351, 356): ['w'], #上 第2弦第6格
    (372, 379): ['l'], #爬 第2弦第7格
    (313, 319): ['d', 'j'], #右跳 第3弦第9格
    (331, 339): ['k', 'd'], #右衝 第3弦第8格
    (231, 238): ['a', 'k'], #左衝 第3弦第3格
    (248, 252): ['a', 'j'], #左跳 第3弦第4格
    (194, 201): ['a', 's', 'j'], #左下衝 第4弦第5格
    (221, 225): ['d', 's', 'j'], #右下衝 第4弦第7格
    (496, 501): ['d', 'w', 'j'], #右上衝 第1弦第7格
    (442, 447): ['a', 'w', 'j'], #左上衝 第1弦第5格
    (469, 474): ['h'], #對話 第1弦第6格
    (394, 402): ['q'], #暫停 第2弦第8格 (1/3)
    (526, 530): ['d', 's', 'j', 'k'], #右hyper 第1弦第8格
    (418, 421): ['a', 's', 'j', 'k'], #左hyper 第1弦第4格
    (209, 212): ['w', 'j'], #上衝 第4弦第6格
    (157, 162): ['s'], #下 第5弦第6格
    (166, 172): ['s', 'j'], #下衝 第5弦第7格
    (558, 564): switchModKey, #切換模式 第1弦第9格
}

current_keys = set()

def audio_callback(indata, frames, time_, status):
    global current_keys
    global normalMode
    global last_mode_switch_time
    if status:
        print(status)

    signal = indata[:, target_channel]
    pitch = pitch_o(signal.astype(np.float32))[0]

    if pitch > 0:
        print(f"偵測到音高：{pitch:.2f} Hz")
        if not Testing:
            new_keys = set()
            now = time.time()
            if normalMode: 
                for freq_range, keys in pitch_key_map.items():
                    if freq_range[0] <= pitch <= freq_range[1]:
                        if keys == switchModKey:
                            if now - last_mode_switch_time > mode_switch_cooldown:
                                print("切換至羽毛模式")
                                normalMode = False
                                last_mode_switch_time = now
                            else:
                                print("切換太快，忽略")
                        else:    
                            new_keys.update(keys)  # 加入多個鍵
            if not normalMode:
                for freq_range, keys in pitch_key_map_feather.items():
                    if freq_range[0] <= pitch <= freq_range[1]: 
                        if keys == switchModKey:
                            if now - last_mode_switch_time > mode_switch_cooldown:
                                print("切換至普通模式")
                                normalMode = False
                                last_mode_switch_time = now
                            else:
                                print("切換太快，忽略")
                        else:    
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
