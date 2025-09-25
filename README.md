# Exif GPS Metadata Extractor

This tool extracts **GPS coordinates** and metadata from images using `exiftool`, then converts them into decimal format and generates a **Google Maps link**.  
It also supports **auto-open in browser** on Windows/Linux/Termux.

---

## 📦 Installation

### 🔹 Termux (Android)
```bash
pkg update && pkg upgrade -y
pkg install python -y
pkg install python-pip -y
pkg install exiftool -y
pkg install termux-api -y
pip install colorama রেকুএস্তস
git clone https://github.com/Forhadj/Mata_data.git
cd Mata_data
python mata_data.py
```

### 🔹 Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip exiftool -y
pip3 install colorama requests
```

### 🔹 Windows
1. Install [Python](https://www.python.org/downloads/)
2. Download [ExifTool](https://exiftool.org/) and place `exiftool(-k).exe` in PATH
3. Install dependencies:
```powershell
pip install colorama requests
git clone https://github.com/Forhadj/Mata_data.git
cd Mata_data
python mata_data.py
```

---

## 🚀 Usage
Run the tool:
```bash
python main.py your_image.jpg
```

It will show:
- GPS Coordinates (Raw & Decimal)
- Google Maps Link
- Address (if internet available)
- Auto-open Google Maps in browser (if supported)

---

## ⚠️ Notes
- `exiftool` is required, otherwise GPS extraction won’t work.
- `requests` is required for reverse geocoding (Address).  
- On Termux, **Termux:API app** must be installed for `termux-open-url`.

---

## 👨‍💻 Author
Made by **Forhad**
