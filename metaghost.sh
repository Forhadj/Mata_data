#!/bin/bash
# Banner Function
banner() {
    clear
    echo -e "\e[1;92m"
    echo "███    ███ ███████ ████████  █████   ██████  ██████   ██████  "
    echo "████  ████ ██         ██    ██   ██ ██    ██ ██   ██ ██    ██ "
    echo "██ ████ ██ █████      ██    ███████ ██    ██ ██████  ██    ██ "
    echo "██  ██  ██ ██         ██    ██   ██ ██    ██ ██   ██ ██    ██ "
    echo "██      ██ ███████    ██    ██   ██  ██████  ██   ██  ██████  "
    echo -e "\e[0m"
    echo -e "\e[1;93m[~] MetaGhost X GeoTracker v4.0 | By FORHAD\e[0m"
    echo
}

menu() {
    echo -e "\e[1;96mChoose an option:\e[0m"
    echo "  [1] Extract Metadata + Location Info"
    echo "  [2] Remove Metadata"
    echo "  [3] Exit"
    echo -n -e "\n>> "
    read choice
    case $choice in
        1) extract_metadata ;;
        2) remove_metadata ;;
        3) echo -e "\e[1;91m[!] Exiting... Stay anonymous!\e[0m"; exit 0 ;;
        *) echo -e "\e[1;91m[!] Invalid choice. Try again.\e[0m"; sleep 1; clear; banner; menu ;;
    esac
}

check_dependencies() {
    if ! command -v exiftool &> /dev/null; then
        echo "[!] Installing exiftool..."
        pkg update -y && pkg install exiftool -y
    fi
    if ! command -v python &> /dev/null; then
        echo "[!] Installing Python..."
        pkg install python -y
    fi
    pip show folium geocoder pytz &> /dev/null || pip install folium geocoder pytz
}

extract_metadata() {
    echo -e "\n\e[1;94m[>] Enter path to image file:\e[0m"
    read image

    if [ ! -f "$image" ]; then
        echo -e "\e[1;91m[!] File not found!\e[0m"
        return
    fi

    mkdir -p reports
    filename=$(basename "$image")
    output="reports/metadata_${filename}.txt"

    echo -e "\e[1;92m[✔] Extracting metadata from: $filename\e[0m"
    exiftool "$image" > "$output"
    cat "$output"
    echo -e "\n\e[1;96m[✔] Metadata saved to: $output\e[0m"

    lat=$(exiftool -GPSLatitude -n "$image" | awk -F': ' '{print $2}')
    lon=$(exiftool -GPSLongitude -n "$image" | awk -F': ' '{print $2}')

    if [ -n "$lat" ] && [ -n "$lon" ]; then
        echo -e "\n\e[1;94m[>] GPS found! Showing location info...\e[0m"
        python <<EOF
import folium, geocoder, pytz
from datetime import datetime
lat, lon = $lat, $lon
g = geocoder.osm([lat, lon], method='reverse')
if not g.ok:
    print("\n❌ Location not found!")
else:
    address = g.address
    city = g.city
    state = g.state
    country = g.country
    timezone = g.timezone
    now_time = None
    if timezone:
        tz = pytz.timezone(timezone)
        now_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    map_obj = folium.Map(location=[lat, lon], zoom_start=13)
    folium.Marker([lat, lon], popup="Target Location 📍").add_to(map_obj)
    map_obj.save("location_map.html")
    print(f"\n✅ Location Info Found:\n")
    print(f"🌍 Latitude: {lat}")
    print(f"🌍 Longitude: {lon}")
    print(f"🏠 Address: {address}")
    print(f"🏙 City: {city}")
    print(f"🌆 State: {state}")
    print(f"🌎 Country: {country}")
    if timezone:
        print(f"🕒 Timezone: {timezone}")
        print(f"⏰ Local Time: {now_time}")
    print("\n🗺 Map File Saved: location_map.html\n")
EOF
    else
        echo -e "\n⚠️  GPS metadata not found in this image."
    fi
}

remove_metadata() {
    echo -e "\n\e[1;94m[>] Enter path to image file:\e[0m"
    read image

    if [ ! -f "$image" ]; then
        echo -e "\e[1;91m[!] File not found!\e[0m"
        return
    fi

    mkdir -p clean_images
    filename=$(basename "$image")
    output="clean_images/cleaned_${filename}"

    echo -e "\e[1;93m[!] Removing metadata...\e[0m"
    exiftool -all= -o "$output" "$image"
    echo -e "\e[1;92m[✔] Clean image saved as: $output\e[0m"
}

clear
banner
check_dependencies
while true; do
    menu
done
