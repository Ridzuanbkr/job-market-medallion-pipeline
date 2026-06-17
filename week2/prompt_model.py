import os
import sys
import requests
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

# Load environment variables from the local .env file
load_dotenv()

def prompt_model(model: str, prompt: str) -> str:
    """
    Prompts either a Google Gemini cloud model or a local Ollama model 
    based on the input string, catching errors and formatting them explicitly.
    """
    model_lower = model.lower()
    
    try:
        # --- ROUTE 1: GOOGLE AI STUDIO (Cloud Gemini Models) ---
        if "gemini" in model_lower:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return "[Gemini Error] GEMINI_API_KEY is missing from your .env configuration file."
            
            # Initialize the modern SDK client
            client = genai.Client(api_key=api_key)
            
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text if response.text else "Error: Model returned an empty string response."

        # --- ROUTE 2: LOCAL OLLAMA SERVER (Ollama Models) ---
        elif any(m in model_lower for m in ["llama", "phi", "deepseek", "mistral"]):
            url = "http://127.0.0.1:11434/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json().get("response", "Error: No text found in Ollama output.")

        # --- FALLBACK: INVALID/UNSUPPORTED SELECTION ---
        else:
            return f"Error: Unsupported model identifier string: '{model}'"

    except APIError as e:
        # Explicit Error Formatting requested by assignment manual
        return f"[Gemini Error] {e.code if hasattr(e, 'code') else 'API_ERROR'}. {e.message if hasattr(e, 'message') else str(e)}"
    except requests.exceptions.RequestException as e:
        return f"[Ollama Error] Local Server Connection Failure. Detail: {e}"
    except Exception as e:
        return f"An unexpected system exception occurred: {str(e)}"


def main():
    # sys.argv contains the execution strings passed to the terminal command line
    # sys.argv[0] is the filename script itself ("prompt_model.py")
    # Expected length: 3 args minimum (script name, model identifier, prompt content)
    if len(sys.argv) < 3:
        print("\n[Usage Guide] Please provide the model identifier and prompt as arguments:")
        print('uv run prompt_model.py <model-name> "<your-prompt-here>"\n')
        print('Example: uv run prompt_model.py llama3.1 "Tell me a joke"')
        return

    # Extract clean target values from terminal arguments
    target_model = sys.argv[1]
    user_prompt = sys.argv[2]

    # Execute and output response block matches formatting constraints
    response = prompt_model(target_model, user_prompt)
    
    print("\n--- RESPONSE ---\n")
    print(response)
    print()

if __name__ == "__main__":
    main()