FROM ubuntu:noble

# set needed ENV
ENV POETRY_VERSION=2.2.1 \
    PATH="/root/.local/bin:$PATH"

# install basics
RUN apt-get update && apt-get install --no-install-recommends -y \
       ca-certificates \
       curl \
       git \
       zsh \
       software-properties-common

# install python 3.14
RUN add-apt-repository -y ppa:deadsnakes/ppa && \
    apt install --no-install-recommends -y \
        python3.14
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.14 0

# install poetry
RUN curl -sSL https://install.python-poetry.org | python3.14 -

# install vscode
RUN curl -sL "https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-arm64" \
        --output /tmp/vscode-cli.tgz && \
    tar -xf /tmp/vscode-cli.tgz -C /usr/bin && \
    rm /tmp/vscode-cli.tgz

# get some favorite zsh aliases
COPY .zshrc /root/
COPY .gitconfig /root/
COPY .ssh/* /root/.ssh/

# change default shell to zsh
RUN chsh -s $(which zsh)

WORKDIR /home/workspace

# start vscode tunnel
CMD ["code", "tunnel", "--name", "devbox", "--accept-server-license-terms", "--cli-data-dir", "/home/workspace/.vscode-server/cli", "--server-data-dir", "/home/workspace/.vscode-server/server", "--extensions-dir", "/home/workspace/.vscode-server/extensions" ]