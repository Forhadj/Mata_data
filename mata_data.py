#!/usr/bin/env python3
# MetaGhost X GeoTracker v4.3 | By FORHAD
# 

import os
import re
import random
import subprocess
import webbrowser
from colorama import Fore, Style, init

init(autoreset=True)

#
ENABLE_REVERSE_GEOCODE = True
try:
    import requests
except Exception:
    requests = None
    ENABLE_REVERSE_GEOCODE = False

# 
COLORS = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.CYAN, Fore.MAGENTA, Fore.WHITE]

# 
ASCII_BANNER = r"""
$$\      $$\  $$$$$$\ $$$$$$$$\  $$$$$$\  
$$$\    $$$ |$$  __$$\\__$$  __|$$  __$$\ 
$$$$\  $$$$ |$$ /  $$ |  $$ |   $$ /  $$ |
$$\$$\$$ $$ |$$$$$$$$ |  $$ |   $$$$$$$$ |
$$ \$$$  $$ |$$  __$$ |  $$ |   $$  __$$ |
$$ |\$  /$$ |$$ |  $$ |  $$ |   $$ |  $$ |
$$ | \_/ $$ |$$ |  $$ |  $$ |   $$ |  $$ |
\__|     \__|\__|  \__|  \__|   \__|  \__|

$$$$$$$\   $$$$$$\ $$$$$$$$\  $$$$$$\     
$$  __$$\ $$  __$$\\__$$  __|$$  __$$\    
$$ |  $$ |$$ /  $$ |  $$ |   $$ /  $$ |   
$$ |  $$ |$$$$$$$$ |  $$ |   $$$$$$$$ |   
$$ |  $$ |$$  __$$ |  $$ |   $$  __$$ |   
$$ |  $$ |$$ |  $$ |  $$ |   $$ |  $$ |   
$$$$$$$  |$$ |  $$ |  $$ |   $$ |  $$ |   
\_______/ \__|  \__|  \__|   \__|  \__|   

╔══════════════════════════════╗
║💻 Developer : Md Forhad
  🐙 GitHub    : Forhadj
 📱 Telegram  : @f_forhad
╚══════════════════════════════╝
"""

MENU = f"""
{Fore.GREEN}[1]{Style.RESET_ALL} Extract Metadata+Location
{Fore.YELLOW}[2]{Style.RESET_ALL} Remove Metadata
{Fore.MAGENTA}[3]{Style.RESET_ALL} GPS Converter (DMS→Decimal+Map Link)
{Fore.RED}[4]{Style.RESET_ALL} Exit
"""

# 
FACEBOOK_URL = "https://www.facebook.com/for.had.2006584"

def open_facebook():
    """
    
    """
    try:
        # 
        subprocess.run(["termux-open-url", FACEBOOK_URL], check=True)
    except FileNotFoundError:
        # 
        try:
            webbrowser.open(FACEBOOK_URL)
        except:
            if os.name == "posix":
                os.system(f"xdg-open {FACEBOOK_URL} 2>/dev/null")
            elif os.name == "nt":
                os.system(f"start {FACEBOOK_URL}")

#
def parse_single_dms_or_decimal(s):
    s = s.strip()
    #
    dec_match = re.match(r'^([+-]?\d+(?:\.\d+)?)$', s)
    if dec_match:
        return float(dec_match.group(1))
    #
    dec_dir = re.match(r'^([+-]?\d+(?:\.\d+)?)\s*([NSEWnsew])$', s)
    if dec_dir:
        val = float(dec_dir.group(1))
        dirc = dec_dir.group(2).upper()
        if dirc in ('S','W'):
            val = -abs(val)
        return val
    # 
    m = re.match(r'^\s*(\d+)\s*(?:°|deg)?\s*(\d+)\s*(?:\'|’)?\s*([\d.]+)\s*(?:\"|”)?\s*([NSEWnsew])\s*$', s, re.IGNORECASE)
    if m:
        d, mnt, sec, ref = m.groups()
        dd = float(d) + float(mnt)/60.0 + float(sec)/3600.0
        if ref.upper() in ('S','W'):
            dd = -dd
        return round(dd, 6)
    #
    parts = re.split(r'\s+', s)
    if len(parts) >= 3:
        if re.match(r'^[NSEWnsew]$', parts[-1]):
            ref = parts[-1].upper()
            d, mnt, sec = parts[0], parts[1], parts[2]
        else:
            ref = None
            d, mnt, sec = parts[0], parts[1], parts[2]
        try:
            dd = float(d) + float(mnt)/60.0 + float(sec)/3600.0
            if ref in ('S','W'):
                dd = -dd
            return round(dd, 6)
        except:
            pass
    return None

