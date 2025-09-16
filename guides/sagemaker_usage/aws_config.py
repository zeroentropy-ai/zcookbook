#!/usr/bin/env python3
"""
AWS Configuration
Edit these values with your AWS credentials,
only neeeded if not already running on SageMaker
"""
import os

# AWS Credentials - defaults to environment variables if set
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'your-access-key-here')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'your-secret-key-here')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
