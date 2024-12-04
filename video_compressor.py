import ffmpeg
import os

class VideoCompressor:
    def __init__(self):
        self.quality_presets = {
            'high': 23,
            'medium': 28,
            'low': 33
        }
    
    def get_video_size_mb(self, filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    
    def _do_compress(self, input_path, output_path, crf):
        try:
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(stream, output_path, vcodec='libx264', crf=crf, acodec='aac')
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            return True
        except ffmpeg.Error:
            return False
    
    def compress_video(self, input_path, output_path, quality='medium', target_size_mb=None):
        if target_size_mb:
            return self.compress_to_target_size(input_path, output_path, target_size_mb)
        
        crf = self.quality_presets[quality]
        return self._do_compress(input_path, output_path, crf)
    
    def compress_to_target_size(self, input_path, output_path, target_size_mb):
        for crf in range(23, 41, 3):
            if self._do_compress(input_path, output_path, crf):
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