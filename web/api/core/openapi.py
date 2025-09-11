"""
Custom OpenAPI schema configuration for KarlCam Fog API

This module provides enhanced OpenAPI schema generation with custom metadata,
security schemes, and common response definitions.
"""
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """
    Generate custom OpenAPI schema with enhanced metadata and configurations
    
    Args:
        app: FastAPI application instance
        
    Returns:
        dict: Enhanced OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    # Generate base OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )
    
    # Add custom info extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://karlcam.com/assets/karlcam-logo.png",
        "altText": "KarlCam Fog Detection System"
    }
    
    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "KarlCam System Documentation",
        "url": "https://docs.karlcam.com"
    }
    
    # Initialize components if not present
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    # Add security schemes (even though most endpoints are public)
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header", 
            "name": "X-API-Key",
            "description": "API key for administrative operations (not required for public endpoints)"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT authentication token for administrative operations"
        }
    }
    
    # Add common response schemas
    openapi_schema["components"]["responses"] = {
        "NotFound": {
            "description": "The specified resource was not found",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "detail": "Camera with id golden-gate-south not found",
                        "error_code": "CAMERA_NOT_FOUND",
                        "timestamp": "2024-01-10T08:30:00Z",
                        "path": "/api/public/cameras/golden-gate-south"
                    }
                }
            }
        },
        "ValidationError": {
            "description": "Request validation failed",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ValidationErrorResponse"},
                    "example": {
                        "detail": "Validation error",
                        "error_code": "VALIDATION_ERROR",
                        "errors": [
                            {
                                "loc": ["query", "hours"],
                                "msg": "ensure this value is greater than 0",
                                "type": "value_error.number.not_gt",
                                "ctx": {"limit_value": 0}
                            }
                        ],
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        },
        "InternalError": {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "detail": "Internal server error",
                        "error_code": "INTERNAL_ERROR",
                        "timestamp": "2024-01-10T08:30:00Z",
                        "path": "/api/public/cameras"
                    }
                }
            }
        },
        "ServiceUnavailable": {
            "description": "Service temporarily unavailable",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "detail": "Database connection unavailable",
                        "error_code": "SERVICE_UNAVAILABLE",
                        "timestamp": "2024-01-10T08:30:00Z"
                    }
                }
            }
        }
    }
    
    # Add common parameters
    openapi_schema["components"]["parameters"] = {
        "CameraId": {
            "name": "camera_id",
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
            "description": "Unique camera identifier",
            "example": "golden-gate-north"
        },
        "HistoryHours": {
            "name": "hours", 
            "in": "query",
            "required": False,
            "schema": {
                "type": "integer",
                "minimum": 1,
                "maximum": 168,
                "default": 24
            },
            "description": "Hours of historical data to include (max 168 = 1 week)",
            "example": 24
        }
    }
    
    # Add custom headers for CORS and caching
    openapi_schema["components"]["headers"] = {
        "X-Cache-Status": {
            "description": "Indicates if the response was served from cache",
            "schema": {"type": "string", "enum": ["HIT", "MISS"]},
            "example": "HIT"
        },
        "X-RateLimit-Remaining": {
            "description": "Number of requests remaining in the current rate limit window", 
            "schema": {"type": "integer"},
            "example": 95
        },
        "X-Response-Time": {
            "description": "Response processing time in milliseconds",
            "schema": {"type": "integer"},
            "example": 245
        }
    }
    
    # Add API versioning info
    openapi_schema["info"]["x-api-version"] = {
        "current": "2.0.0",
        "supported": ["2.0.0"],
        "deprecated": [],
        "sunset": {}
    }
    
    # Add rate limiting info
    openapi_schema["info"]["x-rate-limit"] = {
        "public_endpoints": {
            "limit": 1000,
            "window": "1 hour",
            "description": "Rate limit for public API endpoints"
        },
        "authenticated_endpoints": {
            "limit": 5000, 
            "window": "1 hour",
            "description": "Higher rate limit for authenticated requests"
        }
    }
    
    # Cache the schema
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_openapi(app: FastAPI):
    """
    Apply custom OpenAPI schema to FastAPI application
    
    Args:
        app: FastAPI application instance to configure
    """
    app.openapi = lambda: custom_openapi(app)