FROM node:22.9.0-slim

# MarkdownからPDFを生成するのに利用しているpuppeteerの設定
RUN apt-get update \
    && apt-get install -y wget gnupg firefox-esr fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-khmeros fonts-kacst fonts-freefont-ttf libxss1
ENV PUPPETEER_PRODUCT=firefox \
    NEXT_PUBLIC_HOST_PUPPETEER_EXECUTABLE_PATH=/usr/bin/firefox

# for Netskope
COPY ./netskope_root.crt /usr/local/share/ca-certificates
RUN update-ca-certificates
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/netskope_root.crt

WORKDIR /app

COPY package*.json ./
RUN npm ci --include=dev

COPY . .

ENV NEXT_PUBLIC_HOST=host.docker.internal

EXPOSE 3000

CMD ["sh", "./startPrdDocker.sh"]