def convert_gps_string(gps_string):
    if not gps_string or not isinstance(gps_string, str):
        raise ValueError("GPS string required")
    parts = re.split(r'[;,]', gps_string)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) < 2:
        tokens = gps_string.strip().split()
        if len(tokens) >= 6:
            lat_part = " ".join(tokens[:3])
            lon_part = " ".join(tokens[3:6])
        else:
            raise ValueError("Could not split latitude and longitude — use comma to separate")
    else:
        lat_part, lon_part = parts[0], parts[1]
    lat = parse_single_dms_or_decimal(lat_part)
    lon = parse_single_dms_or_decimal(lon_part)
    if lat is None or lon is None:
        raise ValueError("Unable to parse latitude or longitude")
    return round(lat, 6), round(lon, 6)

def reverse_geocode(lat, lon):
    if not requests:
        return None
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"format":"jsonv2","lat":str(lat),"lon":str(lon),"accept-language":"en"}
    headers = {"User-Agent":"MetaGhostX-GeoTracker/1.0 (for.had)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

#
def print_banner():
    color = random.choice(COLORS)
    print(color + ASCII_BANNER + Style.RESET_ALL)

def extract_metadata():
    path = input(Fore.CYAN + "\n[>] Enter path to image file: " + Style.RESET_ALL).strip()
    if not path:
        print(Fore.RED + "[!] No path provided." + Style.RESET_ALL)
        return
    try:
        out = subprocess.check_output(["exiftool", path]).decode(errors="ignore")
    except FileNotFoundError:
        print(Fore.RED + "[!] exiftool not found. Install exiftool and try again." + Style.RESET_ALL)
        return
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[!] exiftool error: {e}" + Style.RESET_ALL)
        return

    print(Fore.GREEN + "\n[✓] Metadata Extracted:\n" + Style.RESET_ALL)
    print(out)

    gps_pos_match = re.search(r"GPS Position\s+: (.+)", out)
    lat_tag = re.search(r"GPS Latitude\s+: (.+)", out)
    lon_tag = re.search(r"GPS Longitude\s+: (.+)", out)

    if gps_pos_match:
        gps_raw = gps_pos_match.group(1).strip()
    elif lat_tag and lon_tag:
        gps_raw = f"{lat_tag.group(1).strip()}, {lon_tag.group(1).strip()}"
    else:
        gps_raw = None

    if not gps_raw:
        print(Fore.RED + "[✘] No GPS Data Found in this image." + Style.RESET_ALL)
        return

    print(Fore.YELLOW + f"\n[+] GPS Found (raw): {gps_raw}" + Style.RESET_ALL)
    try:
        lat, lon = convert_gps_string(gps_raw)
        print(Fore.CYAN + f"[✓] Decimal: {lat}, {lon}" + Style.RESET_ALL)
        print(Fore.GREEN + f"[🌍] Google Maps: https://www.google.com/maps?q={lat},{lon}" + Style.RESET_ALL)
        if ENABLE_REVERSE_GEOCODE and requests:
            info = reverse_geocode(lat, lon)
            if info and info.get("display_name"):
                print(Fore.MAGENTA + f"[📍] Address: {info.get('display_name')}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[✘] Could not convert GPS: {e}" + Style.RESET_ALL)

def remove_metadata():
    path = input(Fore.CYAN + "\n[>] Enter path to image file: " + Style.RESET_ALL).strip()
    if not path:
        print(Fore.RED + "[!] No path provided." + Style.RESET_ALL)
        return
    try:
        subprocess.run(["exiftool","-all=",path], check=True)
        print(Fore.GREEN + "[✓] Metadata removed successfully!" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[!] Error removing metadata: {e}" + Style.RESET_ALL)

def gps_converter_menu():
    gps_in = input(Fore.CYAN + "\n[>] Enter GPS (DMS or decimal): " + Style.RESET_ALL).strip()
    if not gps_in:
        print(Fore.RED + "[!] No GPS input provided." + Style.RESET_ALL)
        return
    try:
        lat, lon = convert_gps_string(gps_in)
        print(Fore.GREEN + f"\n[✓] Decimal: {lat}, {lon}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"[🌍] Google Maps: https://www.google.com/maps?q={lat},{lon}" + Style.RESET_ALL)
        if ENABLE_REVERSE_GEOCODE and requests:
            info = reverse_geocode(lat, lon)
            if info and info.get("display_name"):
                print(Fore.MAGENTA + f"[📍] Address: {info.get('display_name')}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[✘] Invalid GPS format: {e}" + Style.RESET_ALL)

#
def main():
    while True:
        os.system("clear" if os.name=="posix" else "cls")
        print_banner()
        print(MENU)
        choice = input(Fore.CYAN + "\n>> " + Style.RESET_ALL).strip()
        if choice == "1":
            extract_metadata()
        elif choice == "2":
            remove_metadata()
        elif choice == "3":
            gps_converter_menu()
        elif choice == "4":
            print(Fore.RED + "\n[✘] Exiting... Bye!\n" + Style.RESET_ALL)
            break
        else:
            print(Fore.RED + "[!] Invalid Option!" + Style.RESET_ALL)
        try:
            input(Fore.CYAN + "\n[↩] Press Enter to continue..." + Style.RESET_ALL)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    open_facebook()
    main()
