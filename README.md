# MetaGhost X GeoTracker v4.0

A Termux tool to extract/remove image metadata and auto-detect GPS location.

## Installation
pkg update -y
pkg install git python exiftool -y
git clone https://github.com/Forhadj/MetaGhost-X.git
cd MetaGhost-X
pip install -r requirements.txt
bash metaghost.sh

## Usage
- [1] Extract Metadata + Location Info
- [2] Remove Metadata
- [3] Exit

Location map saved as `location_map.html`
