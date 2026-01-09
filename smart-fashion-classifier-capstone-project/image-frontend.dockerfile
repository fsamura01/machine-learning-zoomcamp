# Use a slim version of Python 3.11 for a smaller image size
FROM python:3.11-slim

# Install pipenv
RUN pip install pipenv

# Set the working directory in the container
WORKDIR /app

# Copy dependency files
COPY ["Pipfile", "Pipfile.lock", "./"]

# Install dependencies directly into the system python
RUN pipenv install --system --deploy

# Copy the Streamlit application code
COPY ["streamlit-frontend/app.py", "./"]

# Streamlit uses port 8501 by default
EXPOSE 8501

# Configure Streamlit to run in a production-ready container environment
# --server.address=0.0.0.0 allows external connections
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]