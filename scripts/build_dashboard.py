#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the 3-tab dashboard (Agronomic Assessment | Bunch Development | Yield Map).

WC1 tab (REAL): markers by assessment type, ESTATE + MONTH dropdowns, type
toggles, and a frame IMAGE popup (loaded from frame_relpath).
Bunch / Yield tabs: MOCK placeholder data, banner-flagged.

Keep the output HTML in the dashboard project root so frame_relpath
(e.g. data/Serdang/DJI_..._D/frame_00001.jpg) resolves.

Login-free static snapshot — for the login-gated live version, run
app/app.py instead.

    pip install pandas openpyxl
    python scripts/build_dashboard.py
"""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core import dashboard_data as dd

# --------------------------------------------------------------------------- #
OUTPUT_HTML = os.path.join(PROJECT_ROOT, "wc1_dashboard.html")   # project root
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
# --------------------------------------------------------------------------- #


def main():
    if not API_KEY:
        print("WARNING: GOOGLE_MAPS_API_KEY is not set — set it in .env "
              "(see .env.example) or the map won't load.")
    wc1, counts, estates, months, center = dd.load_wc1()
    html = (TEMPLATE
            .replace("__API_KEY__", API_KEY)
            .replace("__WC1_MARKERS__", json.dumps(wc1))
            .replace("__WC1_COLORS__", json.dumps(dd.WC1_COLORS))
            .replace("__WC1_COUNTS__", json.dumps(counts))
            .replace("__ESTATES__", json.dumps(estates))
            .replace("__MONTHS__", json.dumps(months))
            .replace("__BUNCH_MARKERS__", json.dumps(dd.mock_bunch(center)))
            .replace("__YIELD_MARKERS__", json.dumps(dd.mock_yield(center)))
            .replace("__CENTER__", json.dumps(center)))
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUTPUT_HTML}")
    print(f"  WC1 (real): {len(wc1)} markers | estates={estates} | months={months}")
    for t, n in counts.items():
        print(f"    {t}: {n}")


TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Oil Palm WC Dashboard</title>
<style>
  html,body{height:100%;margin:0;font-family:Arial,sans-serif;}
  #tabs{height:46px;background:#16181A;display:flex;align-items:stretch;}
  #tabs button{background:none;border:none;color:#bbb;font-size:14px;padding:0 20px;
    cursor:pointer;border-bottom:3px solid transparent;}
  #tabs button.active{color:#C9A227;border-bottom-color:#C9A227;font-weight:bold;}
  .view{position:absolute;top:46px;left:0;right:0;bottom:0;display:none;}
  .view.active{display:block;}
  .map{width:100%;height:100%;}
  .panel{position:absolute;top:16px;right:16px;background:rgba(255,255,255,0.96);
    padding:12px 14px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.3);
    font-size:13px;max-width:290px;z-index:5;}
  .panel h3{margin:0 0 8px 0;font-size:14px;}
  .panel label{display:flex;align-items:center;gap:8px;margin:5px 0;cursor:pointer;}
  .panel select{width:100%;margin:2px 0 8px;padding:4px;font-size:13px;}
  .dot{width:14px;height:14px;border-radius:50%;border:1px solid #333;flex:0 0 auto;}
  .panel .btns{margin-top:8px;display:flex;gap:6px;}
  .panel button{font-size:11px;padding:3px 7px;cursor:pointer;}
  .sub{color:#666;font-size:11px;}
  .banner{position:absolute;top:16px;left:50%;transform:translateX(-50%);z-index:6;
    background:#D7263D;color:#fff;padding:6px 14px;border-radius:6px;font-size:12px;
    font-weight:bold;box-shadow:0 2px 6px rgba(0,0,0,0.3);}
  .iw{font-size:12px;line-height:1.5;max-width:260px;}
  .iw img{max-width:250px;max-height:180px;display:block;margin:6px 0;border:1px solid #ccc;}
</style>
</head>
<body>
<div id="tabs">
  <button id="t_wc1" class="active" onclick="showTab('wc1')">Agronomic Assessment</button>
  <button id="t_bunch" onclick="showTab('bunch')">Bunch Development</button>
  <button id="t_yield" onclick="showTab('yield')">Yield Map</button>
</div>

<div id="v_wc1" class="view active">
  <div id="map_wc1" class="map"></div>
  <div class="panel">
    <h3>Agronomic assessment</h3>
    <div class="sub">Estate</div><select id="f_estate" onchange="recomputeWc1()"></select>
    <div class="sub">Assessment month</div><select id="f_month" onchange="recomputeWc1()"></select>
    <div id="wc1_toggles"></div>
    <div class="btns">
      <button onclick="setAllWc1(true)">Show all</button>
      <button onclick="setAllWc1(false)">Hide all</button>
    </div>
    <div class="sub" style="margin-top:8px;">Click a marker to see its frame image.</div>
  </div>
</div>

<div id="v_bunch" class="view">
  <div id="map_bunch" class="map"></div>
  <div class="banner">MOCK DATA &mdash; placeholder for WC2 (not real)</div>
  <div class="panel">
    <h3>Days to ripe (predicted)</h3>
    <div><span class="dot" style="background:#D7263D"></span> Ripe now (0-3 d)</div>
    <div><span class="dot" style="background:#F17105"></span> Near-ripe (4-10 d)</div>
    <div><span class="dot" style="background:#F2C200"></span> Developing (11-21 d)</div>
    <div><span class="dot" style="background:#2E8B57"></span> Early (&gt;21 d)</div>
  </div>
</div>

<div id="v_yield" class="view">
  <div id="map_yield" class="map"></div>
  <div class="banner">MOCK DATA &mdash; placeholder for WC4 (not real)</div>
  <div class="panel">
    <h3>Predicted yield (kg/palm)</h3>
    <div><span class="dot" style="background:#C7E9C0"></span> Low (&lt;120)</div>
    <div><span class="dot" style="background:#74C476"></span> Mid (120-170)</div>
    <div><span class="dot" style="background:#238B45"></span> High (&gt;170)</div>
    <div class="sub" style="margin-top:6px;">Circle size scales with yield.</div>
  </div>
</div>

<script>
const WC1 = __WC1_MARKERS__;
const WC1_COLORS = __WC1_COLORS__;
const WC1_COUNTS = __WC1_COUNTS__;
const ESTATES = __ESTATES__;
const MONTHS = __MONTHS__;
const BUNCH = __BUNCH_MARKERS__;
const YIELD = __YIELD_MARKERS__;
const CENTER = __CENTER__;

const maps = {};
let wc1Recs = [];
const typeState = {};

function circle(color, scale){
  return {path: google.maps.SymbolPath.CIRCLE, fillColor: color, fillOpacity: 0.9,
          strokeColor: "#333", strokeWeight: 1, scale: scale};
}

function fillSelect(id, values){
  const s = document.getElementById(id);
  s.innerHTML = '<option value="__all">All</option>';
  values.forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v; s.appendChild(o); });
}

function initMap(){
  maps.wc1 = new google.maps.Map(document.getElementById("map_wc1"),
    {zoom: 19, center: CENTER, mapTypeId: "hybrid"});
  const iw1 = new google.maps.InfoWindow();
  WC1.forEach(m => {
    const mk = new google.maps.Marker({position: {lat: m.dlat, lng: m.dlng},
      map: maps.wc1, title: m.type, icon: circle(WC1_COLORS[m.type] || "#888", 7)});
    mk.addListener("click", () => {
      const img = m.img ? '<img src="' + m.img + '" alt="frame" onerror="this.style.display=\'none\'">' : '';
      iw1.setContent('<div class="iw"><strong>' + m.type + '</strong>' + img +
        (m.remarks ? 'Remarks: ' + m.remarks + '<br/>' : '') +
        'Estate: ' + m.estate + ' | Month: ' + m.month + '<br/>' +
        'Frame: ' + m.frame + '<br/>Video: ' + m.video + '<br/>' +
        (m.dt ? 'Time: ' + m.dt + '<br/>' : '') +
        'Lat: ' + m.lat.toFixed(6) + ', Lng: ' + m.lng.toFixed(6) + '</div>');
      iw1.open({anchor: mk, map: maps.wc1});
    });
    wc1Recs.push({marker: mk, type: m.type, estate: m.estate, month: m.month});
  });

  fillSelect("f_estate", ESTATES);
  fillSelect("f_month", MONTHS);

  const tg = document.getElementById("wc1_toggles");
  Object.keys(WC1_COUNTS).forEach(t => {
    typeState[t] = true;
    const id = "cb_" + t.replace(/[^a-z0-9]/gi, "");
    const row = document.createElement("label");
    row.innerHTML = '<input type="checkbox" id="' + id + '" checked>' +
      '<span class="dot" style="background:' + WC1_COLORS[t] + '"></span>' + t + ' (' + WC1_COUNTS[t] + ')';
    tg.appendChild(row);
    row.querySelector("input").addEventListener("change", e => { typeState[t] = e.target.checked; recomputeWc1(); });
  });

  maps.bunch = new google.maps.Map(document.getElementById("map_bunch"),
    {zoom: 18, center: CENTER, mapTypeId: "hybrid"});
  const iw2 = new google.maps.InfoWindow();
  BUNCH.forEach(m => {
    const c = m.days <= 3 ? "#D7263D" : m.days <= 10 ? "#F17105" : m.days <= 21 ? "#F2C200" : "#2E8B57";
    const mk = new google.maps.Marker({position: {lat: m.lat, lng: m.lng}, map: maps.bunch, icon: circle(c, 7), title: m.stage});
    mk.addListener("click", () => {
      iw2.setContent('<div class="iw"><strong>' + m.stage + '</strong><br/>Palm: ' + m.palm +
        '<br/>Predicted days to ripe: <b>' + m.days + '</b><br/><span style="color:#D7263D">(mock value)</span></div>');
      iw2.open({anchor: mk, map: maps.bunch});
    });
  });

  maps.yield = new google.maps.Map(document.getElementById("map_yield"),
    {zoom: 18, center: CENTER, mapTypeId: "hybrid"});
  const iw3 = new google.maps.InfoWindow();
  YIELD.forEach(m => {
    const c = m.yield_kg < 120 ? "#C7E9C0" : m.yield_kg <= 170 ? "#74C476" : "#238B45";
    const mk = new google.maps.Marker({position: {lat: m.lat, lng: m.lng}, map: maps.yield,
      icon: circle(c, 5 + (m.yield_kg - 80) / 140 * 8), title: m.palm});
    mk.addListener("click", () => {
      iw3.setContent('<div class="iw"><strong>Palm ' + m.palm + '</strong><br/>Predicted yield: <b>' +
        m.yield_kg + ' kg</b><br/><span style="color:#D7263D">(mock value)</span></div>');
      iw3.open({anchor: mk, map: maps.yield});
    });
  });

  recomputeWc1();
}

function recomputeWc1(){
  const est = document.getElementById("f_estate").value;
  const mon = document.getElementById("f_month").value;
  const bounds = new google.maps.LatLngBounds();
  let shown = 0;
  wc1Recs.forEach(r => {
    const vis = (typeState[r.type] !== false)
      && (est === "__all" || r.estate === est)
      && (mon === "__all" || r.month === mon);
    r.marker.setVisible(vis);
    if (vis){ bounds.extend(r.marker.getPosition()); shown++; }
  });
  if (shown > 0) maps.wc1.fitBounds(bounds);
}

function showTab(name){
  ["wc1","bunch","yield"].forEach(n => {
    document.getElementById("v_" + n).classList.toggle("active", n === name);
    document.getElementById("t_" + n).classList.toggle("active", n === name);
  });
  const m = maps[name];
  if (m) setTimeout(() => {
    google.maps.event.trigger(m, "resize");
    if (name === "wc1") recomputeWc1(); else m.setCenter(CENTER);
  }, 60);
}

function setAllWc1(v){
  Object.keys(typeState).forEach(t => {
    typeState[t] = v;
    const cb = document.getElementById("cb_" + t.replace(/[^a-z0-9]/gi, ""));
    if (cb) cb.checked = v;
  });
  recomputeWc1();
}
</script>
<script async src="https://maps.googleapis.com/maps/api/js?key=__API_KEY__&callback=initMap"></script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
