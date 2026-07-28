import os
from dotenv import load_dotenv

loaded = load_dotenv()

print("Loaded:", loaded)
print("Current Directory:", os.getcwd())
print("API Key:", os.getenv("MISTRAL_API_KEY"))