# TextToSound

借助 Edge 的微軟文字轉語音，實現超長文本轉換

## 安裝依賴

```shell
pip install msspeech pydub
sudo apt install ffmpeg
```

## 使用方式

```shell
# 輸入 txt 輸出生成音頻
python text_to_sound.py <input> <output>
# 顯示可用聲音
python text_to_sound.py -p
```

## 修改配置

```py
# 設定聲音樣式
VOICE_NAME = "zh-CN-YunxiNeural"
# 設定聲音語速
VOICE_RATE = 1.0
# 設定聲音音調
VOICE_PITCH = 0
# 設定聲音音量
VOICE_VOLUME = 1.0
# 緩存資料夾名稱
TMP_DIR_NAME = "tmp"
# 無法直接轉換時，分割檔案的字數
SPLIT_FILE_TEXT_SIZE = 19000
```
