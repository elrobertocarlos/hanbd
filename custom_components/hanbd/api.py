"""HANBD API Client."""

from __future__ import annotations

import base64
import binascii
import json
import socket
import time
from typing import Any, cast

import aiohttp
import async_timeout
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    APP_PUBLIC_KEY,
    ENDPOINT_AUTHORIZE,
    ENDPOINT_DEVICE_LIST,
    ENDPOINT_DEVICE_OPERATE,
    LOGGER,
)


class HanbdApiClientError(Exception):
    """Exception to indicate a general API error."""


class HanbdApiClientCommunicationError(
    HanbdApiClientError,
):
    """Exception to indicate a communication error."""


class HanbdApiClientAuthenticationError(
    HanbdApiClientError,
):
    """Exception to indicate an authentication error."""


class HanbdApiClientDeviceBusyError(
    HanbdApiClientError,
):
    """Exception to indicate device is busy performing another operation."""


SENSITIVE_KEYS = {
    "authorization",
    "access_token",
    "refresh_token",
    "credential",
    "password",
}


def _is_auth_error_response(response: dict[str, Any]) -> bool:
    """Check if API response indicates an authentication error."""
    if not response.get("success"):
        msg = response.get("msg", "").lower()
        # Check for session/login expiration messages
        return any(
            auth_phrase in msg
            for auth_phrase in [
                "login is no longer valid",
                "unauthorized",
                "token expired",
                "access denied",
            ]
        )
    return False


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""

    def _raise_auth_error(msg: str) -> None:
        raise HanbdApiClientAuthenticationError(msg)

    if response.status in (401, 403):
        msg = "Invalid credentials"
        _raise_auth_error(msg)
    response.raise_for_status()


