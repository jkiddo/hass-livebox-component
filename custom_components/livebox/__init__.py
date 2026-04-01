"""SoftAtHome Gateway integration."""

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CALLID, DOMAIN, PLATFORMS
from .coordinator import LiveboxDataUpdateCoordinator

type LiveboxConfigEntry = ConfigEntry[LiveboxDataUpdateCoordinator]

CALLMISSED_SCHEMA = vol.Schema({vol.Optional(CALLID): str})

STATIC_DHCP_ADD_SCHEMA = vol.Schema(
    {
        vol.Required("mac_address"): str,
        vol.Required("ip_address"): str,
    }
)

STATIC_DHCP_REMOVE_SCHEMA = vol.Schema(
    {
        vol.Required("mac_address"): str,
    }
)

PORT_FORWARDING_ADD_SCHEMA = vol.Schema(
    {
        vol.Required("description"): str,
        vol.Required("destination_ip_address"): str,
        vol.Required("internal_port"): vol.Coerce(int),
        vol.Required("external_port"): vol.Coerce(int),
        vol.Optional("protocol", default="tcp"): vol.In(["tcp", "udp", "both"]),
        vol.Optional("enable", default=True): bool,
    }
)

PORT_FORWARDING_REMOVE_SCHEMA = vol.Schema(
    {
        vol.Required("id"): str,
        vol.Required("destination_ip_address"): str,
    }
)

RENAME_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required("mac_address"): str,
        vol.Required("name"): str,
    }
)

PROTOCOL_MAP = {"tcp": "6", "udp": "17", "both": "6,17"}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: LiveboxConfigEntry) -> bool:
    """Set up SoftAtHome Gateway as config entry."""
    coordinator = LiveboxDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_remove_cmissed(call) -> None:
        await coordinator.api.voiceservice.async_clear_calllist(
            {CALLID: call.data.get(CALLID)}
        )
        await coordinator.async_refresh()

    async def async_add_static_dhcp(call) -> None:
        await coordinator.api.dhcp.async_set_dhcp_staticlease(
            {
                "MACAddress": call.data["mac_address"],
                "IPAddress": call.data["ip_address"],
            }
        )
        await coordinator.async_refresh()

    async def async_remove_static_dhcp(call) -> None:
        await coordinator.api.dhcp.async_del_dhcp_staticlease(
            {"MACAddress": call.data["mac_address"]}
        )
        await coordinator.async_refresh()

    async def async_add_port_forwarding(call) -> None:
        await coordinator.api.firewall.async_set_port_forwarding(
            {
                "id": call.data["description"],
                "description": call.data["description"],
                "persistent": True,
                "enable": call.data["enable"],
                "protocol": PROTOCOL_MAP[call.data["protocol"]],
                "destinationIPAddress": call.data["destination_ip_address"],
                "internalPort": call.data["internal_port"],
                "externalPort": call.data["external_port"],
                "origin": "webui",
                "sourceInterface": "data",
                "sourcePrefix": "",
            }
        )
        await coordinator.async_refresh()

    async def async_remove_port_forwarding(call) -> None:
        await coordinator.api.firewall.async_delete_port_forwarding(
            {
                "id": call.data["id"],
                "origin": "webui",
                "destinationIPAddress": call.data["destination_ip_address"],
            }
        )
        await coordinator.async_refresh()

    async def async_rename_device(call) -> None:
        await coordinator.api.devices.async_set_name(
            {"key": call.data["mac_address"], "name": call.data["name"]}
        )
        await coordinator.async_refresh()

    hass.services.async_register(
        DOMAIN, "remove_call_missed", async_remove_cmissed, schema=CALLMISSED_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "add_static_dhcp", async_add_static_dhcp, schema=STATIC_DHCP_ADD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        "remove_static_dhcp",
        async_remove_static_dhcp,
        schema=STATIC_DHCP_REMOVE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "add_port_forwarding",
        async_add_port_forwarding,
        schema=PORT_FORWARDING_ADD_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "remove_port_forwarding",
        async_remove_port_forwarding,
        schema=PORT_FORWARDING_REMOVE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, "rename_device", async_rename_device, schema=RENAME_DEVICE_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: LiveboxConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: LiveboxConfigEntry):
    """Reload device tracker if change option."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove config entry from a device."""
    return True
