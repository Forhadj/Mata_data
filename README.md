# Meta Data Tool v1.0

A Termux tool to extract/remove image metadata and detect GPS location.

## GitHub Repository
[https://github.com/Forhadj/Mata_data](https://github.com/Forhadj/Mata_data)

## Installation
pkg update -y
pkg install git python exiftool -y
git clone https://github.com/Forhadj/Mata_data.git
cd Mata_data
pip install -r requirements.txt
bash metaghost.sh

## Usage
- [1] Extract Metadata + Location Info: Extract all metadata and generate a map if GPS exists.
- [2] Remove Metadata: Remove all metadata from image, save in clean_images folder.
- [3] Exit: Exit safely.

Make sure Termux has storage permission:
termux-setup-storage
