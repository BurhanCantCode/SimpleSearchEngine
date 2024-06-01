!pip install Flask pyngrok flask-socketio requests openai google-cloud-vision google-api-python-client
!ngrok authtoken (dm me for it)

import os
import json
import base64
from flask import Flask, render_template, request, redirect, url_for
import requests
from pyngrok import ngrok
from flask_socketio import SocketIO
from googleapiclient import discovery
from googleapiclient.errors import HttpError

app = Flask(__name__)
socketio = SocketIO(app)

# Set up the Custom Search JSON API endpoint and parameters
API_ENDPOINT = 'https://www.googleapis.com/customsearch/v1'
API_KEY = '(dm me for it)'  # Replace with your actual API key
SEARCH_ENGINE_ID = '(dm me for it)'  # Replace with your actual search engine ID

# Set up the Cloud Vision API client
vision_client = discovery.build('vision', 'v1', developerKey=API_KEY)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if an image file was uploaded
        if 'image' not in request.files:
            return redirect(request.url)
        
        image_file = request.files['image']
        
        # Save the uploaded image temporarily
        image_path = 'static/uploaded_image.jpg'
        image_file.save(image_path)
        
        # Extract labels from the image using the Cloud Vision API
        with open(image_path, 'rb') as image:
            image_content = base64.b64encode(image.read()).decode('utf-8')
            
        response = vision_client.images().annotate(
            body={
                'requests': [
                    {
                        'image': {
                            'content': image_content
                        },
                        'features': [
                            {
                                'type': 'LABEL_DETECTION'
                            }
                        ]
                    }
                ]
            }
        ).execute()
        
        labels = [label['description'] for label in response['responses'][0]['labelAnnotations']]
        
        # Perform the product search using the Custom Search JSON API
        search_query = ' '.join(labels)
        search_results = search_products(search_query)
        
        # Render the template with the search results
        return render_template('results.html', products=search_results)
    
    # Render the template for image upload
    return render_template('index.html')

def search_products(query):
    # Prepare the API request
    params = {
        'key': API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': query,
        'num': 10  # Adjust the number of results to retrieve
    }
    
    # Send the API request
    response = requests.get(API_ENDPOINT, params=params)
    
    # Process the API response
    if response.status_code == 200:
        results = response.json()
        products = []
        
        if 'items' in results:
            for item in results['items']:
                product = {
                    'title': item['title'],
                    'link': item['link'],
                    'snippet': item['snippet']
                }
                products.append(product)
        
        return products
    else:
        print(f'Error: {response.status_code}')
        return []

if __name__ == '__main__':
    # Create the 'templates' directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the 'static' directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Create the 'index.html' template file
    with open('templates/index.html', 'w') as file:
        file.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Image Upload</title>
</head>
<body>
    <h1>Upload an Image</h1>
    <form action="/" method="POST" enctype="multipart/form-data">
        <input type="file" name="image" accept="image/*" required>
        <br><br>
        <input type="submit" value="Search">
    </form>
</body>
</html>
        ''')
    
    # Create the 'results.html' template file
    with open('templates/results.html', 'w') as file:
        file.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Search Results</title>
</head>
<body>
    <h1>Search Results</h1>
    {% if products %}
        <ul>
        {% for product in products %}
            <li>
                <a href="{{ product.link }}" target="_blank">{{ product.title }}</a>
                <br>
                <p>{{ product.snippet }}</p>
            </li>
        {% endfor %}
        </ul>
    {% else %}
        <p>No products found.</p>
    {% endif %}
</body>
</html>
        ''')
    
    ngrok_tunnel = ngrok.connect(5000)
    print('Public URL:', ngrok_tunnel.public_url)
    socketio.run(app, allow_unsafe_werkzeug=True)
