# Use official Python 3.8.10 image
FROM python:3.8.10

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy dependency files first to cache better
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose the Flask port
EXPOSE 5000

# Run the app
CMD ["gunicorn", "index:app", "--bind", "0.0.0.0:5000"]
