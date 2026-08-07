"""
OpenAPI 3.0 Schema Configuration

This module configures drf-spectacular for OpenAPI 3.0 schema generation.
"""

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from django.urls import path


def get_openapi_patterns():
    """
    Get OpenAPI schema URL patterns.
    
    Returns:
        List of URL patterns for OpenAPI endpoints
    """
    return [
        # Schema definition
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        
        # Swagger UI
        path('schema/swagger-ui/', SpectacularSwaggerView.as_view(), name='swagger-ui'),
        
        # Redoc UI (alternative)
        # path('schema/redoc/', SpectacularRedocView.as_view(), name='redoc'),
    ]


# ============================================================================
# API Versioning Configuration
# ============================================================================


API_VERSIONS = {
    'v1': {
        'version': '1.0.0',
        'path': 'api/v1',
        'description': 'Current stable API version',
        'status': 'stable',
    },
    'v2': {
        'version': '2.0.0',
        'path': 'api/v2',
        'description': 'Upcoming API version (in development)',
        'status': 'development',
    },
}


def get_versioned_patterns():
    """
    Get versioned API URL patterns.
    
    Returns:
        Dictionary with versioned URL patterns
    """
    return {
        'v1': 'E-Career.backend.config.urls_v1',
        'v2': 'E-Career.backend.config.urls_v2',
    }


# ============================================================================
# API Response Examples
# ============================================================================


API_RESPONSE_EXAMPLES = {
    'success_200': {
        'description': 'Successful response',
        'content': {
            'application/json': {
                'example': {
                    'success': True,
                    'data': {},
                }
            }
        },
    },
    'success_201': {
        'description': 'Resource created',
        'content': {
            'application/json': {
                'example': {
                    'success': True,
                    'data': {},
                }
            }
        },
    },
    'error_400': {
        'description': 'Bad request',
        'content': {
            'application/json': {
                'example': {
                    'success': False,
                    'error': 'Invalid request parameters',
                }
            }
        },
    },
    'error_401': {
        'description': 'Unauthorized',
        'content': {
            'application/json': {
                'example': {
                    'success': False,
                    'error': 'Authentication credentials were not provided',
                }
            }
        },
    },
    'error_403': {
        'description': 'Forbidden',
        'content': {
            'application/json': {
                'example': {
                    'success': False,
                    'error': 'You do not have permission to perform this action',
                }
            }
        },
    },
    'error_404': {
        'description': 'Not found',
        'content': {
            'application/json': {
                'example': {
                    'success': False,
                    'error': 'Resource not found',
                }
            }
        },
    },
    'error_429': {
        'description': 'Rate limit exceeded',
        'content': {
            'application/json': {
                'example': {
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'retry_after': 60,
                }
            }
        },
    },
    'error_500': {
        'description': 'Internal server error',
        'content': {
            'application/json': {
                'example': {
                    'success': False,
                    'error': 'Internal server error',
                }
            }
        },
    },
}


# ============================================================================
# Authentication Examples
# ============================================================================


AUTHENTICATION_EXAMPLES = {
    'token_auth': {
        'description': 'Token Authentication',
        'value': 'Token your-token-here',
    },
    'jwt_auth': {
        'description': 'JWT Authentication',
        'value': 'Bearer your-jwt-token-here',
    },
}


# ============================================================================
# Query Parameter Examples
# ============================================================================


QUERY_PARAMETER_EXAMPLES = {
    'pagination': {
        'page': {
            'description': 'Page number',
            'type': 'integer',
            'default': 1,
            'minimum': 1,
        },
        'page_size': {
            'description': 'Number of results per page',
            'type': 'integer',
            'default': 10,
            'maximum': 100,
        },
    },
    'filtering': {
        'search': {
            'description': 'Search query',
            'type': 'string',
        },
        'ordering': {
            'description': 'Field to order by (prefix with - for descending)',
            'type': 'string',
        },
    },
    'date_range': {
        'start_date': {
            'description': 'Start date (YYYY-MM-DD)',
            'type': 'string',
            'format': 'date',
        },
        'end_date': {
            'description': 'End date (YYYY-MM-DD)',
            'type': 'string',
            'format': 'date',
        },
    },
}


# ============================================================================
# Response Schema Examples
# ============================================================================


RESPONSE_SCHEMAS = {
    'paginated_response': {
        'type': 'object',
        'properties': {
            'count': {
                'type': 'integer',
                'description': 'Total number of results',
            },
            'next': {
                'type': 'string',
                'nullable': True,
                'format': 'uri',
                'description': 'URL to next page',
            },
            'previous': {
                'type': 'string',
                'nullable': True,
                'format': 'uri',
                'description': 'URL to previous page',
            },
            'results': {
                'type': 'array',
                'items': {
                    'type': 'object',
                },
            },
        },
    },
    'error_response': {
        'type': 'object',
        'properties': {
            'success': {
                'type': 'boolean',
                'example': False,
            },
            'error': {
                'type': 'string',
                'example': 'Error message',
            },
            'details': {
                'type': 'object',
                'nullable': True,
                'example': {},
            },
        },
    },
    'meta_response': {
        'type': 'object',
        'properties': {
            'success': {
                'type': 'boolean',
                'example': True,
            },
            'data': {
                'type': 'object',
            },
            'meta': {
                'type': 'object',
                'properties': {
                    'timestamp': {
                        'type': 'string',
                        'format': 'date-time',
                    },
                    'version': {
                        'type': 'string',
                        'example': '1.0.0',
                    },
                },
            },
        },
    },
}