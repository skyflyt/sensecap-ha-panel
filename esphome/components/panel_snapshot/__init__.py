"""panel_snapshot — serve the live LVGL screen as a BMP over HTTP.

GET http://<panel>:<port>/screenshot returns the active screen, 480x480
RGB565 BMP. Built as the ground-truth post-OTA verification after the
2026-08-31 silent-rollback incident: the only proof a UI change is running
is the pixels themselves.
"""
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_PORT

DEPENDENCIES = ["lvgl"]

panel_snapshot_ns = cg.esphome_ns.namespace("panel_snapshot")
PanelSnapshot = panel_snapshot_ns.class_("PanelSnapshot", cg.Component)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(PanelSnapshot),
        cv.Optional(CONF_PORT, default=8080): cv.port,
    }
).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    cg.add(var.set_port(config[CONF_PORT]))
