import ffmpeg
import os
import time
import re
import threading
from subprocess import Popen, PIPE

class VideoCompressor:
    def __init__(self):
        self.quality_presets = {
            'high': 23,
            'medium': 28,
            'low': 33
        }
        self.supported_formats = ['mp4', 'avi', 'mkv', 'mov', 'webm']
        self.progress = 0
        self.processing = False
        self.current_line = ""
        self.error_message = ""
        self.resolution_presets = {
            '4K': '3840x2160',
            '1440p': '2560x1440',
            '1080p': '1920x1080',
            '720p': '1280x720',
            '480p': '854x480',
            '360p': '640x360'
        }
    
    def get_video_size_mb(self, filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    
    def _do_compress(self, input_path, output_path, crf, output_format='mp4', resolution=None):
        try:
            probe = ffmpeg.probe(input_path)
            duration = float(probe['format']['duration'])
            
            self.progress = 0
            self.processing = True

            stream = ffmpeg.input(input_path)
            if resolution:
                width, height = map(int, resolution.split('x'))
                stream = stream.filter('scale', width, height)
                
            stream = (stream
                .output(output_path, 
                       vcodec='libx264' if output_format != 'webm' else 'libvpx-vp9',
                       crf=crf, 
                       acodec='aac' if output_format != 'webm' else 'libvorbis')
                .overwrite_output())
                
            cmd = stream.compile()

            process = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)

            def read_output():
                while process.poll() is None:
                    line = process.stderr.readline()
                    if line:
                        self.current_line = line.strip()
                        time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})\.", line)
                        if time_match:
                            hours, minutes, seconds = map(int, time_match.groups())
                            current_time = hours * 3600 + minutes * 60 + seconds
                            self.progress = min(99, int(current_time / float(duration) * 100))
                            
            thread = threading.Thread(target=read_output)
            thread.daemon = True
            thread.start()

            process.wait()
            
            if process.returncode == 0:
                self.progress = 100
                self.processing = False
                return True
            else:
                self.processing = False
                return False

        except (ffmpeg.Error, ValueError) as e:
            self.processing = False
            return False
    
    def compress_video(self, input_path, output_path, quality='medium', target_size_mb=None, output_format='mp4', resolution_preset=None):
        if resolution_preset and resolution_preset not in self.resolution_presets:
            self.error_message = "Invalid resolution preset"
            return False
            
        resolution = self.resolution_presets.get(resolution_preset) if resolution_preset else None
        
        if not os.path.exists(input_path):
            self.error_message = "Input file does not exist"
            return False
            
        if quality not in self.quality_presets and target_size_mb is None:
            self.error_message = "Invalid quality preset"
            return False
            
        if target_size_mb is not None and target_size_mb <= 0:
            self.error_message = "Invalid target size"
            return False
            
        if output_format not in self.supported_formats:
            self.error_message = "Unsupported output format"
            return False
            
        try:
            if target_size_mb is not None:
                return self.compress_to_target_size(input_path, output_path, target_size_mb, output_format, resolution)
            else:
                crf = self.quality_presets[quality]
                return self._do_compress(input_path, output_path, crf, output_format, resolution)
        except Exception as e:
            self.error_message = str(e)
            return False
    
    def compress_to_target_size(self, input_path, output_path, target_size_mb, output_format='mp4', resolution=None):
        for crf in range(23, 41, 3):
            if self._do_compress(input_path, output_path, crf, output_format, resolution):
                compressed_size = self.get_video_size_mb(output_path)
                if compressed_size <= target_size_mb:
                    return True
                os.remove(output_path)
        return False

    def get_video_metadata(self, filepath):
        try:
            probe = ffmpeg.probe(filepath)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            return {
                'duration': float(probe['format'].get('duration', 0)),
                'size_mb': self.get_video_size_mb(filepath),
                'width': int(video_info.get('width', 0)),
                'height': int(video_info.get('height', 0)),
                'codec': video_info.get('codec_name', 'unknown'),
                'bitrate': float(probe['format'].get('bit_rate', 0)) / 1000000  # Convert to Mbps
            }
        except (ffmpeg.Error, KeyError, StopIteration):
            return None

    def get_progress(self):
        return {
            'progress': self.progress,
            'processing': self.processing,
            'current_line': self.current_line,
            'error': self.error_message
        }