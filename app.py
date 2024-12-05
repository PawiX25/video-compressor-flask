from flask import Flask, render_template, request, send_file, jsonify
import os
from video_compressor import VideoCompressor
from werkzeug.utils import secure_filename
import mimetypes
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'compressed'
app.config['MAX_FILE_AGE'] = 3600

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    current_time = time.time()
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > app.config['MAX_FILE_AGE']:
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

compressor = VideoCompressor()

@app.route('/progress')
def progress():
    cleanup_old_files()
    return jsonify(compressor.get_progress())

@app.route('/download/<filename>')
def download_file(filename):
    cleanup_old_files()
    return send_file(
        os.path.join(app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True
    )

@app.route('/video/<filename>')
def get_video(filename):
    if os.path.exists(os.path.join(app.config['OUTPUT_FOLDER'], filename)):
        return send_file(
            os.path.join(app.config['OUTPUT_FOLDER'], filename),
            mimetype=mimetypes.guess_type(filename)[0]
        )
    elif os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return send_file(
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            mimetype=mimetypes.guess_type(filename)[0]
        )
    else:
        return "File not found", 404

@app.route('/', methods=['GET', 'POST'])
def index():
    cleanup_old_files()
    
    if request.method == 'POST':
        if 'video' not in request.files:
            return render_template('index.html', error='No video file uploaded')
        
        video = request.files['video']
        if video.filename == '':
            return render_template('index.html', error='No selected file')
            
        if not allowed_file(video.filename):
            return render_template('index.html', error='Invalid file type')

        # Secure the filename and handle output format
        base_filename = secure_filename(video.filename)
        output_format = request.form.get('output_format', 'mp4')
        filename_without_ext = os.path.splitext(base_filename)[0]
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], base_filename)
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], 
                                 f'compressed_{filename_without_ext}.{output_format}')
        
        try:
            video.save(input_path)
            metadata = compressor.get_video_metadata(input_path)
            
            if metadata is None:
                raise ValueError("Invalid video file")
                
            compression_mode = request.form.get('mode', 'quality')
            resolution_preset = request.form.get('resolution', '')
            
            if compression_mode == 'size':
                try:
                    target_size_mb = float(request.form['target_size'])
                    if target_size_mb <= 0:
                        raise ValueError()
                except (ValueError, KeyError):
                    return render_template('index.html', error='Invalid target size')
                    
                result = compressor.compress_video(input_path, output_path, 
                                                target_size_mb=target_size_mb,
                                                output_format=output_format,
                                                resolution_preset=resolution_preset)
            else:
                quality = request.form.get('quality', 'medium')
                result = compressor.compress_video(input_path, output_path, 
                                                quality=quality,
                                                output_format=output_format,
                                                resolution_preset=resolution_preset)
            
            if result:
                compressed_metadata = compressor.get_video_metadata(output_path)
                return render_template('index.html',
                                    original_metadata=metadata,
                                    compressed_metadata=compressed_metadata,
                                    input_filename=base_filename,
                                    download_filename=f'compressed_{filename_without_ext}.{output_format}')
            
            return render_template('index.html', error='Compression failed')
            
        except Exception as e:
            # Clean up input file only on error
            if os.path.exists(input_path):
                os.remove(input_path)
            return render_template('index.html', error=str(e))
    
    return render_template('index.html')

def cleanup_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)