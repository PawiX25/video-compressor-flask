from flask import Flask, render_template, request, send_file, jsonify
import os
from video_compressor import VideoCompressor
from werkzeug.utils import secure_filename
import mimetypes

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'compressed'

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

compressor = VideoCompressor()

@app.route('/progress')
def progress():
    return jsonify(compressor.get_progress())

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(
        os.path.join(app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True
    )

@app.route('/', methods=['GET', 'POST'])
def index():
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
            
            if compression_mode == 'size':
                try:
                    target_size_mb = float(request.form['target_size'])
                    if target_size_mb <= 0:
                        raise ValueError()
                except (ValueError, KeyError):
                    return render_template('index.html', error='Invalid target size')
                    
                result = compressor.compress_video(input_path, output_path, 
                                                target_size_mb=target_size_mb,
                                                output_format=output_format)
            else:
                quality = request.form.get('quality', 'medium')
                result = compressor.compress_video(input_path, output_path, 
                                                quality=quality,
                                                output_format=output_format)
            
            if result:
                compressed_metadata = compressor.get_video_metadata(output_path)
                return render_template('index.html',
                                    original_metadata=metadata,
                                    compressed_metadata=compressed_metadata,
                                    download_filename=f'compressed_{filename_without_ext}.{output_format}')
            
            return render_template('index.html', error='Compression failed')
            
        except Exception as e:
            return render_template('index.html', error=str(e))
        finally:
            # Cleanup input file
            if os.path.exists(input_path):
                os.remove(input_path)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)