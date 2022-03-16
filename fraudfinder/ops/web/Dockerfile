# Use lightweight Linux image with nodejs pre-installed.
FROM node:14-alpine

# Set default working directory.
WORKDIR /usr/src/app

# Copy local artifacts to the container image.
COPY rollup.config.js ./
COPY package*.json ./

# Install dependencies into this container so there's no need to 
# install anything at container run time.
RUN npm install

# Copy installed files into container image.
COPY ./src ./src
COPY ./public ./public

# Build step.
RUN npm run-script build

# Service must listen to $PORT environment variable.
# This default value facilitates local development.
EXPOSE 8080
ENV PORT 8080
ENV HOST 0.0.0.0

# Run the web service on container startup. Here you use the gunicorn
# server, with one worker process and 8 threads. For environments 
# with multiple CPU cores, increase the number of workers to match 
# the number of cores available.
CMD [ "npm", "start" ]
