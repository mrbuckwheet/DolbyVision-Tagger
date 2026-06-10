# 🎬 MrBuckwheet's Dolby Vision Tagger

Have you ever wanted your Plex server to show exactly which version of Dolby Vision your movies are using (like Profile 5 or Profile 8)? Plex doesn't show this by default, which makes it hard to automatically add those nice artwork overlays to your posters.

This tool solves that. It automatically scans your movie files, figures out their exact Dolby Vision format, and adds a clean text label directly to that movie in Plex.

It is designed to work perfectly alongside **[MrBuckwheet's Kometa Configurations](https://github.com/mrbuckwheet/kometa-config)** to automatically give your Plex library gorgeous, dynamic poster art overlays.

---

## ✨ Features

* **Smart Scanning:** Looks inside your video files to find the exact Dolby Vision profile.
* **Easy Web Dashboard:** Open a simple web page (port `3636`) to change your settings, see live logs, or click a button to run a scan right now.
* **Set It and Forget It:** Runs automatically in the background on a schedule so new movies get tagged without you doing a thing.
* **Safe & Clean:** It doesn't modify your actual video files at all—it only adds text labels inside Plex.

## 📦 Quick Start with Docker Compose

Add the following service layout into your environment's `docker-compose.yml` file:

```yaml
services:
  dv-tagger:
    image: mrbuckwheet/dolbyvision-tagger:latest
    container_name: dolbyvision-tagger
    restart: unless-stopped
    ports:
      - "3636:3636"
    environment:
      - TZ=America/New_York
      - PUID=1000
      - PGID=1000
    volumes:
      - /path/to/your/movies:/Movies        # Change the left side to your actual movie folder
      - ./config:/app/config                # Where your settings and logs will be saved
      - /etc/localtime:/etc/localtime:ro
```
---

---

## ⚙️ Settings Explained

The first time you start the container, it will create a settings file in your config folder. You can change these settings easily by opening the **Web UI** in your browser at `http://your-server-ip:3636`.

| Setting Name | What to Put Here |
| :--- | :--- |
| `PLEX_TOKEN` | **(Required)** Your secret Plex token. This allows the script to talk to your Plex server. |
| `PLEX_SERVER_URL` | The local network address of your Plex server (usually `http://127.0.0.1:32400`). |
| `PLEX_LIBRARIES` | The exact name of your movie library in Plex (usually just `Movies`). |
| `CRON_SCHEDULE` | How often the script runs automatically in the background. The default setting runs it twice a day (at 6:50 AM and 6:50 PM) to match MrBuckwheet's Kometa config which runs at 7am and 7pm daily. |
| `GENERAL_LABEL` | Set to `True` if you want a generic `Dolby Vision` label added to the movie, on top of the specific profile label (like 'Dolby Vision' and `Dolby Vision Profile 5`). |

---

---

## ⚠️ Crucial Step: Matching Your Folders

For this tool to work, it needs to look at your actual video files. It does this by combining your **Docker Compose Volume** and the `PLEX_PATH_PREFIX` setting.

1. **In your Docker Compose:** You must always map your actual host movie folder to `/Movies` inside the container (like `- /path/to/movies:/Movies`).
2. **In your Settings:** You use `PLEX_PATH_PREFIX` to tell this tool exactly what **Plex** calls that folder in its own library settings.

Look at the three examples below to find the one that matches your server setup:

### 💡 Scenario A: The paths are completely identical
Use this if your host files, Plex, and the container all use the same folder name.
* **Your actual folder on the host:** `/Movies`
* **What Plex sees:** `/Movies/Inception (2010)/Inception.mkv`

**How to set it up:**
* **Compose Volume:** `- /Movies:/Movies`
* **Settings:** `PLEX_PATH_PREFIX=/Movies`

### 💡 Scenario B: Plex uses a basic media folder shortcut
Use this if Plex looks in a generic `/media` folder, but your files live in `/Movies` on your host.
* **Your actual folder on the host:** `/Movies`
* **What Plex sees:** `/media/Movies/Inception (2010)/Inception.mkv`

**How to set it up:**
* **Compose Volume:** `- /Movies:/Movies`
* **Settings:** `PLEX_PATH_PREFIX=/media/Movies`

### 💡 Scenario C: Nested data folders
Use this if your actual files live deep inside a specific hard drive or data pool structure, but Plex sees it as a simple `/media` folder.
* **Your actual folder on the host:** `/data/Media/Movies`
* **What Plex sees:** `/media/Movies/Inception (2010)/Inception.mkv`

**How to set it up:**
* **Compose Volume:** `- /data/Media/Movies:/Movies`
* **Settings:** `PLEX_PATH_PREFIX=/media/Movies`

---

## 🤝 Need Poster Art Overlays?

Once your movies are tagged, head over to the main configuration project to learn how to turn those Plex labels into automatic poster borders, flags, and overlays:

👉 **[Get the Companion Kometa Configurations](https://github.com/mrbuckwheet/kometa-config)**

<!-- markdownlint-disable MD033 -->
<p align="center">
<a href="https://www.buymeacoffee.com/mrbuckwheet" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/lato-black.png" alt="Buy Me A Coffee" style="height: 51px !important;width: 217px !important;" ></a>
<!-- markdownlint-enable MD033 -->