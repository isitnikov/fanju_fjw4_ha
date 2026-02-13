from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FanJuApi, FanJuAuthError, FanJuApiError


class FanJuCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: FanJuApi, interval_s: int) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name="FanJu FJW4",
            update_interval=timedelta(seconds=interval_s),
        )
        self.api = api
        self.device: dict[str, Any] | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            # Можна разово підняти bound device, але хай буде тут без фанатизму
            if self.device is None:
                self.device = (await self.api.get_bound_device()).get("content")
            realtime = await self.api.get_realtime()
            return {
                "device": self.device,
                "realtime": realtime.get("content") or {},
            }
        except (FanJuAuthError, FanJuApiError) as e:
            raise UpdateFailed(str(e)) from e
        except Exception as e:
            raise UpdateFailed(f"Unexpected error: {e}") from e
