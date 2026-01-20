"""
Helper functions for creating mock objects in tests
"""

import json
from unittest.mock import Mock, MagicMock
from pathlib import Path


def create_mock_anthropic_client(real_responses=None):
    """Create a mock Anthropic client for testing, optionally with real responses"""
    mock_client = Mock()

    # Mock batch creation
    mock_batch = Mock()
    mock_batch.id = "batch_test_123"
    mock_batch.processing_status = "ended"
    mock_batch.request_counts = Mock()
    mock_batch.request_counts.succeeded = 2
    mock_batch.request_counts.errored = 0
    mock_batch.output_file_id = "file_test_output"

    mock_client.batches.create.return_value = mock_batch
    mock_client.batches.retrieve.return_value = mock_batch

    # Mock file operations
    mock_file = Mock()
    mock_file.id = "file_test_456"
    mock_client.files.create.return_value = mock_file

    # Mock file content - use real responses if provided
    if real_responses and "avorion_batch_responses" in real_responses:
        # Extract the JSON from the real response
        real_response = real_responses["avorion_batch_responses"]
        if real_response.get("success"):
            response_text = real_response["response_text"]
            # Try to parse and extract the JSON part
            try:
                # Look for JSON in markdown code blocks
                if "```json" in response_text:
                    start = response_text.find("```json") + 6
                    end = response_text.find("```", start)
                    json_part = response_text[start:end].strip()
                    parsed_json = json.loads(json_part)
                else:
                    # Try to parse the entire response as JSON
                    parsed_json = json.loads(response_text)
                # Format as expected by tests
                formatted_response = json.dumps(parsed_json, indent=2)
            except:
                # Fallback to basic mock response if parsing fails
                formatted_response = '{"prompt": "Test prompt", "response": "Test response"}'
        else:
            formatted_response = '{"prompt": "Test prompt", "response": "Test response"}'
    else:
        formatted_response = '{"prompt": "Test prompt", "response": "Test response"}'

    mock_file_content = Mock()
    mock_file_content.text = formatted_response
    mock_client.files.content.return_value = mock_file_content

    return mock_client


def create_mock_training_arguments():
    """Create mock training arguments for testing"""
    mock_args = Mock()
    mock_args.output_dir = "./test_adapters"
    mock_args.num_train_epochs = 1
    mock_args.per_device_train_batch_size = 1
    mock_args.gradient_accumulation_steps = 1
    mock_args.learning_rate = 1e-4
    mock_args.warmup_ratio = 0.01
    mock_args.logging_steps = 1
    mock_args.save_steps = 1
    mock_args.save_total_limit = 1
    mock_args.bf16 = True
    mock_args.optim = "paged_adamw_8bit"
    mock_args.report_to = "none"

    return mock_args


def create_mock_model_config():
    """Create mock model configuration"""
    mock_config = {
        "model": {"name": "Qwen/Qwen3-Coder-30B-A3B-Instruct", "load_in_4bit": True}
    }
    return mock_config


def get_real_anthropic_response(response_name, real_responses):
    """Get a real Anthropic response for testing"""
    if real_responses and response_name in real_responses:
        response_data = real_responses[response_name]
        if response_data.get("success"):
            return response_data["response_text"]

    # Return a default mock response if no real response is available
    return '{"prompt": "Test prompt", "response": "Test response"}'
