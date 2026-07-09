FROM mcr.microsoft.com/vscode/devcontainers/python:dev-3.12-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

COPY first-run-notice.txt /tmp/staging/
RUN sudo mv -f /tmp/staging/first-run-notice.txt /usr/local/etc/vscode-dev-containers/ \
    && sudo rm -rf /tmp/staging

RUN curl -fsSL https://aka.ms/install-azd.sh | bash
