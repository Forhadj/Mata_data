#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MetaGhost X GeoTracker v6.1 (Security & Stability Fix)
By: Md Forhad | GitHub: Forhadj | Telegram: @f_forhad

A tool to extract, convert, and manage image metadata & GPS coordinates.
"""

import os
import re
import sys
import json
import math
import time
import shutil
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path

# ─── Global Variables ───
GITHUB_URL = "https://github.com/Forhadj"

# ─── Dependency Check (No Auto-Install) ───
MISSING_DEPS = []
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    from rich.markdown import Markdown
except ImportError:
    MISSING_DEPS.append("rich")

try:
    import requests
except ImportError:
    MISSING_DEPS.append("requests")

if MISSING_DEPS:
    print("[!] Missing required packages: {}".format(", ".join(MISSING_DEPS)))
    print("[*] Please install them manually:")
    print("    pip install {}".format(" ".join(MISSING_DEPS)))
    sys.exit(1)

# ─── Configuration ───
console = Console()
VERSION = "6.1"
CONFIG_DIR = Path.home() / ".metaghost"
CONFIG_FILE = CONFIG_DIR / "config.json"
EXPORT_DIR = CONFIG_DIR / "exports"
BACKUP_DIR = CONFIG_DIR / "backups"
LOG_FILE = CONFIG_DIR / "activity.log"

for d in [CONFIG_DIR, EXPORT_DIR, BACKUP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Logging ───
def log_activity(msg):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("[{}] {}\n".format(ts, msg))
    except OSError:
        pass

# ─── Config Management ───
def load_config():
    defaults = {
        "auto_backup": True,
        "auto_export": False,
        "default_export_format": "json",
        "map_provider": "google",
        "api_delay": 1.0,
        "fetch_weather": True,
        "fetch_address": True,
    }
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                defaults.update(saved)
    except (json.JSONDecodeError, OSError):
        pass
    return defaults

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except OSError as e:
        console.print("[yellow][!] Could not save config: {}[/yellow]".format(e))

config = load_config()

# ─── ExifTool Check ───
def check_exiftool():
    try:
        subprocess.run(
            ["exiftool", "-ver"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

# ─── Banner ───
def print_banner():
    banner = """
 [bold cyan]███╗   ███╗███████╗████████╗ ████╗ [/bold cyan][bold yellow] ██████╗ ██╗  ██╗[/bold yellow]
 [bold cyan]████╗ ████║██╔════╝╚══██╔══╝██╔══██╗[/bold cyan][bold yellow]██╔════╝ ╚██╗██╔╝[/bold yellow]
 [bold cyan]██╔████╔██║█████╗     ██║   ███████║[/bold cyan][bold yellow]██║  ███╗ ╚███╔╝ [/bold yellow]
 [bold cyan]██║╚██╔╝██║██╔══╝     ██║   ██╔══██║[/bold cyan][bold yellow]██║   ██║ ██╔██╗ [/bold yellow]
 [bold cyan]██║ ╚═╝ ██║███████╗   ██║   ██║  ██║[/bold cyan][bold yellow]╚██████╔╝██╔╝ ██╗[/bold yellow]
 [bold cyan]╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝[/bold cyan][bold yellow] ╚═════╝ ╚═╝  ╚═╝[/bold yellow]
