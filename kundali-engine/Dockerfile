
# 1. Use an official Python runtime as a parent image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file FIRST to leverage Docker's build cache
COPY requirements.txt .

# 4. Install the Python dependencies
RUN pip install --no-cache-dir --default-timeout=100 --retries=5 -r requirements.txt
RUN apt-get update && apt-get install -y curl
# 5. Copy the rest of your application code and assets
#    The .dockerignore file will prevent junk files from being copied.
COPY . .

# 6. Expose the port the app runs on
EXPOSE 9090

# 7. Define the command to run your app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9090"]
