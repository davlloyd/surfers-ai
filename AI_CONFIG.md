# AI Configuration for Surfers AI

This document explains how to configure the OpenAI model used by the Surfers AI application.

## Environment Variable Configuration

The OpenAI model can be configured using the `OPENAI_MODEL` environment variable.

### Default Configuration
- **Default Model**: `gpt-4o`
- **Environment Variable**: `OPENAI_MODEL`

### Setting the Environment Variable

#### Development (Local)
```bash
export OPENAI_MODEL=gpt-4o
# or
export OPENAI_MODEL=gpt-4-turbo
# or
export OPENAI_MODEL=gpt-3.5-turbo
```

#### Production (Cloud Foundry)
The model is configured in `manifest.yml`:
```yaml
env:
  OPENAI_MODEL: gpt-4o
```

#### Docker
```bash
docker run -e OPENAI_MODEL=gpt-4o your-app
```

## Runtime Configuration (API)

You can also change the model at runtime using the configuration API endpoints (changes don't persist across restarts):

### Get Current Model Configuration
```bash
curl http://localhost:8080/api/config/model
```

Response:
```json
{
  "status": "success",
  "model_name": "gpt-4o",
  "configured_via": "default"
}
```

### Update Model Configuration
```bash
curl -X PUT http://localhost:8080/api/config/model \
  -H "Content-Type: application/json" \
  -d '{"model_name": "gpt-4-turbo"}'
```

Response:
```json
{
  "status": "success",
  "message": "Model name updated from 'gpt-4o' to 'gpt-4-turbo'",
  "previous_model": "gpt-4o",
  "new_model": "gpt-4-turbo",
  "note": "This change is runtime only. To persist across restarts, set the OPENAI_MODEL environment variable."
}
```

### Get All Configuration
```bash
curl http://localhost:8080/api/config
```

### Get Environment Information
```bash
curl http://localhost:8080/api/config/environment
```

## Supported Models

The application supports any OpenAI model that supports chat completions. Common options include:

- `gpt-4o` (default) - Latest GPT-4 Omni model
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-4` - Standard GPT-4
- `gpt-3.5-turbo` - GPT-3.5 Turbo (cost-effective option)

## Configuration Priority

1. **Runtime API updates** (temporary, doesn't persist)
2. **Environment variables** (persistent)
3. **Default value** (`gpt-4o`)

## Example Configurations

### Cost-Effective Setup
```bash
export OPENAI_MODEL=gpt-3.5-turbo
```

### High-Performance Setup
```bash
export OPENAI_MODEL=gpt-4o
```

### Custom Model
```bash
export OPENAI_MODEL=your-custom-model-name
```

## Model Requirements

The selected model must:
- Support OpenAI Chat Completions API
- Handle the message format used by the application
- Be accessible with your OpenAI API key

## Troubleshooting

### Invalid Model Error
If you receive an error about an invalid model:
1. Check that the model name is correct
2. Verify your OpenAI API key has access to the model
3. Check OpenAI's documentation for available models

### Configuration Not Taking Effect
1. Restart the application after setting environment variables
2. Check that the environment variable is properly set: `echo $OPENAI_MODEL`
3. Use the `/api/config/environment` endpoint to verify configuration

## Testing Configuration

After changing the model configuration, test with a simple chat message to verify the new model is being used. Monitor the application logs for any model-related errors. 