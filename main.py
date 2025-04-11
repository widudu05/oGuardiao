from app import app  # noqa: F401

# This file is used to start the application
# The actual application is defined in app.py

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
