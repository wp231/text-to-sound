import os
import sys
import asyncio
from msspeech import MSSpeech
from pydub import AudioSegment

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

if len(sys.argv) < 2:
	print("參數錯誤")
	sys.exit(1)
    
if sys.argv[1] == '-h' or sys.argv[1] == '--help':
	print("TextToSound.py <input> <output>  輸出文字聲音")
	print("TextToSound.py -p                顯示可用聲音")
	sys.exit(1)

if sys.argv[1] == '-p':
	IS_PRINT_VOICE = 1
else:
	IS_PRINT_VOICE = 0
	INPUT_FILE_NAME = sys.argv[1]
	OUTPUT_FILE_NAME = sys.argv[2]


class MicrosoftVoice():
	def __init__(self) -> None:
		self.mss = MSSpeech()

	async def Initialize(self, voice = "zh-CN-YunxiNeural", rate = 1.0, pitch = 0, volume = 1.0):
		await self.mss.set_voice(voice)
		await self.mss.set_rate(rate)
		await self.mss.set_pitch(pitch)
		await self.mss.set_volume(volume)

	async def TextToVoice(self, text:str, voice_file_name:str):
		chunk_size = SPLIT_FILE_TEXT_SIZE
		text_list = SplitString(text, chunk_size)
		text_len = len(text_list)
		text_len_count = len(str(text_len))

		# 創建緩存資料夾
		tmp_dir_path = os.path.join(os.curdir, TMP_DIR_NAME)
		if not os.path.exists(tmp_dir_path):
			os.mkdir(tmp_dir_path)
		
		for i in range(text_len):
			tmp_file_name = ("{:0" + str(text_len_count) + "d}.mp3").format(i)
			tmp_file_path = os.path.join(tmp_dir_path, tmp_file_name)
			# 生成音頻
			await self.mss.synthesize(text_list[i].strip(), tmp_file_path)
		
		MergeAudio(tmp_dir_path, voice_file_name)

		# 刪除緩存資料夾
		RemoveFolder(tmp_dir_path)

# 分割字串 text 按照 chunk_size 長度分割為 子字串
def SplitString(text, chunk_size):
	chunks = []
	current_chunk = ""

	for char in text:
		current_chunk += char
		if len(current_chunk) >= chunk_size and char == '\n':
			chunks.append(current_chunk)
			current_chunk = ""

	if current_chunk:
		chunks.append(current_chunk)

	return chunks

# 合併音頻
def MergeAudio(source_path, output_path, file_extension = ".mp3"):
	original_dir = os.getcwd()
	os.chdir(source_path)

	# 讀取文件並排序
	audio_files = [file for file in os.listdir() if file.endswith(file_extension)]
	audio_files.sort()

	# 建立一個空的音頻段
	combined_audio = AudioSegment.empty()
	# 依序合併音頻文件
	for file in audio_files:
		audio = AudioSegment.from_file(file)
		combined_audio += audio

	os.chdir(original_dir)
	# 輸出合併後的音頻檔案
	combined_audio.export(output_path, format="mp3", bitrate="48k")

	

# 刪除指定資料夾，包底下檔案
def RemoveFolder(folder_path):
    # 確保資料夾存在
    if os.path.exists(folder_path):
        # 取得資料夾中的所有檔案
        file_list = os.listdir(folder_path)
        
        # 刪除所有檔案
        for file_name in file_list:
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        # 刪除根資料夾
        os.rmdir(folder_path)

# 顯示所有可用的聲音語言
async def ShowVoiceList(locale = "zh-CN"):
	mss = MSSpeech()
	voices = await mss.get_voices_list()
	print("可用配音：")
	for voice in voices:
		if voice["Locale"] == locale:
			print(voice["Name"])

async def main():
	if IS_PRINT_VOICE:
		await ShowVoiceList()
	else:
		with open(INPUT_FILE_NAME, "r", encoding="UTF-8") as f:
			text = f.read()

		voice = MicrosoftVoice()
		await voice.Initialize(VOICE_NAME, VOICE_RATE, VOICE_PITCH, VOICE_VOLUME)
		await voice.TextToVoice(text, OUTPUT_FILE_NAME)



if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())