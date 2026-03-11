"""Adds config flow for HANBD."""

from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers import selector
from slugify import slugify

from .api import (
    HanbdApiClient,
    HanbdApiClientAuthenticationError,
    HanbdApiClientCommunicationError,
    HanbdApiClientError,
)
from .const import DOMAIN, LOGGER

CONF_PHONE = "phone"


class HanbdFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for HANBD."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        return await self._async_handle_credentials_step(
            step_id="user",
            user_input=user_input,
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, str],
    ) -> config_entries.ConfigFlowResult:
        """Handle reauthentication when stored credentials are invalid."""
        await self.async_set_unique_id(unique_id=slugify(entry_data[CONF_PHONE]))
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Prompt the user to confirm updated credentials."""
        return await self._async_handle_credentials_step(
            step_id="reauth_confirm",
            user_input=user_input,
            existing_entry=self._get_reauth_entry(),
        )

    async def async_step_reconfigure(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle manual reconfiguration of credentials."""
        return await self._async_handle_credentials_step(
            step_id="reconfigure",
            user_input=user_input,
            existing_entry=self._get_reconfigure_entry(),
        )

    async def _async_handle_credentials_step(
        self,
        step_id: str,
        user_input: dict | None,
        existing_entry: config_entries.ConfigEntry | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Validate credentials and create or update the config entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    phone=user_input[CONF_PHONE],
                    password=user_input[CONF_PASSWORD],
                )
            except HanbdApiClientAuthenticationError as exception:
                LOGGER.error(exception)
                errors["base"] = "auth"
            except HanbdApiClientCommunicationError as exception:
                LOGGER.error(exception)
                errors["base"] = "connection"
            except HanbdApiClientError as exception:
                LOGGER.exception(exception)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    unique_id=slugify(user_input[CONF_PHONE])
                )
                if existing_entry is None:
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"HANBD ({user_input[CONF_PHONE]})",
                        data=user_input,
                    )

                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    existing_entry,
                    data_updates=user_input,
                )

        return self.async_show_form(
            step_id=step_id,
            data_schema=self._get_data_schema(user_input, existing_entry),
            errors=errors,
        )

    def _get_data_schema(
        self,
        user_input: dict | None,
        existing_entry: config_entries.ConfigEntry | None = None,
    ) -> vol.Schema:
        """Build the credentials form schema."""
        existing_data = existing_entry.data if existing_entry is not None else {}

        return vol.Schema(
            {
                vol.Required(
                    CONF_PHONE,
                    default=(
                        (user_input or {}).get(
                            CONF_PHONE,
                            existing_data.get(CONF_PHONE, vol.UNDEFINED),
                        )
                    ),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEL,
                    ),
                ),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.PASSWORD,
                    ),
                ),
            },
        )

    async def _test_credentials(self, phone: str, password: str) -> None:
        """Validate credentials."""
        connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
        async with aiohttp.ClientSession(connector=connector) as session:
            client = HanbdApiClient(
                phone=phone,
                password=password,
                session=session,
            )
            await client.async_authenticate()
