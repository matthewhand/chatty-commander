#!/usr/bin/env python3
"""
Node.js Bridge Generator for Discord/Slack Integration

This tool generates a Node.js application that acts as a bridge between
Discord/Slack platforms and the Python advisor API.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


def generate_package_json() -> str:
    """Generate package.json for the Node.js bridge application."""
    return json.dumps({
        "name": "chatty-commander-bridge",
        "version": "1.0.0",
        "description": "Node.js bridge for Discord/Slack integration with ChattyCommander advisors",
        "main": "src/index.js",
        "scripts": {
            "start": "node src/index.js",
            "dev": "nodemon src/index.js",
            "test": "jest"
        },
        "dependencies": {
            "express": "^4.18.2",
            "discord.js": "^14.14.1",
            "@slack/bolt": "^3.17.1",
            "axios": "^1.6.0",
            "dotenv": "^16.3.1",
            "winston": "^3.11.0"
        },
        "devDependencies": {
            "nodemon": "^3.0.1",
            "jest": "^29.7.0"
        },
        "engines": {
            "node": ">=18.0.0"
        }
    }, indent=2)


def generate_env_template() -> str:
    """Generate .env template for configuration."""
    return """# Node.js Bridge Configuration

# Python Advisor API
ADVISOR_API_URL=http://localhost:8000
BRIDGE_TOKEN=your_shared_secret_here

# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_GUILD_ID=your_discord_guild_id

# Slack App Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your_slack_signing_secret
SLACK_APP_TOKEN=xapp-your-slack-app-token

