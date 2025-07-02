# Speech Recognition Desktop Application – Windows

This application allows you to convert speech to text and automatically paste it anywhere on Windows.

## Prerequisites
- **Python 3.8 or newer**
  - Download from [python.org](https://www.python.org/downloads/)
  - During installation, check "Add Python to PATH"

## Visual C++ Build Tools (PyAudio-hoz)
1. Download Visual Studio Build Tools from [Microsoft](https://visualstudio.microsoft.com/downloads/)
2. During installation, select the "C++ build tools" component

## Installation & Startup
1. Download or clone this project.
2. Double-click the `start service.bat` file in the project folder.
   - This will install all required Python packages and start the application automatically.

## Usage
- Press the `Ctrl + Win` key combination and speak into your microphone.
- Release the keys to finish.
- The recognized text will be automatically pasted where your cursor is.

## Troubleshooting
- **Python not found:**
  - Make sure Python is installed and added to your PATH.
- **Microphone not working:**
  - Check Windows microphone settings (Settings > System > Sound > Input).
  - Make sure microphone access is enabled for desktop apps.
- **Other issues:**
  - Check the on-screen messages or logs.
  - Restart your computer if problems persist.

## Support
If you have issues:
1. Check the on-screen messages for errors.
2. Ensure all prerequisites are met.
3. Restart your computer.
4. If problems persist, contact the developer or open an issue. (support@futdevpro.hu)

---

*No Node.js, FFmpeg, or Visual C++ installation is required. Just Python and a double-click!* 