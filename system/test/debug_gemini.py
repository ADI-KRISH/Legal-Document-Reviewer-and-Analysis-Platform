from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

print("Attempting to instantiate ChatGoogleGenerativeAI...")

try:
    print("1. With model and temperature=0.0")
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0)
    print("Success 1")
except Exception as e:
    print(f"Failed 1: {e}")

try:
    print("2. With model only")
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    print("Success 2")
except Exception as e:
    print(f"Failed 2: {e}")

try:
    print("3. With default (no args)")
    llm = ChatGoogleGenerativeAI()
    print("Success 3")
except Exception as e:
    print(f"Failed 3: {e}")

try:
    print("4. With google_api_key explicitly passed")
    api_key = os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
    print("Success 4")
except Exception as e:
    print(f"Failed 4: {e}")
