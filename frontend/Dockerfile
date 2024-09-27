# Use an official Node runtime as a parent image
FROM node:20

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and package-lock.json files
COPY package*.json ./

# Install any needed packages
RUN npm install --legacy-peer-deps
RUN npm install @memgraph/orb

# Copy the current directory contents into the container at /app
COPY . .

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Run the app
CMD ["npm", "start"]