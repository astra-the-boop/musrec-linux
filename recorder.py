import os
import subprocess
import sys
import shutil
from time import sleep, time
from tqdm import tqdm

import numpy as np
import sounddevice as sd
import soundfile as sf
import tracks as t
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4, MP4Cover


def recorder(track_count,
             fileType="wav",
             sample_rate=44100,
             channels=2,
             blocksize=1024,
             skipWarning=False,
             outputDir=".",
             adSkip=True,
             service="spotify",
             bitrate="320k",
             config=False):
    os.makedirs(outputDir, exist_ok=True)

    def callback(indata, frames, time, status):
        if status:
            print(status)
        recordedChunks.append(indata.copy())

    if not skipWarning:
        # checks if external (non-python) dependencies / apps are presents :(
        if sys.platform != 'linux':
            raise RuntimeError(
                "!! MusRec Linux only supports Linux distros !!\nIf you're on macOS, please check out https://github.com/astra-the-boop/musrec")
        if not shutil.which('ffmpeg'):
            sys.exit(1) if input(
                "Missing: ffmpeg; ffmpeg is required for .mp3, .flac, .ogg exports\n\nPlease install it via Homebrew:\nbrew install ffmpeg\n\nEnter [c] to cancel; enter anything else to proceed") == "c" else None

    device_index = check_blackhole()



    print(f"Using device index: {device_index}")

    print(sd.query_devices())

    for i in range(int(track_count)):
        interrupted = False
        t.pause(service)
        duration = t.getDuration(service)
        if t.getPosition(service) != 0:
            t.setPlayerPos(0, service)
        title = t.getTitle(service)
        artist = t.getArtist(service)
        album = t.getAlbum(service)

        while t.adLikely(service) and adSkip:
            t.play(service)
            print("Advertisement likely, skipping recording for track")
            sleep(t.getDuration(service))

        recordedChunks = []
        t.play(service)

        print(
            f"({i}/{track_count}) Currently recording {title} by {artist} with length of {t.getDuration(service)} seconds; Pause music to stop recording"
        )

        with sd.InputStream(samplerate=sample_rate,
                            channels=channels,
                            callback=callback,
                            blocksize=blocksize,
                            device=device_index,
                            dtype='float32'):
            start_time = time()
            pbar = tqdm(total=int(duration), desc=f"{title} — {artist}", unit="sec")
            sleep(1)
            last = 0
            while t.isPlaying(service) and (time() - start_time) < duration:
                elapsed = int(time() - start_time)
                if int(elapsed) > last:
                    pbar.update(int(elapsed) - last)
                    last = int(elapsed)
                sleep(0.1)
            pbar.close()
            print("Recording stopped")

        interrupted = not t.isPlaying(service) and (time() - start_time) < duration

        if interrupted:
            print("Recording not saved due to user interrupt")
            break

        audio = np.concatenate(recordedChunks, axis=0)

        wav_file = f"{outputDir}/{title} — {artist}.wav"
        file_name = f"{title} — {artist}.{fileType}"
        file_path = f"{outputDir}/{file_name}"

        sf.write(wav_file, audio, sample_rate)

        saved_as = f"Saved as '{file_name}' in {outputDir}/. If audio is blank, check if 'BlackHole 2ch' or a multi-output device with it is being used for sound output in Audio MIDI Setup"

        if fileType == "wav":
            print(saved_as)

        if fileType == "mp3":
            if not config:
                subprocess.run([
                    "ffmpeg", "-y", "-i", wav_file, "-codec:a", "libmp3lame",
                    "-b:a", bitrate, file_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            else:
                subprocess.run([
                    "ffmpeg", "-y", "-i", wav_file, "-codec:a", "libmp3lame",
                    "-b:a", bitrate, file_path
                ])
            print(saved_as)

            print("Writing metadata...")
            file = EasyID3(file_path)
            file["title"] = title
            file["artist"] = artist
            file["album"] = album
            file.save()
            file = ID3(file_path)

            if t.fetchAlbumCover(title, artist, album, "cover.jpg") != None:
                with open("cover.jpg", "rb") as albumArt:
                    file.add(
                        APIC(encoding=3,
                             mime='image/jpeg',
                             type=3,
                             desc=f"Cover of {title} — {artist}",
                             data=albumArt.read()))
                file.save()

            print("Metadata saved")

            try:
                os.remove("cover.jpg")
            except FileNotFoundError:
                pass

        if fileType == "flac":
            if not config:
                subprocess.run([
                    "ffmpeg", "-y", "-i", wav_file, "-codec:a", "flac", file_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            else:
                subprocess.run([
                    "ffmpeg", "-y", "-i", wav_file, "-codec:a", "flac", file_path
                ])
            print(saved_as)

            print("Writing metadata...")
            file = FLAC(file_path)
            file["title"] = title
            file["artist"] = artist
            file["album"] = album

            if t.fetchAlbumCover(title, artist, album, "cover.jpg") != None:
                with open("cover.jpg", "rb") as albumArt:
                    art = Picture()
                    art.type = 3
                    art.mime = "image/jpeg"
                    art.desc = f"Cover of {title} — {artist}"
                    art.data = albumArt.read()
                    file.add_picture(art)
                file.save()

            print("Metadata saved")

        if fileType == "ogg":
            if not config:
                subprocess.run([
                    "ffmpeg", "-y", "-i", wav_file, "-codec:a", "libvorbis",
                    "-qscale:a", "10", file_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            else:
                subprocess.run([
                    "ffmpeg", "-y", "-i", wav_file, "-codec:a", "libvorbis",
                    "-qscale:a", "10", file_path
                ])
            print(saved_as)

            print("Writing metadata...")
            file = OggVorbis(file_path)
            file["title"] = title
            file["artist"] = artist
            file["album"] = album
            file.save()

            print("Metadata saved")

        if fileType == "m4a":
            if not config:
                subprocess.run([
                    "ffmpeg", "-y", "-i", wav_file, "-c:a", "alac", file_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            else:
                subprocess.run([
                    "ffmpeg", "-y", "-i", wav_file, "-c:a", "alac", file_path
                ])
            print(saved_as)
            print("Writing metadata...")
            file = MP4(file_path)
            file["\xa9nam"] = title
            file["\xa9ART"] = artist
            file["\xa9alb"] = album

            if t.fetchAlbumCover(title, artist, album, "cover.jpg") != None:
                with open("cover.jpg", "rb") as albumArt:
                    file["covr"] = [MP4Cover(albumArt.read(), imageformat=MP4Cover.FORMAT_JPEG)]

            file.save()
            print("Metadata saved")

        if fileType != "wav":
            os.remove(wav_file)

        try:
            os.remove("cover.jpg")
        except FileNotFoundError:
            pass