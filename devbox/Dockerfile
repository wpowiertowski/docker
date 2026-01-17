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
       openssh-server \
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

# configure SSH for public key auth only
RUN mkdir -p /run/sshd && \
    chmod 700 /root/.ssh && \
    chmod 600 /root/.ssh/* && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config && \
    echo 'AuthorizedKeysFile .ssh/authorized_keys' >> /etc/ssh/sshd_config

# change default shell to zsh
RUN chsh -s $(which zsh)

WORKDIR /home/workspace

# start SSH daemon and vscode tunnel
CMD service ssh start && code tunnel --name devbox --accept-server-license-terms --cli-data-dir /home/workspace/.vscode-server/cli --server-data-dir /home/workspace/.vscode-server/server --extensions-dir /home/workspace/.vscode-server/extensions