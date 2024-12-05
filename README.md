# Video Compressor Flask

A Flask web application that allows users to compress videos while maintaining quality. The application supports various output formats and resolutions, providing options for both quality-based and size-based compression.

## Features

- **Upload Videos**: Supports formats like `mp4`, `avi`, `mov`, `mkv`, `flv`, `wmv`.
- **Compression Modes**:
  - **Quality-based Compression**: Choose from `high`, `medium`, or `low` quality settings.
  - **Size-based Compression**: Specify a target file size in MB.
- **Resolution Options**: Select from presets like `4K`, `1440p`, `1080p`, `720p`, `480p`, `360p`, or keep the original resolution.
- **Output Formats**: Convert videos to `mp4`, `avi`, `mkv`, `mov`, or `webm`.
- **Real-time Progress**: Monitor compression progress with a progress bar and FFmpeg output.
- **Preview and Download**: View original and compressed videos side by side and download the compressed version.

## Prerequisites

- **Python 3.x**
- **FFmpeg** installed and added to your system's PATH.
- **pip** package manager.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/PawiX25/video-compressor-flask.git
   cd video-compressor-flask
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` includes:

   - `flask`
   - `ffmpeg-python`
   - `werkzeug`

3. **Set Up Directories**

   Ensure the `uploads` and `compressed` directories exist:

   ```bash
   mkdir -p uploads compressed
   ```

## Usage

1. **Run the Application**

   ```bash
   python app.py
   ```

   The application will start in debug mode by default and run on `http://localhost:5000`.

2. **Access the Web Interface**

   Open your web browser and navigate to `http://localhost:5000`.

3. **Compress a Video**

   - **Upload**: Drag and drop a video file into the designated area or click to select a file.
   - **Configure**: Choose the output format, resolution, and compression mode (quality-based or size-based).
   - **Compress**: Click the "Compress Video" button to start the compression process.
   - **Monitor**: Watch the progress bar and FFmpeg output for real-time updates.
   - **Preview & Download**: Once completed, preview the original and compressed videos and download the compressed file.

## Configuration

- **Maximum Upload Size**: Set to 1 GB by default. Adjust `app.config['MAX_CONTENT_LENGTH']` in `app.py` if needed.
- **File Cleanup**: Files older than 1 hour (3600 seconds) are automatically deleted. Modify `app.config['MAX_FILE_AGE']` to change this behavior.

## Dependencies

- **Flask**: Web framework for Python.
- **FFmpeg**: Tool for handling multimedia data. Download from [FFmpeg Official Site](https://ffmpeg.org/download.html).
- **ffmpeg-python**: Python bindings for FFmpeg.
- **Werkzeug**: WSGI utility library.

## Notes

- Ensure FFmpeg is installed and accessible from the command line.
- Supported video formats for upload are defined in `ALLOWED_EXTENSIONS` in `app.py`.
- The application uses Tailwind CSS for styling, loaded via CDN in the HTML template.
