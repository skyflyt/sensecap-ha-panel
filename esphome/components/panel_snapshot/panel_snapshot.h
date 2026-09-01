#pragma once

#include "esphome/core/component.h"

#include <esp_http_server.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <lvgl.h>

namespace esphome {
namespace panel_snapshot {

/// Serves the live screen as an RGB565 BMP at /screenshot.
///
/// Pixel source: ESPHome's LVGL build is a trimmed managed component with
/// the snapshot module's sources removed, so lv_snapshot_take() cannot link.
/// Instead we chain the display's flush callback and mirror every flushed
/// area into a shadow framebuffer in PSRAM — public LVGL9 API only, no
/// display-driver internals.
///
/// Thread model: flush + loop() both run on ESPHome's main thread, so the
/// shadow is only ever written there. The httpd handler raises `want_`,
/// loop() copies shadow -> out under main-thread coherence and signals; the
/// handler streams `out_`. One request at a time.
class PanelSnapshot : public Component {
 public:
  void set_port(uint16_t port) { this->port_ = port; }
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::LATE; }

  // shared state (single instance; the flush tap uses a global)
  volatile bool want_{false};
  volatile bool ready_{false};
  uint8_t *shadow_{nullptr};
  uint8_t *out_{nullptr};
  int32_t hor_{0}, ver_{0};
  SemaphoreHandle_t done_{nullptr};
  volatile bool busy_{false};
  lv_display_flush_cb_t orig_flush_{nullptr};

  // virtual touch (remote control): /tap?x=&y= presses here via a second
  // LVGL pointer indev. Press duration is counted in READS, not
  // milliseconds: a time window can slide past unseen when the main loop is
  // busy (e.g. mid-screenshot-copy), which was the "sometimes my tap doesn't
  // register" bug — LVGL never sampled the pressed state. A read count
  // guarantees the press is seen however starved the indev timer gets.
  // Tap-only on purpose — anything guarded by a long-press on the physical
  // panel stays physically-present-only.
  volatile int32_t tap_x_{0}, tap_y_{0};
  volatile int32_t tap_reads_{0};
  lv_indev_t *vindev_{nullptr};

 protected:
  uint16_t port_{8080};
  httpd_handle_t server_{nullptr};
};

}  // namespace panel_snapshot
}  // namespace esphome
