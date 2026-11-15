FROM ghcr.io/anomalyco/opencode:2.0.0
USER root
RUN apk add --no-cache git \
 && git config --system credential.helper '!f() { echo username=x-access-token; echo "password=$GITHUB_TOKEN"; }; f' \
 && git config --system --add safe.directory /workspace \
 && git config --system user.name "AROX OpenCode" \
 && git config --system user.email "opencode@arox.local"
USER 1000:1000
