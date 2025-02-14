# AI Documentation Assistant - MadCap Flare Integration

This directory contains the custom toolbar integration for MadCap Flare, providing AI-powered documentation assistance directly within the Flare interface.

## Features

- Real-time AI assistance for documentation queries
- Content drafting capabilities
- Documentation review and suggestions
- Direct insertion of AI-generated content into Flare documents

## Installation

1. Copy the `toolbar` directory to your Flare project's appropriate location
2. Configure the toolbar in Flare:
   - Open Flare
   - Navigate to Tools > Customize Toolbars
   - Add the AI Documentation Assistant toolbar

## Configuration

Update the `API_BASE_URL` in `script.js` to point to your deployed backend service:

javascript
const API_BASE_URL = 'http://your-api-server:5000/api';

## Usage

1. **Ask a Question**: Click the "Ask a Question" button to get instant answers about documentation best practices or technical queries.

2. **Generate Draft**: Use the "Generate Draft" button to create initial content drafts based on your requirements.

3. **Review Content**: Click "Review Content" to get AI-powered suggestions for improving your documentation.

4. **Insert Content**: Use the "Insert into Document" button to add AI-generated content directly into your Flare document.

## Development

### Prerequisites

- MadCap Flare (latest version recommended)
- Modern web browser
- Access to the AI Documentation Assistant backend service

### File Structure

- `toolbar/`
  - `index.html` - Main toolbar interface
  - `styles.css` - Toolbar styling
  - `script.js` - Toolbar functionality and API integration

### Customization

The toolbar can be customized by modifying:

- `styles.css` for visual changes
- `script.js` for behavioral modifications
- `index.html` for structural updates

## Troubleshooting

Common issues and solutions:

1. **API Connection Failed**
   - Verify the API_BASE_URL is correct
   - Check network connectivity
   - Ensure the backend service is running

2. **Content Insertion Issues**
   - Verify Flare permissions
   - Check if the document is locked
   - Ensure the cursor is in a valid insertion point

## Support

For technical support or feature requests, please contact the development team or create an issue in the project repository.

