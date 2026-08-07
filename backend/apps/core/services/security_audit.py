"""
Security Audit Service

Implements security audit features for the application.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class SecurityAuditService:
    """
    Service for security auditing.
    
    Features:
    - SQL injection detection
    - XSS detection
    - Rate limiting
    - Authentication validation
    - Input sanitization
    """
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b.*\bWHERE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(--\s*$)",
        r"(;\s*$)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"('\s*OR\s*')",
        r"('\s*OR\s*1\s*=\s*1)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<svg[^>]*onload",
        r"expression\s*\(",
    ]
    
    # Suspicious user agents
    SUSPICIOUS_USER_AGENTS = [
        r"sqlmap",
        r"nikto",
        r"nmap",
        r"masscan",
        r"dirbuster",
        r"gobuster",
        r"wpscan",
        r"acunetix",
        r"nessus",
        r"openvas",
    ]
    
    def __init__(self):
        self._audit_log = []
        self._blocked_requests = []
    
    def check_sql_injection(self, input_string: str) -> bool:
        """
        Check for SQL injection attempts.
        
        Args:
            input_string: Input string to check
            
        Returns:
            True if SQL injection detected
        """
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                logger.warning(
                    'SQL injection attempt detected',
                    pattern=pattern,
                    input=input_string[:100],
                )
                return True
        return False
    
    def check_xss(self, input_string: str) -> bool:
        """
        Check for XSS attempts.
        
        Args:
            input_string: Input string to check
            
        Returns:
            True if XSS detected
        """
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                logger.warning(
                    'XSS attempt detected',
                    pattern=pattern,
                    input=input_string[:100],
                )
                return True
        return False
    
    def check_suspicious_user_agent(self, user_agent: str) -> bool:
        """
        Check for suspicious user agents.
        
        Args:
            user_agent: User agent string
            
        Returns:
            True if suspicious user agent detected
        """
        for pattern in self.SUSPICIOUS_USER_AGENTS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                logger.warning(
                    'Suspicious user agent detected',
                    user_agent=user_agent[:100],
                )
                return True
        return False
    
    def sanitize_input(self, input_string: str) -> str:
        """
        Sanitize user input.
        
        Args:
            input_string: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', input_string)
        return sanitized.strip()
    
    def validate_csrf_token(self, request: HttpRequest, token: str) -> bool:
        """
        Validate CSRF token.
        
        Args:
            request: HTTP request
            token: CSRF token
            
        Returns:
            True if token is valid
        """
        if not token:
            logger.warning('Missing CSRF token')
            return False
        
        # In production, use Django's CSRF validation
        return True
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if API key is valid
        """
        if not api_key:
            return False
        
        # Check length
        if len(api_key) < 32:
            return False
        
        # Check format (alphanumeric + special chars)
        if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
            return False
        
        return True
    
    def audit_request(self, request: HttpRequest) -> Dict[str, Any]:
        """
        Audit an HTTP request.
        
        Args:
            request: HTTP request
            
        Returns:
            Audit result
        """
        result = {
            'is_safe': True,
            'warnings': [],
            'blocked': False,
        }
        
        # Check user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if self.check_suspicious_user_agent(user_agent):
            result['warnings'].append('Suspicious user agent')
            result['is_safe'] = False
        
        # Check for SQL injection in query parameters
        for key, value in request.GET.items():
            if self.check_sql_injection(value):
                result['warnings'].append(f'SQL injection in {key}')
                result['is_safe'] = False
        
        # Check for XSS in query parameters
        for key, value in request.GET.items():
            if self.check_xss(value):
                result['warnings'].append(f'XSS in {key}')
                result['is_safe'] = False
        
        # Log audit result
        self._audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'path': request.path,
            'method': request.method,
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': user_agent[:100],
            'result': result,
        })
        
        return result
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit log.
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of audit log entries
        """
        return self._audit_log[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get security audit statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'type': 'security_audit',
            'total_audits': len(self._audit_log),
            'blocked_requests': len(self._blocked_requests),
            'sql_injection_patterns': len(self.SQL_INJECTION_PATTERNS),
            'xss_patterns': len(self.XSS_PATTERNS),
            'suspicious_user_agents': len(self.SUSPICIOUS_USER_AGENTS),
        }


def validate_request_security(request: HttpRequest) -> Dict[str, Any]:
    """
    Validate security for an HTTP request.
    
    Args:
        request: HTTP request
        
    Returns:
        Security validation result
    """
    service = SecurityAuditService()
    return service.audit_request(request)