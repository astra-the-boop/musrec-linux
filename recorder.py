import os
import subprocess
import sys
import shutil
from time import sleep, time
from tqdm import tqdm

import numpy as np
import sounddevice as sd
import soundfile as sf


def recorder(
        trackCount,
        fileType = "wav",
        sampleRate = 44100,
        channels = 2,
        blockSize = 1024,
        skipWarnings = False,
        outputDir = ".",
        adSkip = True,
        service="spotify",
        bitrate = "320k",
        config=False):
    os.makedirs(outputDir, exist_ok=True)
    def callback(inData, frames, time, status):
        if status:
            print(status)
        recordedChunks.append(inData.copy())

    if not skipWarnings:
        if sys.platform != "linux":
            raise RuntimeError("!! MusRec Linux only supports Linux !!\nIf you're on macOS, please check out https://github.com/astra-the-boop/musrec")
        if not shutil.which("ffmpeg"):
            sys.exit(1) if input(
                "Missing: ffmpeg; ffmpeg is required for .mp3, .flac, .ogg exports\nPlease install it\n\nEnter [c] to cancel; enter anything else to proceed") == "c" else None


    recordedChunks = []

def checkMonitorDevice() -> int:
    for i, device in enumerate(sd.query_devices()):
        if "monitor" in device["name"].lower():
            return i
    raise RuntimeError("No PulseAudio monitor device found. You may need to enable one via pavucontrol")