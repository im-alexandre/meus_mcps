FROM node:22-bookworm-slim

RUN npm install -g @autodev/codebase

WORKDIR /tmp/autodev-codebase

COPY docker/autodev-codebase/config.json /tmp/autodev-codebase/autodev-config.json

EXPOSE 3001

CMD ["codebase", "index", "--serve"]