"""
    info = (
        "[bold green]Developer:[/bold green] Md Forhad  |  "
        "[bold blue]GitHub:[/bold blue] Forhadj  |  "
        "[bold magenta]Telegram:[/bold magenta] @f_forhad"
    )
    console.print(
        Panel(
            banner + "\n" + info.center(70),
            title="[bold white]MetaGhost X GeoTracker v{}[/bold white]".format(VERSION),
            border_style="cyan",
            padding=(1, 2),
        )
    )

# ─── GPS Math ───
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def decimal_to_dms(dd, is_lat=True):
    direction = "N"
    if is_lat:
        direction = "N" if dd >= 0 else "S"
    else:
        direction = "E" if dd >= 0 else "W"
    dd = abs(dd)
    d = int(dd)
    m = int((dd - d) * 60)
    s = round((dd - d - m / 60) * 3600, 2)
    return "{}° {}' {}\" {}".format(d, m, s, direction)

# ─── GPS Parsing ───
def parse_single_dms_or_decimal(s):
    s = s.strip()
    # Decimal only
    dec_match = re.match(r'^([+-]?\d+(?:\.\d+)?)$', s)
    if dec_match:
        return float(dec_match.group(1))
    # Decimal + direction
    dec_dir = re.match(r'^([+-]?\d+(?:\.\d+)?)\s*([NSEWnsew])$', s)
    if dec_dir:
        val = float(dec_dir.group(1))
        dirc = dec_dir.group(2).upper()
        if dirc in ('S', 'W'):
            val = -abs(val)
        return val
    # DMS with symbols
    m = re.match(
        r'^\s*(\d+)\s*(?:°|deg)?\s*(\d+)\s*(?:\'|\')?\s*([\d.]+)\s*(?:"|”)?\s*([NSEWnsew])\s*$',
        s,
        re.IGNORECASE,
    )
    if m:
        d, mn, sec, ref = m.groups()
        dd = float(d) + float(mn) / 60.0 + float(sec) / 3600.0
        if ref.upper() in ('S', 'W'):
            dd = -dd
        return round(dd, 6)
    # Space-separated DMS
    parts = re.split(r'\s+', s)
    if len(parts) >= 3:
        ref = parts[-1].upper() if re.match(r'^[NSEWnsew]$', parts[-1]) else None
        d, mn, sec = parts[0], parts[1], parts[2]
        try:
            dd = float(d) + float(mn) / 60.0 + float(sec) / 3600.0
            if ref in ('S', 'W'):
                dd = -dd
            return round(dd, 6)
        except ValueError:
            pass
    return None

def convert_gps_string(gps_string):
    if not gps_string or not isinstance(gps_string, str):
        raise ValueError("GPS string is required.")
    parts = [p.strip() for p in re.split(r'[;,]', gps_string) if p.strip()]
    if len(parts) < 2:
        tokens = gps_string.strip().split()
        if len(tokens) >= 6:
            lat_part = " ".join(tokens[:3])
            lon_part = " ".join(tokens[3:6])
        else:
            raise ValueError(
                "Could not separate Latitude and Longitude. Use comma (,) or semicolon (;)."
            )
    else:
        lat_part, lon_part = parts[0], parts[1]
    lat = parse_single_dms_or_decimal(lat_part)
    lon = parse_single_dms_or_decimal(lon_part)
    if lat is None:
        raise ValueError("Invalid latitude format: '{}'".format(lat_part))
    if lon is None:
        raise ValueError("Invalid longitude format: '{}'".format(lon_part))
    return round(lat, 6), round(lon, 6)

# ─── API Calls with Rate Limiting ───
_last_api_call = 0

def _rate_limit():
    """Ensure at least `api_delay` seconds between API calls."""
    global _last_api_call
    delay = config.get("api_delay", 1.0)
    elapsed = time.time() - _last_api_call
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _last_api_call = time.time()

def reverse_geocode(lat, lon):
    if not config.get("fetch_address", True):
        return None
    _rate_limit()
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "jsonv2",
        "lat": str(lat),
        "lon": str(lon),
        "accept-language": "en",
    }
    headers = {"User-Agent": "MetaGhostX-GeoTracker/{}".format(VERSION)}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        console.print("[yellow][!] Geocoding timed out.[/yellow]")
    except requests.exceptions.HTTPError as e:
        console.print("[yellow][!] Geocoding HTTP error: {}[/yellow]".format(e.response.status_code))
    except requests.exceptions.RequestException as e:
        console.print("[yellow][!] Geocoding request failed: {}[/yellow]".format(e))
    return None

def get_weather(lat, lon):
    if not config.get("fetch_weather", True):
        return {}
    _rate_limit()
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        "latitude={}&longitude={}&current_weather=true"
    ).format(lat, lon)
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("current_weather", {})
    except requests.exceptions.Timeout:
        console.print("[yellow][!] Weather API timed out.[/yellow]")
    except requests.exceptions.RequestException as e:
        console.print("[yellow][!] Weather request failed: {}[/yellow]".format(e))
    return {}

# ─── Display Results ───
def display_location_results(lat, lon, show_weather=True):
    table = Table(
        title="[bold green]:round_pushpin: GPS Location Analysis[/bold green]",
        border_style="yellow",
        padding=(0, 1),
        expand=True,
    )
    table.add_column("Property", style="bold cyan", justify="right", no_wrap=True)
    table.add_column("Details", style="white", overflow="fold")

    table.add_row("Decimal Coordinates", "[bold white]{}, {}[/bold white]".format(lat, lon))
    table.add_row("DMS Latitude", decimal_to_dms(lat, is_lat=True))
    table.add_row("DMS Longitude", decimal_to_dms(lon, is_lat=False))

    provider = config.get("map_provider", "google")
    if provider == "google":
        map_url = "https://www.google.com/maps?q={},{}"
        table.add_row(
            "Google Maps",
            "[bold blue]{}[/bold blue]".format(map_url.format(lat, lon)),
        )
    else:
        map_url = "https://www.openstreetmap.org/?mlat={}&mlon={}"
        table.add_row(
            "OpenStreetMap",
            "[bold blue]{}[/bold blue]".format(map_url.format(lat, lon)),
        )

    info = None
    if config.get("fetch_address", True):
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold yellow]Fetching Address..."),
            transient=True,
        ) as progress:
            progress.add_task("geocode", total=None)
            info = reverse_geocode(lat, lon)

        if info and info.get("display_name"):
            table.add_row(
                "Address",
                "[bold magenta]{}[/bold magenta]".format(info.get("display_name")),
            )
            addr = info.get("address", {})
            if addr.get("country"):
                table.add_row("Country", addr.get("country"))
            city = addr.get("city") or addr.get("town") or addr.get("village")
            if city:
                table.add_row("City", city)
            if addr.get("postcode"):
                table.add_row("Postcode", addr.get("postcode"))

    if show_weather and config.get("fetch_weather", True):
        weather = get_weather(lat, lon)
        if weather:
            temp = weather.get("temperature")
            wind = weather.get("windspeed")
            if temp is not None:
                table.add_row("Current Temp", "{}°C".format(temp))
            if wind is not None:
                table.add_row("Wind Speed", "{} km/h".format(wind))

    console.print(table)
    return info

# ─── Export ───
def export_results(data, fmt=None):
    fmt = fmt or config.get("default_export_format", "json")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = EXPORT_DIR / "metaghost_export_{}.{}".format(ts, fmt)
    try:
        if fmt == "json":
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif fmt == "txt":
            with open(fname, "w", encoding="utf-8") as f:
                for k, v in data.items():
                    f.write("{}: {}\n".format(k, v))
        console.print("[bold green][✓] Exported to:[/bold green] {}".format(fname))
        log_activity("Exported results to {}".format(fname))
    except OSError as e:
        console.print("[bold red][!] Export failed: {}[/bold red]".format(e))

# ─── Extract Metadata ───
def extract_metadata(path, silent=False):
    if not check_exiftool():
        if not silent:
            console.print(
                "[bold red][!] ExifTool is not installed![/bold red]\n"
                "    Install it: [yellow]pkg install exiftool[/yellow] (Termux)\n"
                "    Or: [yellow]sudo apt install libimage-exiftool-perl[/yellow] (Linux)"
            )
        return None
    if not path or not os.path.isfile(path):
        if not silent:
            console.print("[bold red][!] Invalid or non-existent file path.[/bold red]")
        return None
    try:
        out = subprocess.check_output(
            ["exiftool", path],
            stderr=subprocess.PIPE,
            timeout=30,
        ).decode("utf-8", errors="ignore")
    except subprocess.TimeoutExpired:
        if not silent:
            console.print("[bold red][!] ExifTool timed out.[/bold red]")
        return None
    except subprocess.CalledProcessError as e:
        if not silent:
            console.print("[bold red][!] ExifTool error: {}[/bold red]".format(e))
        return None
    except OSError as e:
        if not silent:
            console.print("[bold red][!] Could not run ExifTool: {}[/bold red]".format(e))
        return None

    meta = {}
    lines = out.strip().split("\n")
    for line in lines:
        if ":" in line:
            tag, val = line.split(":", 1)
            meta[tag.strip()] = val.strip()

    if not silent:
        meta_table = Table(
            title="[bold blue]:framed_picture: Metadata: {}[/bold blue]".format(os.path.basename(path)),
            border_style="blue",
            padding=(0, 1),
            expand=True,
        )
        meta_table.add_column("Tag", style="bold yellow", no_wrap=True)
        meta_table.add_column("Value", style="white", overflow="fold")
        for k, v in list(meta.items())[:30]:
            meta_table.add_row(k, v)
        console.print(meta_table)

    gps_pos_match = re.search(r"GPS Position\s+: (.+)", out)
    lat_tag = re.search(r"GPS Latitude\s+: (.+)", out)
    lon_tag = re.search(r"GPS Longitude\s+: (.+)", out)

    gps_raw = None
    if gps_pos_match:
        gps_raw = gps_pos_match.group(1).strip()
    elif lat_tag and lon_tag:
        gps_raw = "{}, {}".format(lat_tag.group(1).strip(), lon_tag.group(1).strip())

    result = {"file": path, "metadata": meta, "gps_raw": gps_raw}

    if not gps_raw:
        if not silent:
            console.print("[bold red][✘] No GPS Data Found in this image.[/bold red]")
        log_activity("Extracted metadata from {} (no GPS)".format(path))
        return result

    try:
        lat, lon = convert_gps_string(gps_raw)
        result["latitude"] = lat
        result["longitude"] = lon
        if not silent:
            info = display_location_results(lat, lon)
            result["address_info"] = info
    except ValueError as e:
        if not silent:
            console.print("[bold red][✘] GPS Conversion Error: {}[/bold red]".format(e))
    except Exception as e:
        if not silent:
            console.print("[bold red][✘] Unexpected GPS error: {}[/bold red]".format(e))

    if not silent and config.get("auto_export"):
        export_results(result)

    log_activity("Extracted metadata from {}".format(path))
    return result

# ─── Remove Metadata ───
def remove_metadata(path, silent=False):
    if not check_exiftool():
        if not silent:
            console.print(
                "[bold red][!] ExifTool is not installed![/bold red]\n"
                "    Install it: [yellow]pkg install exiftool[/yellow] (Termux)\n"
                "    Or: [yellow]sudo apt install libimage-exiftool-perl[/yellow] (Linux)"
            )
        return False
    if not path or not os.path.isfile(path):
        if not silent:
            console.print("[bold red][!] Invalid or non-existent file path.[/bold red]")
        return False

    if config.get("auto_backup", True):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / "{}_{}".format(ts, os.path.basename(path))
        try:
            shutil.copy2(path, backup_path)
            if not silent:
                console.print("[bold yellow][!] Backup created:[/bold yellow] {}".format(backup_path))
        except OSError as e:
            if not silent:
                console.print("[bold red][!] Backup failed: {}[/bold red]".format(e))
            return False

    try:
        subprocess.run(
            ["exiftool", "-all=", "-overwrite_original", path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        if not silent:
            console.print("[bold green][✓] Metadata removed successfully![/bold green]")
        log_activity("Removed metadata from {}".format(path))
        return True
    except subprocess.TimeoutExpired:
        if not silent:
            console.print("[bold red][!] ExifTool timed out during removal.[/bold red]")
    except subprocess.CalledProcessError as e:
        if not silent:
            console.print("[bold red][!] ExifTool failed: {}[/bold red]".format(e))
    except OSError as e:
        if not silent:
            console.print("[bold red][!] Could not run ExifTool: {}[/bold red]".format(e))
    return False

# ─── Batch Processing ───
def batch_process():
    folder = Prompt.ask(
        "[bold cyan][>] Enter folder path containing images[/bold cyan]"
    ).strip()
    if not os.path.isdir(folder):
        console.print("[bold red][!] Invalid folder path.[/bold red]")
        return

    valid_exts = (".jpg", ".jpeg", ".png", ".tiff", ".webp", ".heic")
    files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(valid_exts)
    ]
    if not files:
        console.print("[bold red][!] No image files found.[/bold red]")
        return

    action = Prompt.ask(
        "[bold cyan]Action?[/bold cyan]",
        choices=["extract", "remove", "both"],
        default="extract",
    )
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold yellow]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        transient=False,
    ) as progress:
        task = progress.add_task(
            "[cyan]Processing {} files...".format(len(files)), total=len(files)
        )
        for fpath in files:
            if action in ("extract", "both"):
                res = extract_metadata(fpath, silent=True)
                if res:
                    results.append(res)
            if action in ("remove", "both"):
                remove_metadata(fpath, silent=True)
            progress.advance(task)

    # Summary
    sum_table = Table(
        title="[bold green]:open_file_folder: Batch Process Summary ({} files)[/bold green]".format(len(files)),
        border_style="green",
        expand=True,
    )
    sum_table.add_column("File", style="bold cyan")
    sum_table.add_column("GPS", style="white")
    sum_table.add_column("Status", style="bold green")

    gps_count = 0
    for r in results:
        has_gps = "✓ GPS" if r.get("latitude") else "✗ No GPS"
        if r.get("latitude"):
            gps_count += 1
        sum_table.add_row(os.path.basename(r["file"]), has_gps, "[green]Done[/green]")

    console.print(sum_table)
    console.print(
        "[bold yellow]:bar_chart: Total files:[/bold yellow] {}  |  "
        "[bold green]With GPS:[/bold green] {}".format(len(files), gps_count)
    )

    if results and Confirm.ask(
        "[bold cyan]Export batch results?[/bold cyan]", default=True
    ):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = EXPORT_DIR / "batch_export_{}.json".format(ts)
        try:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            console.print("[bold green][✓] Batch results saved to:[/bold green] {}".format(fname))
            log_activity("Batch processed {} files, saved to {}".format(len(files), fname))
        except OSError as e:
            console.print("[bold red][!] Export failed: {}[/bold red]".format(e))

# ─── GPS Converter ───
def gps_converter_menu():
    gps_in = Prompt.ask(
        "[bold cyan][>] Enter GPS (DMS or Decimal, comma separated)[/bold cyan]"
    ).strip()
    if not gps_in:
        console.print("[bold red][!] Empty input.[/bold red]")
        return
    try:
        lat, lon = convert_gps_string(gps_in)
        display_location_results(lat, lon)
    except ValueError as e:
        console.print("[bold red][✘] Invalid GPS format: {}[/bold red]".format(e))

# ─── Distance Calculator ───
def distance_calculator():
    console.print("[bold cyan]:straight_ruler: Distance Calculator (Haversine)[/bold cyan]")
    p1 = Prompt.ask("[bold cyan]Point 1 (lat, lon)[/bold cyan]").strip()
    p2 = Prompt.ask("[bold cyan]Point 2 (lat, lon)[/bold cyan]").strip()
    try:
        lat1, lon1 = convert_gps_string(p1)
        lat2, lon2 = convert_gps_string(p2)
        dist_km = haversine(lat1, lon1, lat2, lon2)
        dist_m = dist_km * 1000
        dist_nm = dist_km * 0.539957
        table = Table(
            title="[bold green]:straight_ruler: Distance Result[/bold green]",
            border_style="yellow",
            expand=True,
        )
        table.add_column("Unit", style="bold cyan")
        table.add_column("Value", style="white")
        table.add_row("Kilometers", "{:.3f} km".format(dist_km))
        table.add_row("Meters", "{:.2f} m".format(dist_m))
        table.add_row("Nautical Miles", "{:.3f} nm".format(dist_nm))
        console.print(table)
        log_activity("Calculated distance between {} and {}".format(p1, p2))
    except ValueError as e:
        console.print("[bold red][✘] Error: {}[/bold red]".format(e))

# ─── Settings ───
def settings_menu():
    global config
    cfg_table = Table(title="[bold blue]:gear: Settings[/bold blue]", border_style="blue", expand=True)
    cfg_table.add_column("Setting", style="bold cyan")
    cfg_table.add_column("Value", style="white")
    cfg_table.add_row("Auto Backup", str(config.get("auto_backup", True)))
    cfg_table.add_row("Auto Export", str(config.get("auto_export", False)))
    cfg_table.add_row("Default Export Format", config.get("default_export_format", "json"))
    cfg_table.add_row("Map Provider", config.get("map_provider", "google"))
    cfg_table.add_row("API Delay (seconds)", str(config.get("api_delay", 1.0)))
    cfg_table.add_row("Fetch Address", str(config.get("fetch_address", True)))
    cfg_table.add_row("Fetch Weather", str(config.get("fetch_weather", True)))
    console.print(cfg_table)

    if Confirm.ask("[bold cyan]Change settings?[/bold cyan]", default=False):
        config["auto_backup"] = Confirm.ask(
            "[bold cyan]Auto Backup before removing metadata?[/bold cyan]",
            default=config.get("auto_backup", True),
        )
        config["auto_export"] = Confirm.ask(
            "[bold cyan]Auto Export after extraction?[/bold cyan]",
            default=config.get("auto_export", False),
        )
        config["default_export_format"] = Prompt.ask(
            "[bold cyan]Default export format?[/bold cyan]",
            choices=["json", "txt"],
            default=config.get("default_export_format", "json"),
        )
        config["map_provider"] = Prompt.ask(
            "[bold cyan]Map provider?[/bold cyan]",
            choices=["google", "osm"],
            default=config.get("map_provider", "google"),
        )
        try:
            delay = float(
                Prompt.ask(
                    "[bold cyan]API delay between requests (seconds, min 1.0)?[/bold cyan]",
                    default=str(config.get("api_delay", 1.0)),
                )
            )
            config["api_delay"] = max(1.0, delay)
        except ValueError:
            console.print("[yellow][!] Invalid number, keeping default.[/yellow]")
        config["fetch_address"] = Confirm.ask(
            "[bold cyan]Fetch address from Nominatim?[/bold cyan]",
            default=config.get("fetch_address", True),
        )
        config["fetch_weather"] = Confirm.ask(
            "[bold cyan]Fetch weather from Open-Meteo?[/bold cyan]",
            default=config.get("fetch_weather", True),
        )
        save_config(config)
        console.print("[bold green][✓] Settings saved.[/bold green]")

# ─── Logs ───
def show_logs():
    if not LOG_FILE.exists():
        console.print("[bold yellow][!] No logs yet.[/bold yellow]")
        return
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        console.print("[bold red][!] Could not read logs: {}[/bold red]".format(e))
        return
    if not lines:
        console.print("[bold yellow][!] Log file is empty.[/bold yellow]")
        return
    log_table = Table(
        title="[bold blue]:clipboard: Activity Log (Last 20)[/bold blue]",
        border_style="blue",
        expand=True,
    )
    log_table.add_column("Entry", style="white", overflow="fold")
    for line in lines[-20:]:
        log_table.add_row(line.strip())
    console.print(log_table)

# ─── Help ───
def show_help():
    help_md = """
