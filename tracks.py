import requests
import subprocess
import dbus
import os

def fetchAlbumCover(title, artist, album, saveAs="cover.jpg"):
    query = f"{title} {artist} {album}".replace(" ","+")
    response = requests.get(f"https://itunes.apple.com/search?term={query}&limit=1&media=music")
    data = response.json()
    if data["resultCount"] == 0:
        print("No cover found")
        return None
    artworkUrl = data["results"][0]["artworkUrl100"].replace("100x100","600x600")
    imgData = requests.get(artworkUrl).content
    with open(saveAs, "wb") as f:
        f.write(imgData)
    return saveAs

def getMprisPlayer(service="spotify"):
    bus = dbus.SessionBus()
    for services in bus.list_names():
        if service.lower() in services.lower() and services.startswith("org.mpris.MediaPlayer2."):
            return bus.get_object(services, "/org/mpris/MediaPlayer2")
    raise RuntimeError(f"No MPRIS player found for {service}")

def getMetadata(player):
    interface = dbus.Interface(player,dbus_interface="org.freedesktop.DBus.Properties")
    metadata = interface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
    return metadata

def getDuration(service="spotify"):
    player = getMprisPlayer(service)
    metadata = getMetadata(player)
    return int(metadata.get("mpris:length", 0)) / 1000000 #for some stupid ass reason, shit's in microseconds, yes. microseconds. not ms, micro.
                                                          #yk what else is micro? your d- unfunny sorry not sorry

def getPosition(service="spotify"):
    player = getMprisPlayer(service)
    interface = dbus.Interface(player,dbus_interface="org.freedesktop.DBus.Properties")
    return interface.Get("org.mpris.MediaPlayer2.Player", "Position") / 1000000

def setPlayerPos(position, service="spotify"):
    #remove the if when deploy for prod
    if os.environ.get("FLATPAK_ID"):
        subprocess.run(["flatpak-spawn", "--host", "playerctl", "-p", service, "position", str(position)], check=True)
    else:
        subprocess.run(["playerctl", "-p", service, "position", str(position)], check=True)

def pause(service="spotify"):
    player=getMprisPlayer(service)
    interface=dbus.Interface(player,dbus_interface="org.mpris.MediaPlayer2.Player")
    interface.Pause()

def play(service="spotify"):
    player=getMprisPlayer(service)
    interface = dbus.Interface(player,dbus_interface="org.mpris.MediaPlayer2.Player")
    interface.Play()

def getTitle(service="spotify"):
    metadata = getMetadata(getMprisPlayer(service))
    return str(metadata.get("xesam:title", ""))

def getArtist(service="spotify"):
    metadata = getMetadata(getMprisPlayer(service))
    artist = metadata.get("xesam:artist", "")
    return str(artist[0]) if artist else ""

def getAlbum(service="spotify"):
    metadata = getMetadata(getMprisPlayer(service))
    return str(metadata.get("xesam:album",""))

def isPlaying(service="spotify"):
    player = getMprisPlayer(service)
    interface = dbus.Interface(player, dbus_interface="org.freedesktop.DBus.Properties")
    return interface.Get("org.mpris.MediaPlayer2.Player","PlaybackStatus") == "Playing"

def adLikely(service="spotify"):
    if getTitle(service).strip() == "" or getArtist(service).strip() == "":
        return True
    elif getTitle(service).strip() == "" and getArtist(service).strip().lower() in ["advertisement", "spotify"] or getArtist(service).strip().lower() in ["advertisement", 'spotify']:
        return True
    elif getAlbum(service).strip() == "" and getTitle(service).strip() == "" and getDuration() <= 30:
        return True
    else:
        return False