FROM python:3.13-alpine

# 安装系统依赖
RUN apk add --no-cache \
    wget \
    gnupg \
    curl \
    unzip \
    chromium \
    chromium-chromedriver \
    harfbuzz \
    nss \
    freetype \
    ttf-freefont \
    font-noto-emoji \
    wqy-zenhei

# 安装Chrome浏览器已被替换为Alpine自带的chromium

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装编译依赖
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 删除编译依赖
RUN apk del .build-deps

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HEADLESS=true
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 暴露Redis端口
EXPOSE 6379

# 启动应用
CMD ["python", "domain_tester.py"]