# MetaGhost X GeoTracker v6.1 - Help

## Features
- **Extract Metadata**: Read EXIF data from images including GPS coordinates.
- **Remove Metadata**: Strip all metadata. Auto-backup is enabled by default.
- **GPS Converter**: Convert DMS (Degrees, Minutes, Seconds) to Decimal.
- **Batch Processing**: Process entire folders of images at once.
- **Distance Calculator**: Calculate distance between two GPS coordinates.
- **Reverse Geocoding**: Get human-readable addresses from coordinates.
- **Weather Info**: Current weather at GPS location (via Open-Meteo).
- **Export**: Save results as JSON or TXT.

## GPS Input Formats Supported
- Decimal: `23.8103, 90.4125`
- DMS: `23° 48' 37.08" N, 90° 24' 45.00" E`
- Simple: `23 48 37 N, 90 24 45 E`

## Requirements
- Python 3.7+
- ExifTool (`pkg install exiftool` on Termux)
- Internet connection for geocoding and weather

## Important Notes
- **Nominatim Rate Limit**: API calls are delayed by at least 1 second
  to comply with OpenStreetMap's usage policy.
- **Auto Backup**: Before removing metadata, a backup is created in
  `~/.metaghost/backups/`.
- **No Silent Install**: Missing packages are reported, not auto-installed.
- **No Auto Browser Open**: Social links are available in the About menu.

