"""Tests for Livebox custom services."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.livebox.const import DOMAIN


@pytest.mark.parametrize("AIOSysbus", ["7"], indirect=True)
async def test_service_add_static_dhcp(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    AIOSysbus: AsyncMock,
):
    """Test the add_static_dhcp service."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "add_static_dhcp",
        {"mac_address": "AA:BB:CC:DD:EE:FF", "ip_address": "192.168.1.100"},
        blocking=True,
    )

    AIOSysbus.dhcp.async_set_dhcp_staticlease.assert_called_once_with(
        {"MACAddress": "AA:BB:CC:DD:EE:FF", "IPAddress": "192.168.1.100"}
    )


@pytest.mark.parametrize("AIOSysbus", ["7"], indirect=True)
async def test_service_remove_static_dhcp(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    AIOSysbus: AsyncMock,
):
    """Test the remove_static_dhcp service."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "remove_static_dhcp",
        {"mac_address": "AA:BB:CC:DD:EE:FF"},
        blocking=True,
    )

    AIOSysbus.dhcp.async_del_dhcp_staticlease.assert_called_once_with(
        {"MACAddress": "AA:BB:CC:DD:EE:FF"}
    )


@pytest.mark.parametrize("AIOSysbus", ["7"], indirect=True)
async def test_service_add_port_forwarding(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    AIOSysbus: AsyncMock,
):
    """Test the add_port_forwarding service."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "add_port_forwarding",
        {
            "description": "Web Server",
            "destination_ip_address": "192.168.1.100",
            "internal_port": 8080,
            "external_port": 80,
            "protocol": "tcp",
            "enable": True,
        },
        blocking=True,
    )

    AIOSysbus.firewall.async_set_port_forwarding.assert_called_once_with(
        {
            "id": "Web Server",
            "description": "Web Server",
            "persistent": True,
            "enable": True,
            "protocol": "6",
            "destinationIPAddress": "192.168.1.100",
            "internalPort": 8080,
            "externalPort": 80,
            "origin": "webui",
            "sourceInterface": "data",
            "sourcePrefix": "",
        }
    )


@pytest.mark.parametrize("AIOSysbus", ["7"], indirect=True)
async def test_service_remove_port_forwarding(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    AIOSysbus: AsyncMock,
):
    """Test the remove_port_forwarding service."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "remove_port_forwarding",
        {"id": "Web Server", "destination_ip_address": "192.168.1.100"},
        blocking=True,
    )

    AIOSysbus.firewall.async_delete_port_forwarding.assert_called_once_with(
        {
            "id": "Web Server",
            "origin": "webui",
            "destinationIPAddress": "192.168.1.100",
        }
    )


@pytest.mark.parametrize("AIOSysbus", ["7"], indirect=True)
async def test_service_rename_device(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    AIOSysbus: AsyncMock,
):
    """Test the rename_device service."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "rename_device",
        {"mac_address": "AA:BB:CC:DD:EE:FF", "name": "Living Room TV"},
        blocking=True,
    )

    AIOSysbus.devices.async_set_name.assert_called_once_with(
        {"key": "AA:BB:CC:DD:EE:FF", "name": "Living Room TV"}
    )
