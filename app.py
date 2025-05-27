# Entry point for the StarWeb application

from starweb_app.main import app, StarWeb

if __name__ == '__main__':
    # Apply the WSGI wrapper if it's still intended to be used.
    # Based on the original app.py, it was: app.wsgi_app = StarWeb(app.wsgi_app)
    app.wsgi_app = StarWeb(app.wsgi_app)
    
    # Run the development server
    # Considerations for production: use a proper WSGI server like Gunicorn or uWSGI.
    # Debug mode should typically be False in production.
    app.run(debug=True) # Set debug=True for development, False for production
