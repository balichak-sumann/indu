# Frontend Dockerfile - uses pre-built dist files
FROM node:20-alpine

WORKDIR /app

# Copy pre-built dist files
COPY dist ./dist

# Copy server script
COPY server.cjs .

# Expose port
EXPOSE 3000

# Start application with Node.js server
CMD ["node", "server.cjs"]
