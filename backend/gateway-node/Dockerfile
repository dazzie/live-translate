# Build context MUST be the assignment root (…/Assignment_1_Live_Translate)
# so the provided widget/ folder is available — the gateway serves it at
# /widget.js via ../../widget/translation-widget.js. We mirror that layout.
#
#   fly deploy . \
#     --config backend/gateway-node/fly.toml \
#     --dockerfile backend/gateway-node/Dockerfile
FROM node:20-slim

WORKDIR /app

COPY widget/ ./widget/

COPY backend/gateway-node/package*.json ./backend/gateway-node/
RUN cd backend/gateway-node && npm install --omit=dev

COPY backend/gateway-node/ ./backend/gateway-node/

WORKDIR /app/backend/gateway-node

EXPOSE 8787

CMD ["node", "server.js"]
