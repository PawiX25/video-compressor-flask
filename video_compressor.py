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
        self.bitrate_presets = {
            '4K': '45M',
            '1440p': '25M',
            '1080p': '8M',
            '720p': '5M',
            '480p': '2.5M',
            '360p': '1M'
        }
        self.audio_presets = {
            'high': {'codec': 'aac', 'bitrate': '192k'},
            'medium': {'codec': 'aac', 'bitrate': '128k'},
            'low': {'codec': 'aac', 'bitrate': '96k'}
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
        self.process = None
        self.cancelled = False
        self.encoding_speed = 0
        self.estimated_time = 0
        self.start_time = 0
    
    def get_video_size_mb(self, filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    
    def cancel_compression(self):
        self.cancelled = True
        if self.process:
            try:
                self.process.stderr.close()
                self.process.stdout.close()
                self.process.terminate()
            except:
                pass
        self.processing = False
        self.progress = 0
        self.current_line = ""
        self.error_message = "Compression cancelled"

    def estimate_compression_time(self, input_path, resolution=None, quality='medium'):
        try:
            probe = ffmpeg.probe(input_path)
            duration = float(probe['format']['duration'])
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            resolution_factor = 1.0
            if resolution:
                target_width = int(resolution.split('x')[0])
                source_width = int(video_info.get('width', 0))
                resolution_factor = (target_width / source_width) ** 2

            quality_factor = {
                'high': 1.5,
                'medium': 1.0,
                'low': 0.7
            }.get(quality, 1.0)

            base_processing_rate = 0.5 
            estimated_seconds = duration * base_processing_rate * resolution_factor * quality_factor
            
            return estimated_seconds
        except Exception:
            return 0

    def _do_compress(self, input_path, output_path, crf, output_format='mp4', resolution=None):
        self.cancelled = False
        self.start_time = time.time()
        self.estimated_time = self.estimate_compression_time(input_path, resolution)
        
        try:
            probe = ffmpeg.probe(input_path)
            duration = float(probe['format']['duration'])
            
            self.progress = 0
            self.processing = True

            stream = ffmpeg.input(input_path)
            if resolution:
                width, height = map(int, resolution.split('x'))
                stream = stream.filter('scale', width, height)

            bitrate = None
            for res, br in self.bitrate_presets.items():
                if resolution and resolution.startswith(res):
                    bitrate = br
                    break

            audio_preset = self.audio_presets['medium']
            
            output_args = {
                'vcodec': 'libx264' if output_format != 'webm' else 'libvpx-vp9',
                'crf': crf,
                'acodec': audio_preset['codec'],
                'audio_bitrate': audio_preset['bitrate']
            }

            if bitrate:
                output_args['video_bitrate'] = bitrate

            stream = (stream
                .output(output_path, **output_args)
                .overwrite_output())
                
            cmd = stream.compile()

            self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            process_ref = self.process

            def read_output():
                while process_ref and process_ref.poll() is None and not self.cancelled:
                    try:
                        line = process_ref.stderr.readline()
                        if line:
                            self.current_line = line.strip()
                            speed_match = re.search(r"speed=\s*([\d.]+)x", line)
                            if speed_match:
                                self.encoding_speed = float(speed_match.group(1))
                            
                            time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})\.", line)
                            if time_match:
                                hours, minutes, seconds = map(int, time_match.groups())
                                current_time = hours * 3600 + minutes * 60 + seconds
                                self.progress = min(99, int(current_time / float(duration) * 100))
                                
                                if self.progress > 0:
                                    elapsed_time = time.time() - self.start_time
                                    self.estimated_time = (elapsed_time / self.progress) * (100 - self.progress)
                    except:
                        break

            thread = threading.Thread(target=read_output)
            thread.daemon = True
            thread.start()

            self.process.wait()
            
            if self.cancelled:
                try:
                    if self.process:
                        self.process.stderr.close()
                        self.process.stdout.close()
                        self.process.wait()
                    if os.path.exists(output_path):
                        time.sleep(0.5)
                        os.remove(output_path)
                except:
                    pass
                self.error_message = "Compression cancelled"
                return False

            if self.process.returncode == 0:
                self.progress = 100
                self.processing = False
                return True
            else:
                self.processing = False
                return False

        except (ffmpeg.Error, ValueError) as e:
            self.processing = False
            return False
        finally:
            if self.process:
                try:
                    self.process.stderr.close()
                    self.process.stdout.close()
                except:
                    pass
            self.process = None
    
    def compress_video(self, input_path, output_path, quality='medium', target_size_mb=None, output_format='mp4', resolution_preset=None):
        self.error_message = ""
        
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
                success = self.compress_to_target_size(input_path, output_path, target_size_mb, output_format, resolution)
            else:
                crf = self.quality_presets[quality]
                success = self._do_compress(input_path, output_path, crf, output_format, resolution)
            
            if not success and not self.error_message:
                self.error_message = "Compression failed"
            return success
                
        except Exception as e:
            self.error_message = str(e)
            return False
    
    def compress_to_target_size(self, input_path, output_path, target_size_mb, output_format='mp4', resolution=None):
        for crf in range(23, 41, 3):
            if self._do_compress(input_path, output_path, crf, output_format, resolution):
                compressed_size = self.get_video_size_mb(output_path)
                if compressed_size <= target_size_mb:
                    return True
                time.sleep(0.5)
                try:
                    os.remove(output_path)
                except:
                    pass
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
        base_info = {
            'progress': self.progress,
            'processing': self.processing,
            'current_line': self.current_line,
            'error': self.error_message,
            'encoding_speed': self.encoding_speed,
            'estimated_time': self.estimated_time,
            'elapsed_time': time.time() - self.start_time if self.start_time else 0
        }
        return base_info