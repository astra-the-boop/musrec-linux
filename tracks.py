import requests

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

