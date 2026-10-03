FROM python:3.10-slim

# প্রয়োজনীয় সিস্টেম প্যাকেজ ও Google Chrome ইনস্টল
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libglib2.0-0 \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ফাইল কপি ও পাইথন প্যাকেজ ইনস্টল
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# বট চালু করার কমান্ড
CMD ["python", "main.py"]
