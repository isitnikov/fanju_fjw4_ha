from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FanJuApi, FanJuAuthError
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD


class FanJuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = FanJuApi(
                session,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            try:
                await api.ensure_token()
            except FanJuAuthError:
                errors["base"] = "auth_failed"
            except Exception:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="FanJu FJW4 Weather Station",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
