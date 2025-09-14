import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Error configuring Google AI: {e}")
    model = None

def generate_product_description(name: str, category: str, artist_notes: str) -> str:
    if not model:
        return "AI service is not available. Please check API key."
    
    prompt = f"""
    You are an expert copywriter for an artisan marketplace called Artiflex. Your task is to write a compelling, evocative, and story-driven product description.
    
    Product Name: {name}
    Category: {category}
    Artist's Notes: {artist_notes}
    
    Based on the information above, write a product description that:
    1. Tells a short story about the inspiration or creation process.
    2. Highlights the unique craftsmanship and materials used.
    3. Connects with the customer on an emotional level.
    4. Is formatted beautifully for a web page using simple paragraphs.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating description: {e}"


def suggest_product_price(name: str, category: str, artist_notes: str) -> str:
    if not model:
        return "AI service is not available."

    prompt = f"""
    You are an e-commerce pricing consultant specializing in handcrafted goods. 
    
    Product Name: {name}
    Category: {category}
    Artist's Notes on materials and effort: {artist_notes}
    
    Analyze the product details and suggest a price range (in USD). Provide a brief justification. Format the output as:
    
    Suggested Price Range: $XX.XX - $YY.YY
    Justification: [Your reasoning here in one paragraph]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error suggesting price: {e}"