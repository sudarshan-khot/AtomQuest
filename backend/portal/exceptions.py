"""
Custom exception handlers for the portal application.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that provides consistent error responses.
    
    Args:
        exc: The exception that was raised
        context: Additional context about the request
        
    Returns:
        Response object with error details
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If the response is None, it means the exception was not handled by DRF
    if response is None:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return Response(
            {
                'error': 'An unexpected error occurred',
                'detail': str(exc) if not isinstance(exc, Exception) else 'Internal server error'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Log the error
    if response.status_code >= 400:
        logger.warning(
            f"API Error: {response.status_code} - {exc.__class__.__name__}",
            extra={'response_data': response.data}
        )
    
    return response
