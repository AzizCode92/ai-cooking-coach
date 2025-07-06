import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

class VideoAnalyzer:
    """
    Handles the interaction with the Gemini API to analyze a video.
    """
    def __init__(self, prompt_path="prompts/cooking.txt"):
        # Load environment variables from .env file
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        
        try:
            with open(prompt_path, 'r') as f:
                self.prompt = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found at {prompt_path}")

    def analyze_video(self, video_path):
        """
        Uploads a video, sends it for analysis, and returns the structured JSON response.
        """
        print(f"Uploading '{video_path}' to Gemini... This may take a moment.")
        video_file = genai.upload_file(path=video_path)

        # Wait for the upload to complete
        while video_file.state.name == "PROCESSING":
            print('.', end='', flush=True)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise ValueError(f"Video upload failed: {video_file.state.name}")

        print(f"\nVideo uploaded successfully. Sending to model for analysis...")
        
        # Send the prompt and the video file to the model
        response = self.model.generate_content([self.prompt, video_file], request_options={"timeout": 600})
        
        # Clean up the uploaded file on the server
        genai.delete_file(video_file.name)
        print("Analysis complete. Server file cleaned up.")

        # Clean and parse the JSON response
        response_text = response.text
        if "```json" in response_text:
            response_text = response_text.split("```json\n")[1].split("\n```")[0]
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to decode JSON from Gemini's response:\n{response.text}")
