#include "panel_snapshot.h"

#include "esphome/core/log.h"

#include <esp_heap_caps.h>
#include <cstring>

// This LVGL build has lv_display_set_flush_cb but no getter, and we must
// chain the original. The private header ships in the managed component and
// exposes the member (verified: src/display/lv_display_private.h:78).
#include <src/display/lv_display_private.h>

namespace esphome {
namespace panel_snapshot {

static const char *const TAG = "panel_snapshot";
static PanelSnapshot *g_self = nullptr;

// Mirror every flushed area into the shadow framebuffer, then hand off to
// the real flush. Runs on ESPHome's main thread (the only LVGL thread).
static void flush_tap(lv_display_t *disp, const lv_area_t *area,
                      uint8_t *px_map) {
  PanelSnapshot *s = g_self;
  if (s != nullptr && s->shadow_ != nullptr) {
    const int32_t aw = area->x2 - area->x1 + 1;
    for (int32_t y = area->y1; y <= area->y2; y++) {
      if (y < 0 || y >= s->ver_)
        continue;
      memcpy(s->shadow_ + ((size_t) y * s->hor_ + area->x1) * 2,
             px_map + ((size_t) (y - area->y1) * aw) * 2, (size_t) aw * 2);
    }
  }
  if (s != nullptr && s->orig_flush_ != nullptr)
    s->orig_flush_(disp, area, px_map);
}

// 66-byte BMP header: BITMAPINFOHEADER + BI_BITFIELDS masks, 16bpp RGB565,
// negative height = top-down rows (matches the shadow buffer directly).
static void build_bmp_header(uint8_t *h, int32_t w, int32_t hgt,
                             uint32_t img_bytes) {
  auto p32 = [&](int off, uint32_t v) {
    h[off] = v & 0xFF;
    h[off + 1] = (v >> 8) & 0xFF;
    h[off + 2] = (v >> 16) & 0xFF;
    h[off + 3] = (v >> 24) & 0xFF;
  };
  auto p16 = [&](int off, uint16_t v) {
    h[off] = v & 0xFF;
    h[off + 1] = (v >> 8) & 0xFF;
  };
  memset(h, 0, 66);
  h[0] = 'B';
  h[1] = 'M';
  p32(2, 66 + img_bytes);
  p32(10, 66);
  p32(14, 40);              // BITMAPINFOHEADER; masks follow (BI_BITFIELDS)
  p32(18, (uint32_t) w);
  p32(22, (uint32_t) (-hgt));  // top-down
  p16(26, 1);
  p16(28, 16);
  p32(30, 3);               // BI_BITFIELDS
  p32(34, img_bytes);
  p32(38, 2835);
  p32(42, 2835);
  p32(54, 0xF800);
  p32(58, 0x07E0);
  p32(62, 0x001F);
}

// The virtual finger. Runs in LVGL context (indev timer on the main loop);
// the httpd task only writes the aligned-int target/deadline, which is
// atomic on Xtensa.
static void vtouch_read(lv_indev_t *indev, lv_indev_data_t *data) {
  PanelSnapshot *s = g_self;
  data->point.x = s->tap_x_;
  data->point.y = s->tap_y_;
  if (s->tap_reads_ > 0) {
    data->state = LV_INDEV_STATE_PRESSED;
    s->tap_reads_ = s->tap_reads_ - 1;
  } else {
    data->state = LV_INDEV_STATE_RELEASED;
  }
}

// /view — a self-contained remote-control page: the screenshot refreshing
// itself, and every click/touch forwarded to /tap at panel coordinates.
static const char VIEW_HTML[] = R"HTML(<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Office Indicator</title>
<style>
 body{margin:0;background:#14161A;color:#9AA0A6;font:14px sans-serif;
      display:flex;flex-direction:column;align-items:center;gap:8px;
      padding:12px}
 #s{width:min(96vw,480px);aspect-ratio:1;image-rendering:pixelated;
    border:1px solid #2A2F37;border-radius:8px;cursor:crosshair;
    touch-action:manipulation}
 #m{min-height:1em}
</style></head><body>
<img id="s" alt="panel">
<div id="m">live &middot; click or tap the image to touch the panel</div>
<script>
 const img=document.getElementById('s'),msg=document.getElementById('m');
 let busy=false;
 function refresh(){
   if(busy)return;
   const n=new Image();
   n.onload=()=>{img.src=n.src;};
   n.src='/screenshot?t='+Date.now();
 }
 setInterval(refresh,1500);
 refresh();
 img.addEventListener('click',async e=>{
   const r=img.getBoundingClientRect();
   const x=Math.round((e.clientX-r.left)*480/r.width);
   const y=Math.round((e.clientY-r.top)*480/r.height);
   busy=true;
   msg.textContent='tap '+x+','+y+' ...';
   try{await fetch('/tap?x='+x+'&y='+y);}catch(_){}
   setTimeout(()=>{busy=false;refresh();
     msg.textContent='live · click or tap the image to touch the panel';
   },400);
 });
</script></body></html>)HTML";

