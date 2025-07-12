FROM node:21-alpine3.19
WORKDIR /app
COPY package*.json ./
RUN npm clean-install
COPY . .
ARG PORT=3000
ENV PORT $PORT
EXPOSE $PORT
CMD ["npm", "start","start-watch"]
