FROM node:22.9.0-slim

# MarkdownからPDFを生成するのに利用しているpuppeteerの設定
RUN apt-get update \
    && apt-get install -y wget gnupg firefox-esr fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-khmeros fonts-kacst fonts-freefont-ttf libxss1
ENV PUPPETEER_PRODUCT=firefox \
    NEXT_PUBLIC_HOST_PUPPETEER_EXECUTABLE_PATH=/usr/bin/firefox

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ENV NEXT_PUBLIC_HOST=host.docker.internal

EXPOSE 3000

CMD ["sh", "./startDevDocker.sh"]