static esp_err_t view_handler(httpd_req_t *req) {
  httpd_resp_set_type(req, "text/html");
  httpd_resp_send(req, VIEW_HTML, HTTPD_RESP_USE_STRLEN);
  return ESP_OK;
}

static esp_err_t tap_handler(httpd_req_t *req) {
  auto *self = static_cast<PanelSnapshot *>(req->user_ctx);
  char query[64] = {0};
  char val[12] = {0};
  int32_t x = -1, y = -1;
  if (httpd_req_get_url_query_str(req, query, sizeof(query)) == ESP_OK) {
    if (httpd_query_key_value(query, "x", val, sizeof(val)) == ESP_OK)
      x = atoi(val);
    if (httpd_query_key_value(query, "y", val, sizeof(val)) == ESP_OK)
      y = atoi(val);
  }
  if (x < 0 || y < 0 || x >= self->hor_ || y >= self->ver_) {
    httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "need x=0..479&y=0..479");
    return ESP_FAIL;
  }
  self->tap_x_ = x;
  self->tap_y_ = y;
  self->tap_reads_ = 3;  // three guaranteed pressed samples, then release
  httpd_resp_set_type(req, "text/plain");
  httpd_resp_sendstr(req, "tapped");
  return ESP_OK;
}

static esp_err_t screenshot_handler(httpd_req_t *req) {
  auto *self = static_cast<PanelSnapshot *>(req->user_ctx);
  if (self->busy_ || self->out_ == nullptr) {
    httpd_resp_send_err(req, HTTPD_500_INTERNAL_SERVER_ERROR, "busy");
    return ESP_FAIL;
  }
  self->busy_ = true;
  self->ready_ = false;
  self->want_ = true;
  if (xSemaphoreTake(self->done_, pdMS_TO_TICKS(5000)) != pdTRUE ||
      !self->ready_) {
    self->want_ = false;
    self->busy_ = false;
    httpd_resp_send_err(req, HTTPD_500_INTERNAL_SERVER_ERROR,
                        "snapshot timed out");
    return ESP_FAIL;
  }
  const int32_t w = self->hor_, hgt = self->ver_;
  const uint32_t row_bytes = (uint32_t) w * 2;
  uint8_t hdr[66];
  build_bmp_header(hdr, w, hgt, row_bytes * hgt);
  httpd_resp_set_type(req, "image/bmp");
  esp_err_t err = httpd_resp_send_chunk(req, (const char *) hdr, 66);
  for (int32_t y = 0; y < hgt && err == ESP_OK; y++) {
    err = httpd_resp_send_chunk(
        req, (const char *) (self->out_ + (size_t) y * row_bytes), row_bytes);
  }
  if (err == ESP_OK)
    httpd_resp_send_chunk(req, nullptr, 0);
  self->busy_ = false;
  return err;
}

