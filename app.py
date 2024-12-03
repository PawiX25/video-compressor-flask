from flask import Flask, render_template, request, send_file
import os
from video_compressor import VideoCompressor

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'compressed'

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'video' not in request.files:
            return 'No video file uploaded', 400
        
        video = request.files['video']
        if video.filename == '':
            return 'No selected file', 400

        # Save uploaded file
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
        video.save(input_path)
        
        # Compress video
        compressor = VideoCompressor()
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f'compressed_{video.filename}')
        
        compression_mode = request.form.get('mode', 'quality')
        if compression_mode == 'size':
            target_size_mb = float(request.form['target_size'])
            result = compressor.compress_video(input_path, output_path, target_size_mb=target_size_mb)
        else:
            quality = request.form.get('quality', 'medium')
            result = compressor.compress_video(input_path, output_path, quality=quality)
        
        # Clean up input file
        os.remove(input_path)
        
        if result:
            return send_file(output_path, as_attachment=True)
        return 'Compression failed', 400
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)