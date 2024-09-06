import os
import re
import time
import queue
import ffmpeg
import os.path
import asyncio
import argparse
import threading
from typing import List
from threading import Thread
from msspeech import MSSpeech
from collections import defaultdict
from speech_generation.speech import Speech
from speech_generation.text_queue import TextQueue

DEFAULT_THREADS = 1
DEFAULT_OUTPUT_PATH = "voice/"

text_queue: TextQueue

output_file: str
output_file_count = 1
output_filename_queue = queue.Queue()


def create_output_folder(file_path: str) -> None:
    dir_path = os.path.dirname(file_path)
    os.makedirs(dir_path, exist_ok=True)


def get_output_file_count() -> int:
    with text_queue.lock:
        global output_file_count
        output_file_count += 1
        return output_file_count - 1


def generate_voice() -> None:
    speech = Speech()

    while True:
        text = text_queue.get()
        if text is None:
            break

        print(text)

        count = get_output_file_count()
        file_name, file_extension = output_file.rsplit(".", 1)
        output_file_name = f"{file_name}_{count}.{file_extension}"

        speech.generate(text, output_file_name)
        # output_filename_queue.put(output_file_name)


def multi_threading_generate_voice(thread_count: int) -> None:
    threads: List[Thread] = []
    for _ in range(thread_count):
        thread = threading.Thread(target=generate_voice)
        thread.start()
        threads.append(thread)
        time.sleep(1)

    for thread in threads:
        thread.join()


def print_format_voice_list(voice_data) -> None:
    voices = defaultdict(list)

    pattern = r"\(([^,]+), ([^)]+)\)"
    matches = re.findall(pattern, voice_data)

    for locale, voice in matches:
        voices[locale].append(voice)

    for locale, voice_names in voices.items():
        print(locale)
        for i, voice in enumerate(voice_names):
            if i == len(voice_names) - 1:
                print(f"  └─ {locale}-{voice}")
            else:
                print(f"  ├─ {locale}-{voice}")


async def show_voice_list(locale: str = "") -> None:
    mss = MSSpeech()

    output = ""
    voices = await mss.get_voices_list()
    for voice in voices:
        if voice["Locale"].lower() == locale.lower():
            output += voice["Name"] + "\n"
        elif locale == "":
            output += voice["Name"] + "\n"

    print_format_voice_list(output)


def extract_number(filename: str) -> int:
    match = re.search(r'\d+', filename)
    return int(match.group()) if match else 0


def merge_voice_files(input_files: list, output_file: str):
    list_file = 'temp_merge_voice_file_list.txt'

    with open(list_file, 'w') as f:
        for file in input_files:
            f.write(f"file '{file}'\n")

    ffmpeg.input(list_file, format='concat', safe=0).output(
        output_file, c='copy').run(overwrite_output=True)

    os.remove(list_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script processes a text file and converts it into a voice file (MP3)."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--input", type=str, metavar="FILENAME",
                       help="Input txt file name (e.g., a.txt)")
    group.add_argument("-l", "--list", type=str, metavar="LOCALE", nargs='?', const='all',
                       help="Show all available voice list or the voice list of the specified locale")

    parser.add_argument("-o", "--output", type=str, metavar="FILENAME",
                        help="Output voice file name (e.g., a.mp3). Default is 'voice/<Input_file_name>.mp3'")
    parser.add_argument("-c", "--concurrencies", type=int, metavar="NUMS",
                        help="Number of threads to use. Default is 5 if not specified.")
    parser.add_argument("-m", "--merge", action="store_true",
                        help="Merge all output files into one file")

    args = parser.parse_args()

    # list arguments
    if args.list:
        loop = asyncio.get_event_loop()
        if args.list == 'all':
            loop.run_until_complete(show_voice_list())
        else:
            loop.run_until_complete(show_voice_list(args.list))
        exit(0)

    # input arguments
    input_file = args.input

    try:
        with open(input_file, "r", encoding="UTF-8") as f:
            f.read()
    except:
        print(f"Error: Cannot open {input_file}")
        exit(1)

    # output arguments
    if args.output:
        output_file = args.output
        if os.path.basename(output_file) == "":
            print("Error: Output file name is not valid")
            exit(1)
        if not output_file.endswith(".mp3"):
            print("Error: Output file must be an MP3 file")
            exit(1)
    else:
        base_name = os.path.basename(input_file)
        file_name, _ = os.path.splitext(base_name)
        output_file = os.path.join(DEFAULT_OUTPUT_PATH, f"{file_name}.mp3")

    output_file = os.path.normpath(output_file)

    # concurrencies arguments
    if args.concurrencies:
        thread_count = args.concurrencies
    else:
        thread_count = DEFAULT_THREADS

    text_queue = TextQueue(input_file, 60)

    queue_len = text_queue.get_length()
    if thread_count > queue_len:
        thread_count = queue_len

    # generate voice
    create_output_folder(output_file)
    multi_threading_generate_voice(thread_count)

    # merge arguments
    if args.merge:
        output_files: List[str] = []
        while not output_filename_queue.empty():
            output_files.append(output_filename_queue.get())
        output_files.sort(key=extract_number)

        merge_voice_files(output_files, output_file)