void PanelSnapshot::setup() {
  lv_display_t *disp = lv_display_get_default();
  if (disp == nullptr) {
    ESP_LOGE(TAG, "no LVGL display; is lvgl set up before %s?", TAG);
    this->mark_failed();
    return;
  }
  this->hor_ = lv_display_get_horizontal_resolution(disp);
  this->ver_ = lv_display_get_vertical_resolution(disp);
  const size_t fb_bytes = (size_t) this->hor_ * this->ver_ * 2;
  this->shadow_ = (uint8_t *) heap_caps_malloc(fb_bytes, MALLOC_CAP_SPIRAM);
  this->out_ = (uint8_t *) heap_caps_malloc(fb_bytes, MALLOC_CAP_SPIRAM);
  if (this->shadow_ == nullptr || this->out_ == nullptr) {
    ESP_LOGE(TAG, "PSRAM alloc failed (%u bytes x2)", (unsigned) fb_bytes);
    this->mark_failed();
    return;
  }
  memset(this->shadow_, 0, fb_bytes);
  this->done_ = xSemaphoreCreateBinary();
  g_self = this;
  this->orig_flush_ = disp->flush_cb;   // via lv_display_private.h
  lv_display_set_flush_cb(disp, flush_tap);
  // force one full repaint so the shadow starts complete
  lv_obj_invalidate(lv_screen_active());

  httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
  cfg.server_port = this->port_;
  cfg.ctrl_port = this->port_ + 1;
  cfg.stack_size = 6144;
  if (httpd_start(&this->server_, &cfg) != ESP_OK) {
    ESP_LOGE(TAG, "httpd_start failed on port %u", this->port_);
    this->mark_failed();
    return;
  }
  httpd_uri_t uri = {
      .uri = "/screenshot",
      .method = HTTP_GET,
      .handler = screenshot_handler,
      .user_ctx = this,
  };
  httpd_register_uri_handler(this->server_, &uri);
  httpd_uri_t tap_uri = {
      .uri = "/tap",
      .method = HTTP_GET,
      .handler = tap_handler,
      .user_ctx = this,
  };
  httpd_register_uri_handler(this->server_, &tap_uri);
  httpd_uri_t view_uri = {
      .uri = "/view",
      .method = HTTP_GET,
      .handler = view_handler,
      .user_ctx = this,
  };
  httpd_register_uri_handler(this->server_, &view_uri);

  // virtual pointer — a second touchscreen LVGL polls like the real one
  this->vindev_ = lv_indev_create();
  lv_indev_set_type(this->vindev_, LV_INDEV_TYPE_POINTER);
  lv_indev_set_read_cb(this->vindev_, vtouch_read);
  lv_indev_set_display(this->vindev_, disp);

  ESP_LOGI(TAG, "serving /screenshot and /tap on port %u (%dx%d)",
           this->port_, (int) this->hor_, (int) this->ver_);
}

void PanelSnapshot::loop() {
  if (!this->want_)
    return;
  this->want_ = false;
  // main thread: coherent with flush_tap by construction. Swap bytes while
  // copying — the display pipeline runs RGB565 big-endian per pixel, BMP
  // wants little-endian (first capture came out pink-on-cyan; the swap was
  // diagnosed from the picture itself, which is rather the point of this
  // component).
  const uint16_t *src = (const uint16_t *) this->shadow_;
  uint16_t *dst = (uint16_t *) this->out_;
  const size_t n = (size_t) this->hor_ * this->ver_;
  for (size_t i = 0; i < n; i++)
    dst[i] = __builtin_bswap16(src[i]);
  this->ready_ = true;
  xSemaphoreGive(this->done_);
}

void PanelSnapshot::dump_config() {
  ESP_LOGCONFIG(TAG, "Panel snapshot: http://<ip>:%u/screenshot", this->port_);
}

}  // namespace panel_snapshot
}  // namespace esphome
