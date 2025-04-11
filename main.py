from app import app
import routes  # Import routes to register them
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
