FROM docker:29.1.3-alpine3.23

RUN apk add --no-cache curl && \
    curl -sL "https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-arm64" \
        --output /tmp/vscode-cli.tar.gz && \
    tar -xf /tmp/vscode-cli.tar.gz -C /usr/bin && \
    rm /tmp/vscode-cli.tar.gz

WORKDIR /home/workspace

CMD ["code", "tunnel", "--name", "devbox", "--accept-server-license-terms", "--cli-data-dir", "/home/workspace/.vscode-server/cli", "--server-data-dir", "/home/workspace/.vscode-server/server", "--extensions-dir", "/home/workspace/.vscode-server/extensions" ]