import cv2
import time
import os
from moviepy import VideoFileClip

class VideoVisualizer:
    """
    Handles drawing feedback onto video frames and saving the output video with audio.
    """
    def __init__(self, video_path, analysis_data):
        self.video_path = video_path
        self.analysis_data = analysis_data
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.9 # Slightly smaller font for better wrapping
        self.font_color = (255, 255, 255) # White
        self.line_type = 2
        self.feedback_display_time = 5  # seconds

    def _time_str_to_seconds(self, time_str):
        """Converts a 'MM:SS' or 'MM:SS-MM:SS' string to total seconds."""
        try:
            if '-' in time_str:
                time_str = time_str.split('-')[0].strip()
            
            minutes, seconds = map(int, time_str.split(':'))
            return minutes * 60 + seconds
        except (ValueError, IndexError):
            print(f"Warning: Could not parse timestamp '{time_str}'. Skipping.")
            return -1

    def _draw_text(self, frame, text, position, color=(0, 0, 0)):
        """Draws wrapped text with a semi-transparent background."""
        frame_width = frame.shape[1]
        max_width = frame_width - position[0] - 20 # Max width for text line
        
        words = text.split(' ')
        lines = []
        current_line = ""
        
        # Logic to wrap text into multiple lines
        for word in words:
            test_line = f"{current_line} {word}".strip()
            (text_w, text_h), _ = cv2.getTextSize(test_line, self.font, self.font_scale, self.line_type)
            if text_w > max_width:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        lines.append(current_line)

        # Draw each line of text
        y = position[1]
        line_height = cv2.getTextSize("A", self.font, self.font_scale, self.line_type)[0][1] + 15
        
        for i, line in enumerate(lines):
            (text_w, text_h), _ = cv2.getTextSize(line, self.font, self.font_scale, self.line_type)
            x1, y1 = position[0] - 10, y - text_h - 10
            x2, y2 = position[0] + text_w + 10, y

            if x1 >= 0 and y1 >= 0 and x2 <= frame.shape[1] and y2 <= frame.shape[0]:
                sub_img = frame[y1:y2, x1:x2]
                overlay = sub_img.copy()
                cv2.rectangle(overlay, (0, 0), (sub_img.shape[1], sub_img.shape[0]), color, -1)
                alpha = 0.6
                cv2.addWeighted(overlay, alpha, sub_img, 1 - alpha, 0, sub_img)
            
            cv2.putText(frame, line, (position[0], y - 5), self.font, self.font_scale, self.font_color, self.line_type)
            y += line_height

    def create_video_with_feedback(self, output_path):
        """
        Reads the input video, overlays feedback, and saves it to a new file with audio.
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise IOError(f"Could not open video file at {self.video_path}")

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Temporary path for the silent video file
        temp_video_path = "temp_silent_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video_path, fourcc, fps, (frame_width, frame_height))

        events = {self._time_str_to_seconds(item['timestamp']): item for item in self.analysis_data.get('analysis', [])}
        title = self.analysis_data.get('summary', {}).get('title', 'Cooking Analysis')
        
        active_feedback = ""
        feedback_timer_end = 0

        print("Step 1/2: Generating video with text overlay...")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            current_time_seconds = int(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)

            if current_time_seconds in events:
                event = events[current_time_seconds]
                active_feedback = f"{event['action']}: {event['feedback']}"
                feedback_timer_end = time.time() + self.feedback_display_time
                if current_time_seconds in events:
                    del events[current_time_seconds]

            if active_feedback and time.time() < feedback_timer_end:
                self._draw_text(frame, active_feedback, (50, 70), color=(0, 100, 0))
            
            self._draw_text(frame, title, (50, frame_height - 50), color=(150, 0, 0))
            out.write(frame)

        cap.release()
        out.release()
        cv2.destroyAllWindows()
        print("Video with text overlay generated.")

        # Step 2: Combine the generated video with the original audio using moviepy
        print("Step 2/2: Adding original audio to the video...")
        try:
            original_clip = VideoFileClip(self.video_path)
            generated_clip = VideoFileClip(temp_video_path)

            final_clip = generated_clip.with_audio(original_clip.audio)
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            original_clip.close()
            generated_clip.close()
            final_clip.close()
            print(f"Successfully created video with audio at {output_path}")

        except Exception as e:
            print(f"An error occurred while adding audio: {e}")
            print("Please ensure you have FFMPEG installed on your system.")
        finally:
            # Clean up the temporary silent video file
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
