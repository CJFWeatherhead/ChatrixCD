"""Log redaction for sensitive information."""

import re
import logging
from typing import Optional


class SensitiveInfoRedactor:
    """Redact sensitive information from logs and output."""
    
    # ANSI color code for pink text
    PINK = '\033[95m'
    RESET = '\033[0m'
    
    def __init__(self, enabled: bool = False, colorize: bool = False):
        """Initialize the redactor.
        
        Args:
            enabled: Whether redaction is enabled
            colorize: Whether to colorize redacted content in pink
        """
        self.enabled = enabled
        self.colorize = colorize
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns for redaction."""
        # Matrix room IDs: !roomid:server.com
        self.room_id_pattern = re.compile(r'![a-zA-Z0-9]+:[a-zA-Z0-9\.\-]+')
        
        # Matrix user IDs: @username:server.com (including URL-encoded characters like =40 for @)
        self.user_id_pattern = re.compile(r'@[a-zA-Z0-9\-_\.=]+:[a-zA-Z0-9\.\-]+')
        
        # IPv4 addresses - mask last 2 octets
        self.ipv4_pattern = re.compile(r'\b(\d{1,3}\.\d{1,3}\.)\d{1,3}\.\d{1,3}\b')
        
        # IPv6 addresses - mask last 4 groups
        # More specific pattern to avoid matching timestamps
        self.ipv6_pattern = re.compile(
            r'\b([0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}:)[0-9a-fA-F:]+\b'
        )
        
        # Hostnames/domains - mask middle parts (but not IP addresses)
        # This pattern requires at least one alphabetic character to avoid matching IPs
        self.hostname_pattern = re.compile(
            r'\b([a-zA-Z][-a-zA-Z0-9]*\.)([a-zA-Z0-9][-a-zA-Z0-9]*\.)+([a-zA-Z]{2,})\b'
        )
        
        # Access tokens (Bearer tokens, API tokens)
        self.token_pattern = re.compile(
            r'\b(token[=:\s]+|bearer\s+|authorization[=:\s]+bearer\s+)'
            r'[a-zA-Z0-9_\-\.]+',
            re.IGNORECASE
        )
        
        # Cryptographic sender keys (base64-like strings in sender_key field)
        self.sender_key_pattern = re.compile(
            r'(sender[_\s]?key[\'\":\s]+[\'\"]+)([A-Za-z0-9+/]{20,})[\.]*',
            re.IGNORECASE
        )
        
        # Session IDs and similar hex/base64 strings (alphanumeric strings 32+ chars)
        self.session_id_pattern = re.compile(r'\b[a-zA-Z0-9]{32,}')
        
        # Device IDs (Matrix device IDs in various contexts)
        self.device_id_pattern = re.compile(
            r'\bdevice[_\s]?id[\'\"=:\s]+[\'\"]*([A-Z0-9]{6,})',
            re.IGNORECASE
        )
        
        # SSH/TLS host keys and fingerprints
        self.hostkey_pattern = re.compile(
            r'\b(ssh-[a-z0-9]+\s+[A-Za-z0-9+/=]+|'
            r'[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){15,})\b'
        )
        
        # Passwords in URLs or parameters
        self.password_pattern = re.compile(
            r'(password[=:\s]+)[^\s&]+',
            re.IGNORECASE
        )
        
        # Cryptographic keys (ed25519, curve25519, etc.)
        self.crypto_key_pattern = re.compile(
            r'\b(ed25519|curve25519|olm_key|megolm_key)[\'\":\s]*[\'\"]*([A-Za-z0-9+/]{6,})[\'\"]*',
            re.IGNORECASE
        )
        
        # Matrix event IDs ($ followed by base64-like string)
        self.event_id_pattern = re.compile(r'\$[A-Za-z0-9+/]{10,}')
        
        # Matrix transaction IDs (alphanumeric strings starting with specific prefixes)
        self.transaction_id_pattern = re.compile(r'\b(t_[a-zA-Z0-9]{10,}|[a-zA-Z0-9]{20,}_[a-zA-Z0-9]{8,})\b')
        
        # Room keys and session data (base64 encoded)
        self.room_key_pattern = re.compile(
            r'\b(room_key|session_key|group_session)[\'\":\s]*[\'\"]*([A-Za-z0-9+/]{10,}=*)[\'\"]*',
            re.IGNORECASE
        )
        
        # One-time keys (base64 encoded arrays)
        self.one_time_key_pattern = re.compile(
            r'\b(one_time_key|otk)[\'\":\s]*\[\s*[\'\"]*[A-Za-z0-9+/=]{10,}[\'\"]*\s*\]',
            re.IGNORECASE
        )
        
        # Device key fingerprints (hex strings)
        self.fingerprint_pattern = re.compile(r'\b[fF]ingerprint[\'\":\s]*[\'\"]*([0-9a-fA-F]{64})[\'\"]*', re.IGNORECASE)
        
        # Matrix sync tokens (s followed by numbers)
        self.sync_token_pattern = re.compile(r'\bs\d+')
        
        # Base64 encoded data (long strings that look like base64)
        self.base64_data_pattern = re.compile(r'\b[A-Za-z0-9+/]{50,}=*\b')
    
    def _wrap_redacted(self, text: str) -> str:
        """Wrap redacted text with color if enabled.
        
        Args:
            text: The redacted placeholder text
            
        Returns:
            Colorized text if colorize is enabled, otherwise plain text
        """
        if self.colorize:
            return f'{self.PINK}{text}{self.RESET}'
        return text
    
    def redact(self, message: str) -> str:
        """Redact sensitive information from a message.
        
        Args:
            message: The message to redact
            
        Returns:
            Redacted message with sensitive info replaced
        """
        if not self.enabled or not message:
            return message
        
        # Redact tokens first (most sensitive)
        message = self.token_pattern.sub(
            lambda m: m.group(1) + self._wrap_redacted('[TOKEN_REDACTED]'),
            message
        )
        
        # Redact passwords
        message = self.password_pattern.sub(
            lambda m: m.group(1) + self._wrap_redacted('[PASSWORD_REDACTED]'),
            message
        )
        
        # Redact hostkeys and fingerprints
        message = self.hostkey_pattern.sub(
            self._wrap_redacted('[HOSTKEY_REDACTED]'),
            message
        )
        
        # Redact sender keys (before session IDs to be more specific)
        message = self.sender_key_pattern.sub(
            lambda m: m.group(1) + self._wrap_redacted('[SENDER_KEY_REDACTED]'),
            message
        )
        
        # Redact device IDs (before session IDs as device IDs might match session pattern)
        message = self.device_id_pattern.sub(
            lambda m: m.group(0)[:m.group(0).index(m.group(1))] + self._wrap_redacted('[DEVICE_ID_REDACTED]'),
            message
        )
        
        # Redact session IDs (after more specific patterns)
        message = self.session_id_pattern.sub(
            self._wrap_redacted('[SESSION_ID_REDACTED]'),
            message
        )
        
        # Redact cryptographic keys
        message = self.crypto_key_pattern.sub(
            lambda m: m.group(1) + self._wrap_redacted('[CRYPTO_KEY_REDACTED]'),
            message
        )
        
        # Redact event IDs
        message = self.event_id_pattern.sub(
            self._wrap_redacted('[EVENT_ID_REDACTED]'),
            message
        )
        
        # Redact transaction IDs
        message = self.transaction_id_pattern.sub(
            self._wrap_redacted('[TRANSACTION_ID_REDACTED]'),
            message
        )
        
        # Redact room keys and session data
        message = self.room_key_pattern.sub(
            lambda m: m.group(1) + self._wrap_redacted('[ROOM_KEY_REDACTED]'),
            message
        )
        
        # Redact one-time keys
        message = self.one_time_key_pattern.sub(
            lambda m: m.group(1) + self._wrap_redacted('[ONE_TIME_KEY_REDACTED]'),
            message
        )
        
        # Redact fingerprints
        message = self.fingerprint_pattern.sub(
            lambda m: m.group(1) + self._wrap_redacted('[FINGERPRINT_REDACTED]'),
            message
        )
        
        # Redact sync tokens
        message = self.sync_token_pattern.sub(
            self._wrap_redacted('[SYNC_TOKEN_REDACTED]'),
            message
        )
        
        # Redact long base64 data (be careful not to redact legitimate short strings)
        message = self.base64_data_pattern.sub(
            self._wrap_redacted('[BASE64_DATA_REDACTED]'),
            message
        )
        
        # Redact Matrix room IDs (before hostname pattern)
        message = self.room_id_pattern.sub(
            lambda m: self._wrap_redacted(f'![ROOM_ID]:{self._extract_domain(m.group())}'),
            message
        )
        
        # Redact Matrix user IDs (before hostname pattern)
        message = self.user_id_pattern.sub(
            lambda m: self._wrap_redacted(f'@[USER]:{self._extract_domain(m.group())}'),
            message
        )
        
        # Redact IPv4 addresses - keep first 2 octets (must be before hostname pattern)
        message = self.ipv4_pattern.sub(
            lambda m: m.group(1) + self._wrap_redacted('xxx.xxx'),
            message
        )
        
        # Redact IPv6 addresses - keep first 2 groups
        message = self.ipv6_pattern.sub(
            lambda m: m.group(1) + self._wrap_redacted('[IPV6_REDACTED]'),
            message
        )
        
        # Redact hostnames - keep first and last parts (but not if already redacted)
        # Skip if the domain part contains REDACTED markers
        def redact_hostname_if_needed(match):
            full_match = match.group(0)
            # Don't redact if it's already been processed (contains REDACTED markers)
            if 'REDACTED' in full_match or '[' in full_match:
                return full_match
            return match.group(1) + self._wrap_redacted('[DOMAIN]') + '.' + match.group(3)
        
        message = self.hostname_pattern.sub(redact_hostname_if_needed, message)
        
        return message
    
    def _extract_domain(self, identifier: str) -> str:
        """Extract domain from Matrix identifier.
        
        Args:
            identifier: Matrix room or user ID
            
        Returns:
            Domain with middle parts redacted
        """
        if ':' in identifier:
            domain = identifier.split(':', 1)[1]
            # Keep the TLD and partially redact the rest
            parts = domain.split('.')
            if len(parts) > 1:
                # Keep first part and TLD, redact middle
                if len(parts) == 2:
                    # For simple domains like "matrix.org", keep both parts
                    return domain
                else:
                    # For longer domains, redact middle parts
                    return parts[0] + '.' + self._wrap_redacted('[DOMAIN]') + '.' + parts[-1]
            return domain
        return self._wrap_redacted('[SERVER]')


class RedactingFilter(logging.Filter):
    """Logging filter that redacts sensitive information."""
    
    def __init__(self, redactor: SensitiveInfoRedactor):
        """Initialize the filter.
        
        Args:
            redactor: The redactor instance to use
        """
        super().__init__()
        self.redactor = redactor
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log record by redacting sensitive information.
        
        Args:
            record: The log record to filter
            
        Returns:
            Always True (we modify but don't filter out records)
        """
        if self.redactor.enabled:
            # Redact the message
            record.msg = self.redactor.redact(str(record.msg))
            
            # Redact args if present
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: self.redactor.redact(str(v)) if isinstance(v, str) else v
                        for k, v in record.args.items()
                    }
                elif isinstance(record.args, tuple):
                    record.args = tuple(
                        self.redactor.redact(str(arg)) if isinstance(arg, str) else arg
                        for arg in record.args
                    )
        
        return True