## Tips
- Always backup important files before removing metadata.
- Use batch mode for large folders.
- Export results to keep a record of your analysis.
- Adjust API delay in Settings if you have a slow connection.
"""
    console.print(Markdown(help_md))

# ─── About ───
def show_about():
    about_md = """
# About MetaGhost X GeoTracker

**Version:** 6.1 (Security & Stability Fix)
**Developer:** Md Forhad
**GitHub:** Forhadj
**Telegram:** @f_forhad

## What's New in v6.1
- Removed auto browser open on startup
- Removed silent pip install (security fix)
- Added proper UTF-8 encoding declarations
- Added Nominatim API rate limiting (configurable delay)
- Improved exception handling with specific error types
- Added timeout to all subprocess and network calls
- Added About menu for social links
- Better error messages for missing ExifTool
"""
    console.print(Markdown(about_md))
    if Confirm.ask("[bold cyan]Open GitHub profile?[/bold cyan]", default=False):
        try:
            subprocess.run(
                ["termux-open-url", GITHUB_URL],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            webbrowser.open(GITHUB_URL)

# ─── Main ───
def main():
    while True:
        os.system("clear" if os.name == "posix" else "cls")
        print_banner()

        menu = Panel(
            "[bold green][1][/bold green] Extract Metadata & Location\n"
            "[bold yellow][2][/bold yellow] Remove Metadata (with Auto-Backup)\n"
            "[bold magenta][3][/bold magenta] GPS Converter (DMS <-> Decimal + Map Link)\n"
            "[bold blue][4][/bold blue] Batch Process Folder\n"
            "[bold cyan][5][/bold cyan] Distance Calculator\n"
            "[bold white][6][/bold white] Settings\n"
            "[bold white][7][/bold white] Activity Logs\n"
            "[bold green][8][/bold green] Help / Guide\n"
            "[bold magenta][9][/bold magenta] About / Social Links\n"
            "[bold red][0][/bold red] Exit",
            title="[bold white]Select Option[/bold white]",
            border_style="green",
            padding=(1, 2),
        )
        console.print(menu)

        choice = Prompt.ask(
            "[bold cyan]>> [/bold cyan]",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            default="1",
        )

        if choice == "1":
            path = Prompt.ask(
                "[bold cyan][>] Enter path to image file[/bold cyan]"
            ).strip()
            extract_metadata(path)
        elif choice == "2":
            path = Prompt.ask(
                "[bold cyan][>] Enter path to image file[/bold cyan]"
            ).strip()
            remove_metadata(path)
        elif choice == "3":
            gps_converter_menu()
        elif choice == "4":
            batch_process()
        elif choice == "5":
            distance_calculator()
        elif choice == "6":
            settings_menu()
        elif choice == "7":
            show_logs()
        elif choice == "8":
            show_help()
        elif choice == "9":
            show_about()
        elif choice == "0":
            console.print(
                "[bold red]\n[✘] Exiting... Goodbye! :wave:\n[/bold red]"
            )
            break

        Prompt.ask("\n[bold dim][Press Enter to continue...][/bold dim]")


if __name__ == "__main__":
    main()
