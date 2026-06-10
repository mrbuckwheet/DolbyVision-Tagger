import os
import sys
import pathlib
import subprocess
import json
from datetime import datetime
from plexapi.server import PlexServer

PLEX_TOKEN = os.getenv('PLEX_TOKEN')
PLEX_SERVER_URL = os.getenv('PLEX_SERVER_URL', 'http://plex:32400')
BINARIES_PATH = os.getenv('BINARIES_PATH', '/usr/local/bin')
LIBRARIES = os.getenv('PLEX_LIBRARIES', 'Movies').split(',')
GENERAL_LABEL = os.getenv('GENERAL_LABEL', 'True').lower() in ('true', '1', 't')
PLEX_PATH = os.getenv('PLEX_PATH_PREFIX', '/Media/Movies')
LOCAL_PATH = os.getenv('LOCAL_PATH_PREFIX', '/Movies')

fixes_applied = 0
tags_applied = {}

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if not PLEX_TOKEN:
    print(f"[{get_timestamp()}] ❌ Error: PLEX_TOKEN variable is missing. Pass it via Docker environment.", flush=True)
    sys.exit(1)

def log_activity(message):
    print(f"[{get_timestamp()}] {message}", flush=True)

print(f"=== MrBuckwheet's Dolby Vision Tagger Run Started at {get_timestamp()} ===", flush=True)
print(f"[{get_timestamp()}] =============================================================", flush=True)
print(f"[{get_timestamp()}]               MrBuckwheet's Dolby Vision Tagger              ", flush=True)
print(f"[{get_timestamp()}] =============================================================", flush=True)
print(f"[{get_timestamp()}]", flush=True)

log_activity("🔗 Initializing API connections to Plex Media Server...")
try:
    plex = PlexServer(PLEX_SERVER_URL, PLEX_TOKEN, timeout=20)
    binaries = pathlib.Path(BINARIES_PATH)
except Exception as e:
    log_activity(f"❌ Critical Connection Error: Could not connect to Plex Server.")
    log_activity(f"👉 Diagnostic Details: {str(e)}")
    log_activity("💡 Check your Plex Server URL, Token credentials, and network firewall routing rules.")
    sys.exit(1)

for library in LIBRARIES:
    library = library.strip()
    if not library:
        continue
        
    log_activity(f"🎬 Scanning library section: {library}")
    try:
        videos = plex.library.section(library)
        all_videos = videos.all()
        log_activity(f"📦 Found {len(all_videos)} total movies to evaluate.")
    except Exception:
        log_activity(f"⚠️ Warning: Could not locate library [{library}]. Skipping...")
        try:
            valid_sections = [sect.title for sect in plex.library.sections()]
            if valid_sections:
                log_activity(f"💡 Available matching libraries found on server: {', '.join(valid_sections)}")
        except Exception:
            pass
        continue
    
    for video in all_videos:
        if not video.locations:
            continue
            
        path = video.locations[0]
        local_path = path.replace(PLEX_PATH, LOCAL_PATH)
        
        if not os.path.exists(local_path):
            continue

        log_activity(f"🔍 Analyzing [{video.title}] for Dolby Vision profile metadata...")

        ffmpeg = [
            binaries / 'ffmpeg6', '-t', '120', '-i', f'{local_path}', 
            '-c:v', 'copy', '-to', '1', '-f', 'hevc', '-y', '-'
        ]
        ffmpeg_result = subprocess.run(ffmpeg, capture_output=True)
        
        dovi_tool_extract = [binaries / 'dovi_tool', 'extract-rpu', '-', '-o', '/tmp/RPU.bin']
        dovi_result = subprocess.run(dovi_tool_extract, input=ffmpeg_result.stdout, capture_output=True)
        
        if dovi_result.returncode != 0:
            removed_any = False
            for l in video.labels:
                if l.tag.lower().startswith('dolby vision'):
                    log_activity(f"🗑️ Removing legacy/invalid DV label from [{video.title}]")
                    video.removeLabel(l.tag)
                    removed_any = True
                    fixes_applied += 1
            if removed_any:
                video.reload()
            continue
            
        dovi_tool_info = [binaries / 'dovi_tool', 'info', '-i', '/tmp/RPU.bin', '-f', '0']
        dovi_result = subprocess.run(dovi_tool_info, capture_output=True)
        
        if dovi_result.returncode != 0:
            continue
            
        output = dovi_result.stdout.decode('utf-8')
        try:
            metadata = json.loads(output.split('\n', 1)[1])
            dv_profile = metadata['dovi_profile']
            dv_el_type = metadata.get('el_type', '')
            label = f'Dolby Vision P{dv_profile} {dv_el_type}'.strip()
            
            current_labels = [l.tag.lower() for l in video.labels]
            
            removed_any = False
            for l in video.labels:
                if l.tag.lower().startswith('dolby vision p'):
                    if l.tag.lower() != label.lower():
                        log_activity(f"🛡️ Safety Check: Correcting mismatched DV label [{l.tag}] -> [{label}] on [{video.title}]")
                        video.removeLabel(l.tag)
                        removed_any = True
                        fixes_applied += 1
            if removed_any:
                video.reload()
                current_labels = [l.tag.lower() for l in video.labels]
            
            if label.lower() not in current_labels:
                log_activity(f"✅ Tagging [{video.title}] -> {label}")
                video.addLabel(label)
                tags_applied[label] = tags_applied.get(label, 0) + 1
                
            if GENERAL_LABEL and 'dolby vision' not in current_labels:
                log_activity(f"✅ Tagging [{video.title}] -> Dolby Vision")
                video.addLabel('Dolby Vision')
                tags_applied['Dolby Vision'] = tags_applied.get('Dolby Vision', 0) + 1
                
        except (json.JSONDecodeError, IndexError, KeyError):
            continue

log_activity("🏁 Scan complete! Movie tagging processing has finished.")
print(f"[{get_timestamp()}]", flush=True)
log_activity("=============================================================")
log_activity("📊                       RUN SUMMARY                         ")
log_activity("=============================================================")
log_activity(f"🛠️ Total tags corrections/removals applied: {fixes_applied}")
if tags_applied:
    log_activity("🏷️ Breakdown of tags successfully applied to movies:")
    for tag, count in sorted(tags_applied.items()):
        log_activity(f"   ▪️ {tag}: {count} item(s)")
else:
    log_activity("🏷️ Breakdown of tags successfully applied to movies: 0 tags added.")
log_activity("=============================================================")