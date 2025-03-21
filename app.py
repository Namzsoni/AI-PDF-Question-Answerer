from flask import Flask, request, jsonify, render_template
import os
import fitz
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY") or "your_openai_api_key_here"

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyMuPDF.
    """
    try:
        pdf_document = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text += page.get_text()
        pdf_document.close()
        return text
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

def query_openai(prompt):
    """
    Sends a prompt to OpenAI and retrieves the response using the ChatCompletion API.
    """
    client = openai.Client()
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use GPT-3.5 or GPT-4
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error querying OpenAI API: {e}")
        return None
@app.route('/')
def home():
    """
    Renders the home page with a form for PDF upload and question input.
    """
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """
    Handles the PDF upload and question input, processes the PDF, and queries OpenAI.
    """
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF file uploaded."}), 400

    pdf_file = request.files['pdf']
    question = request.form.get('question', '')

    if not question.strip():
        return jsonify({"error": "Question cannot be empty."}), 400

    # Save the uploaded PDF temporarily
    pdf_path = os.path.join("temp", pdf_file.filename)
    os.makedirs("temp", exist_ok=True)
    pdf_file.save(pdf_path)

    # Extract text from the PDF
    pdf_text = extract_text_from_pdf(pdf_path)
    if "Error" in pdf_text:
        return jsonify({"error": pdf_text}), 500

    # Construct the prompt
    prompt = f"Context: {pdf_text}\n\nQuestion: {question}\nAnswer:"

    # Query OpenAI
    answer = query_openai(prompt)
    if "Error" in answer:
        return jsonify({"error": answer}), 500

    # Return the answer
    return render_template('index.html', error=None, answer=answer)

if __name__ == '__main__':
    app.run(debug=True)