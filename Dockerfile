FROM python:3.10-slim

# Install tesseract
RUN apt-get update && apt-get install -y tesseract-ocr && apt-get clean

# Set work directory
WORKDIR /app

# Copy files
COPY . /app

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD ["python", "telegram_ocr_bot.py"]
