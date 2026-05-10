FROM node:20

ENV APP_SECRET=super-secret-value

WORKDIR /app
COPY . .
RUN npm install

CMD ["node", "server.js"]
