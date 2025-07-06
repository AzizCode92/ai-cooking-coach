import os
import sys
import json
from src.analyzer import VideoAnalyzer
from src.visualizer import VideoVisualizer

def main(video_path):
    """
    Main function to orchestrate the video analysis and visualization process.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at '{video_path}'")
        sys.exit(1)

    # Define paths based on the input video name
    video_filename = os.path.basename(video_path)
    video_name, _ = os.path.splitext(video_filename)
    
    # Ensure output directories exist
    os.makedirs("analysis_results", exist_ok=True)
    os.makedirs("videos/output", exist_ok=True)
    
    json_output_path = os.path.join("analysis_results", f"{video_name}_analysis.json")
    video_output_path = os.path.join("videos/output", f"{video_name}_with_feedback.mp4")
    prompt_path = "prompts/cooking.txt"

    # --- Step 1: Analyze the Video (if analysis file doesn't exist) ---
    if not os.path.exists(json_output_path):
        print("Analysis file not found. Starting video analysis with Gemini...")
        analyzer = VideoAnalyzer(prompt_path=prompt_path)
        try:
            analysis_data = analyzer.analyze_video(video_path)
            with open(json_output_path, 'w') as f:
                json.dump(analysis_data, f, indent=4)
            print(f"Analysis complete. Results saved to '{json_output_path}'")
        except Exception as e:
            print(f"An error occurred during analysis: {e}")
            sys.exit(1)
    else:
        print(f"Found existing analysis file at '{json_output_path}'. Loading data.")
        with open(json_output_path, 'r') as f:
            analysis_data = json.load(f)

    # --- Step 2: Create the video with feedback ---
    print("Starting video visualization process...")
    visualizer = VideoVisualizer(video_path, analysis_data)
    visualizer.create_video_with_feedback(video_output_path)
    print(f"Process complete. Output video saved to '{video_output_path}'")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_video>")
        sys.exit(1)
    
    # The first command-line argument is the script name, the second is the video path
    input_video_path = sys.argv[1]
    main(input_video_path)