# Logging
LOG_LEVEL=info
LOG_FILE=bridge.log
"""


def generate_index_js() -> str:
    """Generate the main index.js file for the bridge application."""
    return '''const express = require('express');
const { Client, GatewayIntentBits } = require('discord.js');
const { App } = require('@slack/bolt');
const axios = require('axios');
const winston = require('winston');
require('dotenv').config();

// Configure logging
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: process.env.LOG_FILE || 'bridge.log' })
  ]
});

// Initialize Express app
const app = express();
app.use(express.json());

// Initialize Discord client
const discordClient = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

// Initialize Slack app
const slackApp = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET,
  socketMode: true,
  appToken: process.env.SLACK_APP_TOKEN
});

// Advisor API client
class AdvisorAPIClient {
  constructor() {
    this.baseURL = process.env.ADVISOR_API_URL || 'http://localhost:8000';
    this.bridgeToken = process.env.BRIDGE_TOKEN;
  }

  async sendMessage(platform, channel, user, text) {
    try {
      const response = await axios.post(`${this.baseURL}/api/v1/advisors/message`, {
        platform,
        channel,
        user,
        text
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      return response.data;
    } catch (error) {
      logger.error('Error sending message to advisor API:', error.message);
      throw error;
    }
  }

  async sendBridgeEvent(event) {
    try {
      const response = await axios.post(`${this.baseURL}/bridge/event`, event, {
        headers: {
          'Content-Type': 'application/json',
          'X-Bridge-Token': this.bridgeToken
        }
      });
      return response.data;
    } catch (error) {
      logger.error('Error sending bridge event:', error.message);
      throw error;
    }
  }
}

const advisorClient = new AdvisorAPIClient();

// Discord event handlers
discordClient.on('ready', () => {
  logger.info(`Discord bot logged in as ${discordClient.user.tag}`);
});

discordClient.on('messageCreate', async (message) => {
  if (message.author.bot) return;
  
  try {
    const response = await advisorClient.sendMessage(
      'discord',
      message.channel.id,
      message.author.id,
      message.content
    );
    
    await message.reply(response.reply);
  } catch (error) {
    logger.error('Error handling Discord message:', error);
    await message.reply('Sorry, I encountered an error processing your message.');
  }
});

// Slack event handlers
slackApp.message(async ({ message, say }) => {
  try {
    const response = await advisorClient.sendMessage(
      'slack',
      message.channel,
      message.user,
      message.text
    );
    
    await say(response.reply);
  } catch (error) {
    logger.error('Error handling Slack message:', error);
    await say('Sorry, I encountered an error processing your message.');
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start the application
async function start() {
  try {
    // Start Express server
    const port = process.env.PORT || 3001;
    app.listen(port, () => {
      logger.info(`Bridge server listening on port ${port}`);
    });

    // Start Discord bot
    await discordClient.login(process.env.DISCORD_TOKEN);
    
    // Start Slack app
    await slackApp.start();
    logger.info('Slack app started');
    
  } catch (error) {
    logger.error('Error starting bridge application:', error);
    process.exit(1);
  }
}

start();
'''


def generate_readme() -> str:
    """Generate README.md for the Node.js bridge application."""
    return '''# ChattyCommander Bridge

Node.js bridge application for connecting Discord and Slack to the ChattyCommander advisor API.

## Features

- Discord bot integration with message handling
- Slack app integration with event subscriptions
- Secure authentication with Python advisor API
- Structured logging and error handling
- Health check endpoint

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start the bridge:
   ```bash
   npm start
   ```

## Configuration

### Discord Bot Setup

1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot and get the token
3. Set up intents (Message Content Intent required)
4. Invite the bot to your server

### Slack App Setup

1. Create a Slack app at https://api.slack.com/apps
2. Add bot token scopes (chat:write, channels:history, etc.)
3. Set up event subscriptions for message events
4. Install the app to your workspace

### Python Advisor API

Ensure the Python advisor API is running and accessible at the configured URL.

## Environment Variables

- `ADVISOR_API_URL`: URL of the Python advisor API
- `BRIDGE_TOKEN`: Shared secret for authentication
- `DISCORD_TOKEN`: Discord bot token
- `SLACK_BOT_TOKEN`: Slack bot token
- `SLACK_SIGNING_SECRET`: Slack app signing secret
- `SLACK_APP_TOKEN`: Slack app token for socket mode

## Development

```bash
npm run dev  # Start with nodemon for development
npm test     # Run tests
```

## Deployment

The bridge can be deployed to any Node.js hosting platform (Heroku, Railway, etc.).
Ensure all environment variables are configured in your deployment environment.
'''


def generate_dockerfile() -> str:
    """Generate Dockerfile for containerized deployment."""
    return '''FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S bridge -u 1001

# Change ownership
RUN chown -R bridge:nodejs /app
USER bridge

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD node -e "require('http').get('http://localhost:3001/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"

# Start the application
CMD ["npm", "start"]
'''


def generate_docker_compose() -> str:
    """Generate docker-compose.yml for local development."""
    return '''version: '3.8'

services:
  bridge:
    build: .
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=development
      - ADVISOR_API_URL=http://host.docker.internal:8000
      - BRIDGE_TOKEN=${BRIDGE_TOKEN}
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
      - SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}
      - SLACK_APP_TOKEN=${SLACK_APP_TOKEN}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
'''


def generate_bridge_app(output_dir: str = "bridge") -> None:
    """Generate the complete Node.js bridge application."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create directory structure
    (output_path / "src").mkdir(exist_ok=True)
    (output_path / "logs").mkdir(exist_ok=True)
    
    # Generate files
    files = {
        "package.json": generate_package_json(),
        ".env.example": generate_env_template(),
        "src/index.js": generate_index_js(),
        "README.md": generate_readme(),
        "Dockerfile": generate_dockerfile(),
        "docker-compose.yml": generate_docker_compose(),
        ".gitignore": "node_modules/\n.env\nlogs/\n*.log\n",
    }
    
    for filename, content in files.items():
        file_path = output_path / filename
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Generated: {file_path}")
    
    print(f"\nBridge application generated in: {output_path.absolute()}")
    print("Next steps:")
    print("1. cd bridge")
    print("2. npm install")
    print("3. cp .env.example .env")
    print("4. Configure your environment variables")
    print("5. npm start")


if __name__ == "__main__":
    import sys
    
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "bridge"
    generate_bridge_app(output_dir)
