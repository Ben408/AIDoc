# AI-Powered Documentation System

An intelligent documentation assistant that integrates with MadCap Flare to provide AI-powered content generation, review, and query capabilities.

## Features

### Core AI Functionality (Phase 1A - Completed)
- AI-powered documentation query response
- Documentation generation
- Automated content drafting with context awareness 
- Documentation review and suggestions
- Intelligent content analysis
- Performance monitoring
- Acrolinx quality checks
- Comprehensive error handling
- Content structure analysis
- Style consistency maintenance
- Automated content formatting
- Pattern recognition
- RestAPI endpoints
- Simulator UI

### Integrations
- OpenAI GPT-4 integration
- Confluence integration
- JIRA integration
- Acrolinx content quality platform
- Redis caching

### Flare Integration (Phase 1B - In Progress)
- Integration with Flare's content management via MadCap Flare custom toolbar

## Recent Updates

### Error Handling System
- Centralized error management
- Pattern detection and analysis
- Automated recovery procedures
- Error categorization and severity levels
- Integration with notification systems

### Documentation 
- API documentation generation
- User guide creation
- Developer documentation
- Automated documentation updates

### Testing Infrastructure
- Comprehensive unit tests
- Integration test suite
- System-wide error handling tests
- Performance monitoring tests

## Getting Started

### Prerequisites
```bash
python 3.8+
redis-server
```

### Installation
```bash
pip install -r requirements.txt
cp .env.example .env
# Configure your environment variables
```
## Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Running the System

### Local Development
```bash
python run_simulator.py
```

### Docker Deployment
```bash
docker-compose up
```

### Running Tests
```bash
pytest  # Run all tests
pytest tests/test_utils/  # Run utility tests
pytest tests/test_agents/  # Run agent tests
```

See `.env.example` for required environment variables:
- OpenAI API credentials
- JIRA/Confluence settings
- Redis configuration
- Acrolinx API settings

## Documentation
- [API Documentation](docs/api.md)
- [Developer Guide](docs/developer_guide.md)
- [Test Documentation](tests/README.md)

## License

[MIT License](LICENSE)
