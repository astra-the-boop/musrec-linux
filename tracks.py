import requests
import subprocess
import dbus
import re

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
    player = getMprisPlayer()