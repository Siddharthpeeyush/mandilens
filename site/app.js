/* MandiLens — static site logic. Data comes from data.js (window.MANDILENS_DATA),
   regenerated daily by site/build_site.py. No network calls, no dependencies. */
(function () {
  "use strict";
  var D = window.MANDILENS_DATA;
  if (!D) { document.getElementById("freshBadge").textContent = "Price data failed to load."; return; }

  var inr0 = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
  var inr2 = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2, minimumFractionDigits: 0 });
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function fmtDate(iso) {
    var p = iso.split("-");
    return parseInt(p[2], 10) + " " + MONTHS[parseInt(p[1], 10) - 1] + " " + p[0];
  }
  function rs(v) { return "₹" + inr0.format(v); }
  function rs2(v) { return "₹" + inr2.format(v); }
  function pill(chg) {
    if (chg === null || chg === undefined) return '<span class="pill flat">—</span>';
    if (chg > 0) return '<span class="pill up">▲ +' + chg.toFixed(1) + '%</span>';
    if (chg < 0) return '<span class="pill down">▼ ' + chg.toFixed(1) + '%</span>';
    return '<span class="pill flat">0.0%</span>';
  }
  function el(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  var byShort = {};
  D.today.forEach(function (t) { byShort[t.short] = t; });

  /* ---------- freshness ---------- */
  var lagDays = Math.round((new Date(D.meta.generated) - new Date(D.meta.latestDate)) / 86400000);
  var lagText = lagDays <= 0 ? "updated today" : lagDays === 1 ? "1 day old" : lagDays + " days old";
  el("freshBadge").textContent =
    "Latest prices: " + fmtDate(D.meta.latestDate) + " · portal feed is " + lagText +
    " · " + D.meta.todayCount + " commodities";
  el("aboutLatest").textContent = fmtDate(D.meta.latestDate);
  el("moversSub").textContent =
    "Day-on-day change, " + fmtDate(D.meta.prevDate) + " → " + fmtDate(D.meta.latestDate) + ".";

  /* ---------- hero cards: onion, potato, tomato ---------- */
  var hero = el("heroCards");
  ["Onion", "Potato", "Tomato"].forEach(function (name) {
    var t = byShort[name];
    if (!t) return;
    var b = document.createElement("button");
    b.className = "hero-card";
    b.innerHTML =
      '<div class="veg">' + esc(t.short) + ' · <span class="hi">' + esc(t.hindi) + '</span></div>' +
      '<div class="price">' + rs(t.price) + '<span style="font-size:14px;font-weight:600;color:var(--muted);"> /quintal</span></div>' +
      '<div class="perkg">' + rs2(t.perKg) + ' /kg &nbsp; ' + pill(t.changePct) + '</div>';
    b.addEventListener("click", function () { openDetail(t.commodity); });
    hero.appendChild(b);
  });

  /* ---------- movers ---------- */
  function moverRows(list) {
    return list.map(function (t) {
      return '<div class="mover-row"><span class="nm">' + esc(t.short) +
        ' <small>' + esc(t.hindi) + '</small></span><span>' + rs(t.price) +
        ' &nbsp; ' + pill(t.changePct) + '</span></div>';
    }).join("");
  }
  el("risers").innerHTML = moverRows(D.risers);
  el("fallers").innerHTML = moverRows(D.fallers);

  /* ---------- price explorer ---------- */
  var activeCat = "All";
  var chipsBox = el("chips");
  ["All"].concat(D.categories).forEach(function (c) {
    var b = document.createElement("button");
    b.className = "chip";
    b.textContent = c === "All" ? "All commodities" : c;
    b.setAttribute("aria-pressed", c === "All" ? "true" : "false");
    b.addEventListener("click", function () {
      activeCat = c;
      chipsBox.querySelectorAll(".chip").forEach(function (x) {
        x.setAttribute("aria-pressed", x === b ? "true" : "false");
      });
      renderPrices();
    });
    chipsBox.appendChild(b);
  });

  var selectedCommodity = null;
  function renderPrices() {
    var q = el("search").value.trim().toLowerCase();
    var sort = el("sort").value;
    var rows = D.today.filter(function (t) {
      if (activeCat !== "All" && t.category !== activeCat) return false;
      if (!q) return true;
      return (t.short + " " + t.hindi + " " + t.commodity + " " + t.category)
        .toLowerCase().indexOf(q) !== -1;
    });
    rows.sort(function (a, b) {
      if (sort === "priceDesc") return b.price - a.price;
      if (sort === "priceAsc") return a.price - b.price;
      if (sort === "chgDesc") return (b.changePct || 0) - (a.changePct || 0);
      if (sort === "chgAsc") return (a.changePct || 0) - (b.changePct || 0);
      return a.short.localeCompare(b.short);
    });
    var box = el("priceList");
    if (!rows.length) {
      box.innerHTML = '<div class="empty">No commodity matches that search.</div>';
      return;
    }
    box.innerHTML = rows.map(function (t) {
      var msp = t.msp === null || t.msp === undefined
        ? '<span style="color:var(--muted);">no MSP</span>'
        : t.vsMspPct >= 0
          ? '<span class="msp-vs above">+' + t.vsMspPct.toFixed(1) + '% vs MSP</span>'
          : '<span class="msp-vs below">' + t.vsMspPct.toFixed(1) + '% vs MSP</span>';
      return '<button class="price-row' + (selectedCommodity === t.commodity ? " selected" : "") + '" data-c="' + esc(t.commodity) + '">' +
        '<span class="nm">' + esc(t.short) + ' <small>' + esc(t.hindi) + ' · ' + esc(t.category) + '</small></span>' +
        '<span class="num col-price"><strong>' + rs(t.price) + '</strong></span>' +
        '<span class="num col-perkg">' + rs2(t.perKg) + '</span>' +
        '<span class="col-chg">' + pill(t.changePct) + '</span>' +
        '<span class="col-msp">' + msp + '</span>' +
        '</button>';
    }).join("");
    box.querySelectorAll(".price-row").forEach(function (row) {
      row.addEventListener("click", function () { openDetail(row.getAttribute("data-c")); });
    });
  }
  el("search").addEventListener("input", renderPrices);
  el("sort").addEventListener("change", renderPrices);
  renderPrices();

  /* ---------- detail + trend chart ---------- */
  var chartPts = [];
  function drawChart() {
    var cv = el("trendChart");
    if (!cv || !chartPts.length) return;
    var dpr = window.devicePixelRatio || 1;
    var w = cv.clientWidth, h = 260;
    cv.width = w * dpr; cv.height = h * dpr;
    var ctx = cv.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);
    var padL = 58, padR = 14, padT = 14, padB = 30;
    var vals = chartPts.map(function (p) { return p.p; });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    if (hi === lo) { hi += 1; lo -= 1; }
    var span = hi - lo; lo -= span * 0.12; hi += span * 0.12;
    function X(i) { return padL + (chartPts.length === 1 ? (w - padL - padR) / 2 : i * (w - padL - padR) / (chartPts.length - 1)); }
    function Y(v) { return padT + (1 - (v - lo) / (hi - lo)) * (h - padT - padB); }
    ctx.strokeStyle = "#e3e8e3"; ctx.fillStyle = "#5c6b60";
    ctx.font = "12px -apple-system, sans-serif"; ctx.textAlign = "right";
    for (var g = 0; g <= 3; g++) {
      var gv = lo + (hi - lo) * g / 3, gy = Y(gv);
      ctx.beginPath(); ctx.moveTo(padL, gy); ctx.lineTo(w - padR, gy); ctx.stroke();
      ctx.fillText("₹" + inr0.format(Math.round(gv)), padL - 8, gy + 4);
    }
    ctx.textAlign = "center";
    chartPts.forEach(function (p, i) {
      if (i % Math.ceil(chartPts.length / 6) === 0 || i === chartPts.length - 1) {
        var d = p.d.split("-");
        ctx.fillText(parseInt(d[2], 10) + " " + MONTHS[parseInt(d[1], 10) - 1], X(i), h - 10);
      }
    });
    ctx.beginPath();
    chartPts.forEach(function (p, i) { i === 0 ? ctx.moveTo(X(i), Y(p.p)) : ctx.lineTo(X(i), Y(p.p)); });
    ctx.strokeStyle = "#1b7a3d"; ctx.lineWidth = 2.5; ctx.stroke();
    ctx.lineTo(X(chartPts.length - 1), h - padB); ctx.lineTo(X(0), h - padB); ctx.closePath();
    ctx.fillStyle = "rgba(27,122,61,0.08)"; ctx.fill();
    chartPts.forEach(function (p, i) {
      ctx.beginPath(); ctx.arc(X(i), Y(p.p), 3.5, 0, Math.PI * 2);
      ctx.fillStyle = "#1b7a3d"; ctx.fill();
      ctx.strokeStyle = "#fff"; ctx.lineWidth = 1.5; ctx.stroke();
    });
    var last = chartPts[chartPts.length - 1];
    ctx.fillStyle = "#145c2e"; ctx.textAlign = "left"; ctx.font = "bold 13px -apple-system, sans-serif";
    ctx.fillText(rs(last.p) + " /qtl", Math.min(X(chartPts.length - 1) + 8, w - 110), Math.max(Y(last.p) - 8, 14));
  }

  function openDetail(commodity) {
    var t = D.today.filter(function (x) { return x.commodity === commodity; })[0];
    var pts = D.series[commodity] || [];
    selectedCommodity = commodity;
    renderPrices();
    var sec = el("detail");
    sec.hidden = false;
    el("detailTitle").textContent = t ? t.short + " (" + t.hindi + ")" : commodity;
    el("detailDate").textContent = "National benchmark · " + fmtDate(D.meta.nationalSeriesStart) +
      " – " + fmtDate(D.meta.latestDate);
    var prices = pts.map(function (p) { return p.p; });
    var hi = prices.length ? Math.max.apply(null, prices) : null;
    var lo = prices.length ? Math.min.apply(null, prices) : null;
    var avg = prices.length ? prices.reduce(function (a, b) { return a + b; }, 0) / prices.length : null;
    var first = prices.length ? prices[0] : null;
    var last = prices.length ? prices[prices.length - 1] : null;
    var periodChg = (first && last) ? ((last - first) / first * 100) : null;
    function stat(k, v, sub) {
      return '<div class="stat"><div class="k">' + k + '</div><div class="v">' + v +
        (sub ? ' <small>' + sub + '</small>' : "") + '</div></div>';
    }
    el("detailStats").innerHTML =
      stat("Latest", t ? rs(t.price) : "—", "/quintal") +
      stat("₹ / kg", t ? rs2(t.perKg) : "—", "") +
      stat("11-day range", (lo !== null ? rs(lo) + " – " + rs(hi) : "—"), "") +
      stat("Change since " + fmtDate(D.meta.nationalSeriesStart),
        periodChg === null ? "—" : (periodChg >= 0 ? "+" : "") + periodChg.toFixed(1) + "%", "");
    var mspLine = "";
    if (t && t.msp) {
      mspLine = " MSP is " + rs(t.msp) + "/quintal — today's price sits " +
        (t.vsMspPct >= 0 ? "+" : "") + t.vsMspPct.toFixed(1) + "% " +
        (t.vsMspPct >= 0 ? "above" : "below") + " MSP.";
    } else if (t) {
      mspLine = " No MSP is published for this vegetable.";
    }
    el("detailNote").textContent =
      (pts.length === 1
        ? "Only one day of portal data for this commodity (" + fmtDate(pts[0].d) + ") — the portal publishes it irregularly."
        : "Trend of the National benchmark over the last " + pts.length + " trading days.") +
      mspLine +
      (pts.length && pts[pts.length - 1].a
        ? " Latest arrivals: " + inr0.format(pts[pts.length - 1].a) + " tonnes."
        : "");
    chartPts = pts;
    drawChart();
    sec.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  window.addEventListener("resize", drawChart);

  /* ---------- mandi compare (SAMPLE data) ---------- */
  var VEG = ["Onion", "Potato", "Tomato"];
  var mandiTab = "Onion";
  function renderMandiTabs() {
    var box = el("mandiTabs");
    box.innerHTML = "";
    VEG.forEach(function (v) {
      var b = document.createElement("button");
      b.className = "tab";
      b.textContent = v;
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", v === mandiTab ? "true" : "false");
      b.addEventListener("click", function () { mandiTab = v; renderMandiTabs(); renderMandiTable(); });
      box.appendChild(b);
    });
  }
  function renderMandiTable() {
    var rows = D.mandiToday.filter(function (r) { return r.commodity === mandiTab; })
      .slice().sort(function (a, b) { return a.price - b.price; });
    var html = "<thead><tr><th>Mandi</th><th>₹ / quintal</th><th>₹ / kg</th><th>Range (min–max)</th></tr></thead><tbody>";
    rows.forEach(function (r, i) {
      var cls = i === 0 ? ' class="cheapest"' : (i === rows.length - 1 ? ' class="costliest"' : "");
      var m = D.mandis.filter(function (x) { return x.market === r.market; })[0] || {};
      html += "<tr" + cls + "><td><strong>" + esc(m.short || r.market) + "</strong> · " +
        esc(m.city || "") + "</td><td><strong>" + rs(r.price) + "</strong></td><td>" +
        rs2(r.perKg) + "</td><td>" + rs(r.min) + " – " + rs(r.max) + "</td></tr>";
    });
    el("mandiTable").innerHTML = html + "</tbody>";
  }
  renderMandiTabs();
  renderMandiTable();

  /* ---------- forecast ---------- */
  var fcTab = "Onion";
  el("forecastSub").textContent =
    "Model outlook for 30 Oct – 5 Nov 2026, generated " + fmtDate(D.meta.generated) +
    " from data to 29 Oct 2026. These are model estimates, not mandi announcements.";
  el("forecastNote").innerHTML =
    "<strong>How to read it:</strong> plain OLS regression on the last 3 days' prices, " +
    "refit daily — the same model that won the Day-21 comparison (overall MAE ₹207/quintal). " +
    "Typical 1-day error: onion ₹208, potato ₹144, tomato ₹266. Error compounds with horizon, " +
    "so treat the later days as directional. Forecasts are built on the per-mandi sample series, " +
    "so they carry the same sample-data caveat as the mandi table above.";
  function renderForecastTabs() {
    var box = el("forecastTabs");
    box.innerHTML = "";
    VEG.forEach(function (v) {
      var b = document.createElement("button");
      b.className = "tab";
      b.textContent = v;
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", v === fcTab ? "true" : "false");
      b.addEventListener("click", function () { fcTab = v; renderForecastTabs(); renderForecastTable(); });
      box.appendChild(b);
    });
  }
  function renderForecastTable() {
    var dates = D.meta.forecast.dates || [];
    var head = "<thead><tr><th>Mandi</th>" + dates.map(function (d) {
      var p = d.split("-");
      return "<th>" + parseInt(p[2], 10) + " " + MONTHS[parseInt(p[1], 10) - 1] + "</th>";
    }).join("") + "</tr></thead><tbody>";
    var body = D.mandis.map(function (m) {
      var key = m.market + "||" + fcTab;
      var fc = (D.forecast[key] || []).slice().sort(function (a, b) { return a.h - b.h; });
      var cells = dates.map(function (d) {
        var row = fc.filter(function (x) { return x.d === d; })[0];
        return "<td>" + (row ? rs(row.p) : "—") + "</td>";
      }).join("");
      return "<tr><td><strong>" + esc(m.short) + "</strong> · " + esc(m.city) + "</td>" + cells + "</tr>";
    }).join("");
    el("forecastTable").innerHTML = head + body + "</tbody>";
  }
  renderForecastTabs();
  renderForecastTable();

  /* ---------- calculator ---------- */
  var calcSel = el("calcCommodity");
  D.today.slice().sort(function (a, b) { return a.short.localeCompare(b.short); })
    .forEach(function (t) {
      var o = document.createElement("option");
      o.value = t.commodity;
      o.textContent = t.short + " (" + t.hindi + ") — " + rs(t.price) + "/qtl";
      if (t.short === "Onion") o.selected = true;
      calcSel.appendChild(o);
    });
  function renderCalc() {
    var t = D.today.filter(function (x) { return x.commodity === calcSel.value; })[0];
    var qty = parseFloat(el("calcQty").value);
    var unit = el("calcUnit").value;
    if (!t || isNaN(qty) || qty < 0) {
      el("calcResult").innerHTML = "Enter a quantity to see the cost.";
      return;
    }
    var qtl = unit === "qtl" ? qty : unit === "kg" ? qty / 100 : qty * 10;
    var total = qtl * t.price;
    el("calcResult").innerHTML =
      "<strong>" + rs2(total) + "</strong> for " + inr2.format(qty) + " " +
      (unit === "qtl" ? "quintal" : unit === "kg" ? "kg" : "tonne") + " of " + esc(t.short) +
      "<small>At today's modal price of " + rs(t.price) + " per quintal (" + rs2(t.perKg) +
      " per kg) · " + fmtDate(D.meta.latestDate) + ", National benchmark.</small>";
  }
  ["calcCommodity", "calcQty", "calcUnit"].forEach(function (id) {
    el(id).addEventListener("input", renderCalc);
    el(id).addEventListener("change", renderCalc);
  });
  renderCalc();
})();
