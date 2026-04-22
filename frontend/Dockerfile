FROM node:20-alpine

WORKDIR /app

# Copy package files dulu untuk memanfaatkan Docker cache
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy semua kode
COPY . .

EXPOSE 3000

# Jalankan development server
CMD ["npm", "run", "dev"]