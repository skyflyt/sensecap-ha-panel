// desk_pet_helpers.h — parsing helpers for the desk pet.
//
// Deploy next to your device YAML (on a Home Assistant ESPHome add-on install
// that is /homeassistant/esphome/) and reference it from:
//
//   esphome:
//     includes:
//       - desk_pet_helpers.h
//
// Home Assistant publishes the pet's whole state as ONE string sensor in a
// `key=value;` encoding:
//
//   xp=418;lvl=3;pct=41;hun=12;rdy=0;stg=2;nxt=585;spi=88;on=1
//
// One subscription instead of nine. The panel pays a fixed cost per subscribed
// entity (RAM, and an API round trip on every push), and nine slow-moving
// numbers that always change together are one fact, not nine. The parse is
// identical everywhere and only the key differs, so it lives here rather than
// being repeated inside forty lambdas.

#pragma once

#include <string>
#include "esphome/core/helpers.h"

// Signed integer field. Returns `fallback` when the key is absent.
//
// The `-` handling is not decoration: a field that can legitimately be
// negative (a countdown to a meeting already under way, say) will be read as
// "absent" by a digits-only parser, and the panel then shows a stale value
// forever instead of an obviously wrong one. Absent and zero must stay
// distinguishable, which is why the caller supplies the fallback.
inline int indicator_state_int(const std::string &encoded, const char *key, int fallback) {
  const std::string needle = std::string(key) + "=";
  size_t at = encoded.find(needle);
  if (at == std::string::npos)
    return fallback;
  at += needle.size();
  bool negative = false;
  if (at < encoded.size() && encoded[at] == '-') {
    negative = true;
    at++;
  }
  int value = 0;
  bool any = false;
  while (at < encoded.size() && encoded[at] >= '0' && encoded[at] <= '9') {
    value = value * 10 + (encoded[at] - '0');
    any = true;
    at++;
  }
  if (!any)
    return fallback;
  return negative ? -value : value;
}

// Text field, up to the next ';' or the end of the string.
inline std::string indicator_state_text(const std::string &encoded, const char *key) {
  const std::string needle = std::string(key) + "=";
  size_t at = encoded.find(needle);
  if (at == std::string::npos)
    return std::string();
  at += needle.size();
  size_t end = encoded.find(';', at);
  return (end == std::string::npos) ? encoded.substr(at) : encoded.substr(at, end - at);
}