class HanbdApiClient:
    """HANBD API Client."""

    def __init__(
        self,
        phone: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize HANBD API Client."""
        self._phone = phone
        self._password = password
        self._session = session
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: float | None = None
        self._base_url = API_BASE_URL

    async def async_authenticate(self) -> None:
        """Authenticate with the HANBD API and get tokens."""

        def _raise_authentication_error(msg: str) -> None:
            raise HanbdApiClientAuthenticationError(msg)

        url = f"{self._base_url}{ENDPOINT_AUTHORIZE}"

        encrypted_credential = self._encrypt_credential(self._password)

        payload = {
            "identifier": self._phone,
            "credential": encrypted_credential,
            "code": "",
            "jpushRegistrationid": "",
        }

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json;versions=1;character=utf-8",
            "platform": "Android",
            "version": "1.1.2",
        }

        try:
            response = await self._api_wrapper(
                method="post",
                url=url,
                data=payload,
                headers=headers,
            )

            if response.get("success"):
                data = response.get("data", {})
                self._access_token = data.get("access_token")
                self._refresh_token = data.get("refresh_token")

                # Store token expiry time (expires_in is in seconds)
                expires_in = data.get("expires_in", 3600)  # Default 1 hour
                self._token_expires_at = time.time() + expires_in

                if not self._access_token:
                    msg = "No access token returned"
                    _raise_authentication_error(msg)

                return

            msg = response.get("msg", "Authentication failed")
            _raise_authentication_error(msg)

        except HanbdApiClientAuthenticationError:
            raise
        except Exception as exception:
            msg = f"Authentication error - {exception}"
            raise HanbdApiClientAuthenticationError(msg) from exception

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Get list of devices from the API."""
        # Check if token is expired or about to expire
        if self._is_token_expired():
            LOGGER.debug("Access token expired or expiring soon, re-authenticating")
            await self.async_authenticate()

        url = f"{self._base_url}{ENDPOINT_DEVICE_LIST}"
        headers = self._get_auth_headers()

        try:
            response = await self._api_wrapper(
                method="post",
                url=url,
                data={},
                headers=headers,
            )

            if not response.get("success"):
                msg = response.get("msg", "Failed to get devices")
                # Determine which exception to raise
                error_class = (
                    HanbdApiClientAuthenticationError
                    if _is_auth_error_response(response)
                    else HanbdApiClientError
                )
                raise error_class(msg) from None

            devices = response.get("data", [])
            return devices if isinstance(devices, list) else []

        except HanbdApiClientAuthenticationError:
            # Try to re-authenticate and retry once
            LOGGER.debug("Token expired, re-authenticating")
            await self.async_authenticate()
            headers = self._get_auth_headers()
            response = await self._api_wrapper(
                method="post",
                url=url,
                data={},
                headers=headers,
            )
            if not response.get("success"):
                msg = response.get("msg", "Failed to get devices after re-auth")
                raise HanbdApiClientError(msg) from None

            devices = response.get("data", [])
            return devices if isinstance(devices, list) else []

    async def async_operate_device(
        self,
        device_id: str,
        operation_type: str,
        is_enforce: str = "",
    ) -> dict[str, Any]:
        """Send a device operation command to the HANBD API."""
        # Check if token is expired or about to expire
        if self._is_token_expired():
            LOGGER.debug("Access token expired or expiring soon, re-authenticating")
            await self.async_authenticate()

        if not self._access_token:
            await self.async_authenticate()

        url = f"{self._base_url}{ENDPOINT_DEVICE_OPERATE}"
        headers = self._get_auth_headers()
        payload = {
            "deviceId": device_id,
            "type": operation_type,
            "isEnforce": is_enforce,
        }

        try:
            response = await self._api_wrapper(
                method="post",
                url=url,
                data=payload,
                headers=headers,
            )
        except HanbdApiClientAuthenticationError:
            LOGGER.debug("Token expired during operate call, re-authenticating")
            await self.async_authenticate()
            headers = self._get_auth_headers()
            response = await self._api_wrapper(
                method="post",
                url=url,
                data=payload,
                headers=headers,
            )

        if not response.get("success"):
            msg = response.get("msg", "Device operation failed")
            # Check if this is an auth error and trigger token renewal
            if _is_auth_error_response(response):
                raise HanbdApiClientAuthenticationError(msg)
            # Check if device is busy (common error messages)
            if any(
                busy_msg in msg.lower()
                for busy_msg in [
                    "cleaning",
                    "busy",
                    "running",
                    "in use",
                    "device is",
                ]
            ):
                msg = f"Device is busy: {msg}"
                raise HanbdApiClientDeviceBusyError(msg)
            raise HanbdApiClientError(msg)

        return response

    def _get_auth_headers(self) -> dict[str, str]:
        """Get headers with authentication token."""
        return {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json;versions=1;character=utf-8",
            "Authorization": f"bearer{self._access_token}",
            "platform": "Android",
            "version": "1.1.2",
        }

    def _is_token_expired(self) -> bool:
        """
        Check if access token has expired.

        Returns True if token is expired or about to expire (within 5 minutes).
        """
        if self._token_expires_at is None:
            return False
        # Refresh if expiry is within 5 minutes
        return time.time() >= (self._token_expires_at - 300)

    def _encrypt_credential(self, plain_password: str) -> str:
        """Encrypt password like the Android app (RSA/ECB/PKCS1Padding + Base64)."""

        def _raise_authentication_error(message: str) -> None:
            raise HanbdApiClientAuthenticationError(message)

        try:
            key_der = base64.b64decode(APP_PUBLIC_KEY)
            public_key = serialization.load_der_public_key(key_der)
            if not isinstance(public_key, rsa.RSAPublicKey):
                msg = "Failed to encrypt credential: unsupported public key type"
                _raise_authentication_error(msg)
            rsa_public_key = cast("rsa.RSAPublicKey", public_key)
            encrypted = rsa_public_key.encrypt(
                plain_password.encode("utf-8"),
                padding.PKCS1v15(),
            )
            return base64.b64encode(encrypted).decode("ascii")
        except HanbdApiClientAuthenticationError:
            raise
        except (
            ValueError,
            TypeError,
            binascii.Error,
            UnsupportedAlgorithm,
        ) as exception:
            msg = f"Failed to encrypt credential: {exception}"
            raise HanbdApiClientAuthenticationError(msg) from exception

    async def async_get_data(self) -> Any:
        """Get data from the API (legacy method for compatibility)."""
        devices = await self.async_get_devices()
        return {"devices": devices}

    async def async_set_title(self, _value: str) -> Any:
        """Legacy method for compatibility."""
        # This method is kept for compatibility
        # It doesn't do anything useful for HANBD
        return {"success": True}

    async def async_close(self) -> None:
        """Close the underlying HTTP session if still open."""
        if not self._session.closed:
            await self._session.close()

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        safe_headers = self._redact_mapping(headers or {})
        safe_data = self._redact_mapping(data or {})
        LOGGER.debug(
            "HANBD HTTP request: method=%s url=%s headers=%s json=%s",
            method.upper(),
            url,
            safe_headers,
            safe_data,
        )

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                response_text = await response.text()
                safe_body = self._redact_text_body(response_text)
                LOGGER.debug(
                    "HANBD HTTP response: method=%s url=%s status=%s body=%s",
                    method.upper(),
                    url,
                    response.status,
                    safe_body,
                )
                _verify_response_or_raise(response)
                return json.loads(response_text)

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise HanbdApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise HanbdApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise HanbdApiClientError(
                msg,
            ) from exception

    def _redact_mapping(self, value: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive keys in a dictionary for safe debug logging."""
        safe: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_KEYS:
                safe[key] = "***"
            else:
                safe[key] = item
        return safe

    def _redact_text_body(self, body: str) -> str:
        """Redact known sensitive JSON fields and keep body concise for logs."""
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                redacted = self._redact_mapping(parsed)
                return json.dumps(redacted, ensure_ascii=True)[:1200]
        except ValueError:
            pass
        return body[:1200]
