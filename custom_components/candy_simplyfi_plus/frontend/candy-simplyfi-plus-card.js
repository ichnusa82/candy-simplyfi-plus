/*
 * Candy Simply-Fi Plus Card – card per la lavastoviglie Candy (integrazione candy_simplyfi_plus)
 * Caricata automaticamente dall'integrazione: type: custom:candy-simplyfi-plus-card
 */

const CARD_VERSION = "2.7.0";

const PROGRAMS = [
  { code: "P8", key: "eco", min: 230, name: "Eco", en: "Eco", icon: "mdi:leaf" },
  { code: "P16", key: "auto", min: 95, name: "Auto", en: "Auto", icon: "mdi:refresh-auto" },
  { code: "P2", key: "intensive", min: 130, name: "Intensivo", en: "Intensive", icon: "mdi:pot-steam" },
  { code: "P5", key: "universal", min: 120, name: "Universale", en: "Universal", icon: "mdi:silverware-fork-knife" },
  { code: "P17", key: "night", min: 240, name: "Notte", en: "Night", icon: "mdi:weather-night" },
  { code: "P9", key: "delicate", min: 85, name: "Delicato", en: "Delicate", icon: "mdi:glass-wine" },
  { code: "P19", key: "zoom", min: 39, name: "Zoom", en: "Zoom", icon: "mdi:lightning-bolt" },
  { code: "P20", key: "rapid", min: 24, name: "Rapido", en: "Rapid", icon: "mdi:run-fast" },
  { code: "P12", key: "prewash", min: 5, name: "Prelavaggio", en: "Pre-wash", icon: "mdi:water-outline" },
];

const STATES = {
  off: { label: "Spenta", en: "Off", icon: "mdi:power", kind: "off" },
  reset: { label: "Annullato", en: "Cancelled", icon: "mdi:restore", kind: "idle" },
  idle: { label: "In attesa", en: "Idle", icon: "mdi:dishwasher", kind: "idle" },
  ready: { label: "Pronta", en: "Ready", icon: "mdi:dishwasher", kind: "idle" },
  delayed: { label: "Partenza programmata", en: "Delayed start", icon: "mdi:timer-sand", kind: "delayed" },
  running: { label: "In lavaggio", en: "Washing", icon: "mdi:dishwasher", kind: "running" },
  prewash: { label: "Prelavaggio", en: "Pre-wash", icon: "mdi:water-outline", kind: "running" },
  wash: { label: "Lavaggio", en: "Wash", icon: "mdi:dishwasher", kind: "running" },
  rinse: { label: "Risciacquo", en: "Rinse", icon: "mdi:water-sync", kind: "running" },
  drying: { label: "Asciugatura", en: "Drying", icon: "mdi:weather-sunny", kind: "running" },
  paused: { label: "In pausa", en: "Paused", icon: "mdi:pause-circle", kind: "running" },
  finished: { label: "Terminato", en: "Finished", icon: "mdi:check-circle", kind: "finished" },
  unknown: { label: "Sconosciuto", en: "Unknown", icon: "mdi:help-circle-outline", kind: "idle" },
  unavailable: { label: "Non disponibile", en: "Unavailable", icon: "mdi:lan-disconnect", kind: "off" },
};

// translation_key delle entità di Candy Simply-Fi Plus
const KEYS = {
  sensor: ["stato", "programma", "tempo_residuo", "fine_ciclo", "partenza_alle",
           "avanzamento", "errore", "potenza", "energia_ciclo", "costo_ciclo",
           "lavaggi_filtro", "dati_grezzi"],
  binary_sensor: ["porta", "in_funzione", "manca_sale", "manca_brillantante",
                  "tabs", "smart_door", "in_consumo", "pulizia_filtro", "controllo_remoto"],
  select: ["programma_avvio"],
  number: ["ritardo_avvio"],
  switch: ["avvio_tabs", "avvio_smart_door"],
  button: ["avvia", "ferma"],
};

// testi della card: italiano e inglese (scelti dalla lingua di Home Assistant)
const TEXT = {
  it: {
    name: "Lavastoviglie", not_found: "Nessuna entità di <b>Candy Simply-Fi Plus</b> trovata. Controlla che l'integrazione sia installata.",
    starts: "Parte alle", ends: "Fine alle", remaining: "Residuo", state: "Stato", ready_out: "Pronte da togliere",
    duration: "Durata", door: "Porta aperta", salt: "Manca sale", rinse: "Manca brillantante", consuming: "In consumo",
    kwh_done: "nel ciclo", kwh_now: "finora", filter: "Pulire il filtro", washes: "lavaggi", error: "Errore",
    remote: "Controllo remoto", start: "Avvia", stop: "Ferma", start_in: "tra", delay: "Ritardo", now: "subito",
    confirm_start: "Avviare {p} sulla lavastoviglie?", confirm_stop: "Annullare il programma in corso?",
    pick: "Tocca un programma per sceglierlo",
    ed_name: "Nome", ed_programs: "Mostra programmi", ed_dishwasher: "Mostra la lavastoviglie accanto ai programmi",
    ed_power: "Sensore di potenza (facoltativo, sostituisce quello dell'integrazione)",
    card_name: "Candy Simply-Fi Plus – Lavastoviglie",
    card_desc: "Stato, programma, avanzamento e consumi della lavastoviglie Candy",
  },
  en: {
    name: "Dishwasher", not_found: "No <b>Candy Simply-Fi Plus</b> entities found. Check that the integration is installed.",
    starts: "Starts at", ends: "Ends at", remaining: "Remaining", state: "State", ready_out: "Ready to unload",
    duration: "Duration", door: "Door open", salt: "Salt missing", rinse: "Rinse aid missing", consuming: "Consuming",
    kwh_done: "this cycle", kwh_now: "so far", filter: "Clean the filter", washes: "washes", error: "Error",
    remote: "Remote control", start: "Start", stop: "Stop", start_in: "in", delay: "Delay", now: "now",
    confirm_start: "Start {p} on the dishwasher?", confirm_stop: "Cancel the running program?",
    pick: "Tap a program to choose it",
    ed_name: "Name", ed_programs: "Show programs", ed_dishwasher: "Show the dishwasher next to the programs",
    ed_power: "Power sensor (optional, replaces the integration's one)",
    card_name: "Candy Simply-Fi Plus – Dishwasher",
    card_desc: "State, program, progress and energy of the Candy dishwasher",
  },
};
const langOf = (hass) => {
  const l = (hass && ((hass.locale && hass.locale.language) || hass.language))
    || document.documentElement.lang || "it";
  return String(l).toLowerCase().startsWith("it") ? "it" : "en";
};

const DEFAULT_COLORS = {
  active: "#2E7DD7",
  running: "#52dca5",
  scheduled: "#FFB300",
  finished: "#43a047",
  error: "var(--error-color, #db4437)",
};

class CandySimplyFiPlusCard extends HTMLElement {
  static getStubConfig() {
    return {};
  }

  static getConfigElement() {
    return document.createElement("candy-simplyfi-plus-card-editor");
  }

  setConfig(config) {
    this._config = { show_programs: true, ...config };
    this._colors = { ...DEFAULT_COLORS, ...(config.colors || {}) };
    this._sig = null;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._discover();
    const sig = this._signature();
    if (sig !== this._sig) {
      this._sig = sig;
      this._render();
    }
  }

  getCardSize() {
    return 4;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: "auto" };
  }

  /* ---------- trova le entità ---------- */
  _discover() {
    const hass = this._hass;
    const cfg = this._config || {};
    const found = {};
    const reg = hass.entities || {};
    let device = cfg.device;
    // dispositivo: quello indicato, oppure il primo di candy_simplyfi_plus
    if (!device) {
      const first = Object.values(reg).find((e) => e.platform === "candy_simplyfi_plus" && e.device_id);
      device = first ? first.device_id : null;
    }
    for (const e of Object.values(reg)) {
      if (e.platform !== "candy_simplyfi_plus" || (device && e.device_id !== device)) continue;
      const domain = e.entity_id.split(".")[0];
      if (e.translation_key && (KEYS[domain] || []).includes(e.translation_key)) {
        found[e.translation_key] = e.entity_id;
      }
    }
    // ripiego: nomi standard in italiano
    const fallback = (dom, key, suffix) => {
      if (!found[key] && hass.states[`${dom}.lavastoviglie_candy_${suffix}`]) {
        found[key] = `${dom}.lavastoviglie_candy_${suffix}`;
      }
    };
    fallback("sensor", "stato", "stato");
    fallback("sensor", "programma", "programma");
    fallback("sensor", "tempo_residuo", "tempo_residuo");
    fallback("sensor", "fine_ciclo", "fine_ciclo");
    fallback("sensor", "partenza_alle", "partenza_alle");
    fallback("sensor", "avanzamento", "avanzamento");
    fallback("sensor", "errore", "codice_errore");
    fallback("sensor", "potenza", "potenza");
    fallback("sensor", "energia_ciclo", "energia_ciclo");
    fallback("sensor", "costo_ciclo", "costo_ciclo");
    fallback("sensor", "lavaggi_filtro", "lavaggi_dalla_pulizia_filtro");
    fallback("binary_sensor", "pulizia_filtro", "pulizia_filtro_consigliata");
    fallback("binary_sensor", "porta", "porta");
    fallback("binary_sensor", "in_funzione", "in_funzione");
    fallback("binary_sensor", "manca_sale", "manca_sale");
    fallback("binary_sensor", "manca_brillantante", "manca_brillantante");
    fallback("binary_sensor", "tabs", "opzione_tabs");
    fallback("binary_sensor", "smart_door", "opzione_smart_door");
    fallback("binary_sensor", "in_consumo", "in_consumo");
    // sensore di potenza scelto a mano nella card
    if (cfg.power_entity) found.potenza = cfg.power_entity;
    this._ent = found;
  }

  _fmt(stateObj) {
    // stato tradotto nella lingua di Home Assistant
    try {
      if (this._hass.formatEntityState) return this._hass.formatEntityState(stateObj);
    } catch (e) { /* versioni vecchie */ }
    return stateObj.state;
  }

  _st(key) {
    const id = this._ent && this._ent[key];
    return id ? this._hass.states[id] : undefined;
  }

  _signature() {
    if (!this._ent) return "";
    return Object.values(this._ent)
      .map((id) => {
        const s = this._hass.states[id];
        return s ? `${id}=${s.state}|${s.last_updated}` : id;
      })
      .join(";");
  }

  /* ---------- lavastoviglie stilizzata ---------- */
  _dishwasher(kind, doorOpen, rem, startAt) {
    // display: tempo residuo durante il lavaggio, "End" a fine ciclo
    const disp = kind === "running" ? (rem === null ? "--" : (rem >= 60
      ? `${Math.floor(rem / 60)}:${String(Math.round(rem) % 60).padStart(2, "0")}` : `${Math.round(rem)}'`))
      : kind === "finished" ? "End" : kind === "delayed" ? (startAt || "--:--") : "";
    const panel = `
      <rect x="4" y="4" width="72" height="17" rx="7" class="dw-panel"/>
      <rect x="4" y="13" width="72" height="8" class="dw-panel"/>
      <circle cx="13" cy="12.5" r="2.6" class="dw-led ${kind === "running" ? "blink" : ""}"/>
      <rect x="40" y="7.5" width="31" height="10" rx="2.5" class="dw-screen"/>
      <text x="55.5" y="15.3" class="dw-text">${disp}</text>`;
    if (doorOpen) {
      // porta aperta: si vedono i cestelli con i piatti
      const plates = [16, 24, 32, 40, 48, 56, 64].map((x) =>
        `<rect x="${x - 2}" y="58" width="4" height="17" rx="2" class="dw-dish"/>`).join("");
      const cups = [18, 30, 42, 54].map((x) =>
        `<path d="M${x} 36 h8 l-1 9 h-6 z" class="dw-dish"/>`).join("");
      return `<svg viewBox="-8 0 96 112" class="dw" aria-hidden="true">
        <rect x="4" y="4" width="72" height="84" rx="8" class="dw-body"/>
        <rect x="9" y="24" width="62" height="62" rx="3" class="dw-inside"/>
        ${cups}<line x1="11" y1="46" x2="69" y2="46" class="dw-rack"/>
        ${plates}<line x1="11" y1="76" x2="69" y2="76" class="dw-rack"/>
        ${panel}
        <path d="M4 88 H76 L86 106 H-6 Z" class="dw-door"/>
        <rect x="26" y="98" width="28" height="3.5" rx="1.75" class="dw-handle"/>
      </svg>`;
    }
    const bubbles = kind === "running" ? [[18, 0], [26, 1.3], [34, 0.6], [42, 2.0], [50, 0.3], [58, 1.6], [64, 2.6], [30, 2.9], [46, 1.0]]
      .map(([x, d]) => `<circle cx="${x}" cy="86" r="${2 + (x % 3) * 0.8}" class="dw-bubble" style="animation-delay:${d}s"/>`)
      .join("") : "";
    return `<svg viewBox="-8 0 96 112" class="dw" aria-hidden="true">
      <defs><clipPath id="dwclip"><rect x="8" y="34" width="64" height="58" rx="4"/></clipPath></defs>
      <rect x="4" y="4" width="72" height="100" rx="8" class="dw-body"/>
      <rect x="8" y="34" width="64" height="58" rx="4" class="dw-front"/>
      <g clip-path="url(#dwclip)">${bubbles}</g>
      ${panel}
      <rect x="22" y="26" width="36" height="4" rx="2" class="dw-handle"/>
      <rect x="10" y="96" width="60" height="4" rx="2" class="dw-plinth"/>
    </svg>`;
  }

  /* ---------- formattazione ---------- */
  _hm(min) {
    if (min === null || min === undefined || isNaN(min)) return "--";
    const m = Math.max(0, Math.round(min));
    return m >= 60 ? `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")} h` : `${m} min`;
  }

  _time(st) {
    if (!st || ["unknown", "unavailable", ""].includes(st.state)) return null;
    const d = new Date(st.state);
    if (isNaN(d)) return null;
    const lang = (this._hass.locale && this._hass.locale.language) || "it";
    return d.toLocaleTimeString(lang, { hour: "2-digit", minute: "2-digit" });
  }

  _num(st) {
    if (!st) return null;
    const n = parseFloat(st.state);
    return isNaN(n) ? null : n;
  }

  _watts(st) {
    if (!st) return null;
    let n = parseFloat(st.state);
    if (isNaN(n)) return null;
    const u = (st.attributes.unit_of_measurement || "W").trim();
    if (u === "kW") n *= 1000;
    return n;
  }

  _moreInfo(entityId) {
    if (!entityId) return;
    const ev = new Event("hass-more-info", { bubbles: true, composed: true });
    ev.detail = { entityId };
    this.dispatchEvent(ev);
  }

  /* ---------- disegno ---------- */
  _render() {
    if (!this.shadowRoot || !this._hass || !this._config) return;
    const c = this._colors;
    const stato = this._st("stato");

    const L = langOf(this._hass);
    const T = TEXT[L];
    const lbl = (o) => (L === "en" && o.en ? o.en : o.label);
    if (!stato) {
      this.shadowRoot.innerHTML = `
        <ha-card><div style="padding:16px">
          ${T.not_found}
        </div></ha-card>`;
      return;
    }

    const key = stato.state;
    const info = STATES[key] || { label: key, icon: "mdi:dishwasher", kind: "idle" };
    const running = this._st("in_funzione")?.state === "on" || info.kind === "running";
    const kind = running ? "running" : info.kind;

    const err = this._st("errore");
    const errCode = err?.attributes?.codice;
    const hasError = errCode && errCode !== "E0";

    const accent = hasError ? c.error
      : kind === "running" ? c.running
      : kind === "delayed" ? c.scheduled
      : kind === "finished" ? c.finished
      : kind === "off" ? "var(--disabled-text-color, #9e9e9e)"
      : c.active;

    const prog = this._st("programma");
    const progCode = prog?.attributes?.codice;
    // il sensore restituisce una chiave (es. "intensive"): nome tradotto da Home Assistant
    let progName = null;
    if (prog && !["unknown", "unavailable", "none"].includes(prog.state)) {
      const p = PROGRAMS.find((x) => x.code === progCode);
      progName = p ? (L === "en" ? p.en : p.name) : this._fmt(prog);
    }
    const progTemp = prog?.attributes?.temperatura;

    const rem = this._num(this._st("tempo_residuo"));
    const fine = this._time(this._st("fine_ciclo"));
    const parte = this._time(this._st("partenza_alle"));
    let pct = this._num(this._st("avanzamento"));
    if (kind === "finished") pct = 100;

    const pw = this._watts(this._st("potenza"));
    const consuming = this._st("in_consumo")?.state === "on";

    /* riga principale: fase + orario */
    const errText = err ? this._fmt(err) : `${T.error} ${errCode}`;
    let phaseLabel = hasError ? errText : lbl(info);
    let phaseIcon = hasError ? "mdi:alert-circle" : info.icon;
    let right = "";
    if (kind === "off") {
      right = "";
    } else if (kind === "delayed") {
      right = `<div class="time"><span class="cap">${T.starts}</span><b>${parte || "--:--"}</b></div>
               <div class="time"><span class="cap">${T.ends}</span><b>${fine || "--:--"}</b></div>`;
    } else if (kind === "running") {
      right = `<div class="time"><span class="cap">${T.remaining}</span><b>${this._hm(rem)}</b></div>
               <div class="time"><span class="cap">${T.ends}</span><b>${fine || "--:--"}</b></div>`;
    } else if (kind === "finished") {
      right = `<div class="time"><span class="cap">${T.state}</span><b>${T.ready_out}</b></div>`;
    } else if (rem !== null) {
      right = `<div class="time"><span class="cap">${T.duration}</span><b>${this._hm(rem)}</b></div>`;
    }

    /* comandi a distanza (solo con il controllo remoto attivo sul pannello) */
    const remote = this._st("controllo_remoto")?.state === "on";
    const nextKey = this._st("programma_avvio")?.state;
    const canStart = remote && this._st("avvia") && !["running", "delayed"].includes(kind) && kind !== "off";
    const canStop = remote && this._st("ferma") && ["running", "delayed"].includes(kind);
    const nextProg = PROGRAMS.find((p) => p.key === nextKey);

    /* striscia programmi */
    let programs = "";
    if (this._config.show_programs !== false && kind !== "off") {
      programs = `<div class="programs">` + PROGRAMS.map((p) => {
        const on = p.code === progCode;
        const pn = L === "en" ? p.en : p.name;
        const next = canStart && p.key === nextKey && !on;
        return `<div class="prog ${on ? "sel" : ""} ${next ? "next" : ""} ${canStart ? "pick" : ""}"
                     title="${pn}" ${canStart ? `data-key="${p.key}"` : ""}>
                  <ha-icon icon="${p.icon}"></ha-icon><span>${pn}</span>
                </div>`;
      }).join("") + `</div>`;
      if (this._config.show_dishwasher !== false) {
        const doorOpen = this._st("porta")?.state === "on";
        programs = `<div class="progwrap">${this._dishwasher(kind, doorOpen, rem, parte)}${programs}</div>`;
      }
    }

    /* barra di avanzamento */
    const showBar = kind === "running" || kind === "finished";
    const bar = showBar ? `
      <div class="bar"><div class="fill ${kind === "running" ? "sweep" : ""}"
           style="width:${pct === null ? 0 : pct}%"></div></div>
      <div class="barcap"><span>${progName || ""}</span><span>${pct === null ? "" : pct + "%"}</span></div>` : "";

    /* etichette */
    const chips = [];
    const chip = (icon, text, color) =>
      `<span class="chip" style="--chip:${color}"><ha-icon icon="${icon}"></ha-icon>${text}</span>`;
    if (kind !== "off") {
      if (this._st("porta")?.state === "on") chips.push(chip("mdi:door-open", T.door, c.scheduled));
      if (this._st("manca_sale")?.state === "on") chips.push(chip("mdi:shaker-outline", T.salt, c.error));
      if (this._st("manca_brillantante")?.state === "on") chips.push(chip("mdi:water-alert", T.rinse, c.error));
      if (this._st("tabs")?.state === "on") chips.push(chip("mdi:pill", "TABS", "var(--secondary-text-color)"));
      if (this._st("smart_door")?.state === "on") chips.push(chip("mdi:door-sliding-open", "Smart Door", "var(--secondary-text-color)"));
    }
    if (consuming) chips.push(chip("mdi:flash", T.consuming, c.running));
    const lang = (this._hass.locale && this._hass.locale.language) || "it";
    const kwh = this._num(this._st("energia_ciclo"));
    if (kwh !== null && (kind === "running" || kind === "finished")) {
      const txt = kwh.toLocaleString(lang, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      let label = `${txt} kWh ${kind === "finished" ? T.kwh_done : T.kwh_now}`;
      const costSt = this._st("costo_ciclo");
      const cost = this._num(costSt);
      if (cost !== null) {
        const cur = costSt.attributes.unit_of_measurement || "EUR";
        let money;
        try {
          money = cost.toLocaleString(lang, { style: "currency", currency: cur, minimumFractionDigits: 2, maximumFractionDigits: 2 });
        } catch (e) {
          money = `${cost.toFixed(2)} ${cur}`;
        }
        label += ` · ${money}`;
      }
      chips.push(chip("mdi:lightning-bolt-circle", label, "var(--secondary-text-color)"));
    }
    if (this._st("pulizia_filtro")?.state === "on") {
      const n = this._num(this._st("lavaggi_filtro"));
      chips.push(chip("mdi:air-filter", n !== null ? `${T.filter} (${n} ${T.washes})` : T.filter, c.scheduled));
    }

    if (remote) chips.unshift(chip("mdi:remote", T.remote, "var(--secondary-text-color)"));
    let actions = "";
    if (canStart && nextProg) {
      const delay = this._num(this._st("ritardo_avvio")) || 0;
      const pn = L === "en" ? nextProg.en : nextProg.name;
      // opzioni del prossimo avvio (come sul pannello: niente Smart Door su Zoom/Rapido/Prelavaggio, niente TABS sul Prelavaggio)
      const opt = (key, label, icon, allowed) => {
        const st = this._st(key);
        if (!st) return "";
        const on = st.state === "on" && allowed;
        return `<button class="opt ${on ? "on" : ""}" ${allowed ? `data-toggle="${key}"` : "disabled"}>
                  <ha-icon icon="${icon}"></ha-icon>${label}</button>`;
      };
      const opts = opt("avvio_tabs", "TABS", "mdi:pill", nextProg.code !== "P12")
        + opt("avvio_smart_door", "Smart Door", "mdi:door-sliding-open", !["P19", "P20", "P12"].includes(nextProg.code));
      // ritardo: − / + a passi di 30 minuti (0 = subito, massimo 23 ore)
      const delayCtl = this._st("ritardo_avvio") ? `<span class="delay">
          <span class="dlabel"><ha-icon icon="mdi:timer-play-outline"></ha-icon>${T.delay}</span>
          <button class="step" data-delay="-0.5" ${delay <= 0 ? "disabled" : ""}>−</button>
          <b>${delay > 0 ? this._hm(delay * 60) : T.now}</b>
          <button class="step" data-delay="0.5" ${delay >= 23 ? "disabled" : ""}>+</button>
        </span>` : "";
      actions = `<div class="actions col">
        <div class="ctrls"><span class="opts">${opts || `<span class="pickhint">${T.pick}</span>`}</span>${delayCtl}</div>
        <button class="act start wide" data-act="start" data-name="${pn}">
          <ha-icon icon="mdi:play"></ha-icon>${T.start} ${pn}${delay > 0 ? ` ${T.start_in} ${this._hm(delay * 60)}` : ""}
        </button></div>`;
    } else if (canStop) {
      actions = `<div class="actions"><span class="hint"></span>
        <button class="act stop" data-act="stop"><ha-icon icon="mdi:stop"></ha-icon>${T.stop}</button></div>`;
    }

    const power = pw !== null
      ? `<div class="power ${consuming ? "on" : ""}"><ha-icon icon="mdi:flash"></ha-icon>${
          pw >= 1000 ? (pw / 1000).toFixed(2) + " kW" : Math.round(pw) + " W"}</div>`
      : "";

    this.shadowRoot.innerHTML = `
      <style>
        :host { --accent: ${accent}; }
        ha-card { padding: 16px; overflow: hidden; cursor: pointer; }
        .head { display: flex; align-items: center; gap: 12px; }
        .badge { width: 42px; height: 42px; border-radius: 50%; display: grid; place-items: center;
                 background: color-mix(in srgb, var(--accent) 18%, transparent); color: var(--accent); flex: none; }
        .badge ha-icon { --mdc-icon-size: 24px; }
        .badge.pulse ha-icon { animation: pulse 1.8s ease-in-out infinite; }
        .title { flex: 1; min-width: 0; }
        .name { font-size: 16px; font-weight: 500; color: var(--primary-text-color); }
        .sub { font-size: 13px; color: var(--secondary-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .power { display: flex; align-items: center; gap: 2px; font-size: 14px; font-weight: 500;
                 color: var(--secondary-text-color); }
        .power ha-icon { --mdc-icon-size: 16px; }
        .power.on { color: ${c.running}; }
        .programs { display: grid; grid-template-columns: repeat(auto-fit, minmax(54px, 1fr)); gap: 4px;
                    margin-top: 14px; padding: 4px; border-radius: 13px;
                    background: var(--secondary-background-color); }
        .progwrap { display: flex; gap: 8px; align-items: center; margin-top: 14px; }
        .progwrap .programs { flex: 1; margin-top: 0; }
        .dw { flex: 0 0 78px; width: 78px; height: auto; }
        .progwrap .programs { grid-template-columns: repeat(auto-fit, minmax(48px, 1fr)); }
        .progwrap .prog span { max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .dw-body { fill: var(--secondary-background-color); stroke: var(--divider-color, rgba(127,127,127,.35)); stroke-width: 1.5; }
        .dw-panel { fill: color-mix(in srgb, var(--secondary-text-color) 18%, var(--secondary-background-color)); }
        .dw-front { fill: color-mix(in srgb, var(--accent) 16%, var(--card-background-color, #fff)); }
        .dw-screen { fill: #1d1f24; }
        .dw-text { fill: var(--accent); font: 700 7.5px/1 monospace; text-anchor: middle; }
        .dw-led { fill: var(--accent); }
        .dw-led.blink { animation: blink 1.6s ease-in-out infinite; }
        .dw-handle { fill: color-mix(in srgb, var(--secondary-text-color) 55%, transparent); }
        .dw-plinth { fill: color-mix(in srgb, var(--secondary-text-color) 25%, transparent); }
        .dw-inside { fill: color-mix(in srgb, var(--secondary-text-color) 30%, var(--secondary-background-color)); }
        .dw-rack { stroke: var(--secondary-text-color); stroke-width: 1.5; stroke-linecap: round; opacity: .7; }
        .dw-dish { fill: var(--card-background-color, #fff); stroke: var(--secondary-text-color); stroke-width: .8; }
        .dw-door { fill: color-mix(in srgb, var(--accent) 10%, var(--card-background-color, #fff));
                   stroke: var(--divider-color, rgba(127,127,127,.35)); stroke-width: 1.5; stroke-linejoin: round; }
        .dw-bubble { fill: color-mix(in srgb, var(--accent) 25%, transparent); stroke: var(--accent); stroke-width: 1.2; opacity: 0;
                     animation: bubble 3.2s ease-in infinite; }
        @keyframes bubble { 0% { transform: translateY(0); opacity: 0; } 15% { opacity: .8; }
                            100% { transform: translateY(-52px); opacity: 0; } }
        @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: .25; } }
        .prog { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
                height: 45px; border-radius: 10px; color: var(--secondary-text-color); font-size: 9px; text-align: center; }
        .prog ha-icon { --mdc-icon-size: 17px; }
        .prog.pick { cursor: pointer; }
        .prog.pick:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); }
        .prog.next { outline: 1.5px dashed var(--accent); outline-offset: -2px; color: var(--accent); }
        .actions { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: 12px; }
        .actions .hint { font-size: 11px; color: var(--secondary-text-color); }
        .act { display: inline-flex; align-items: center; gap: 6px; border: none; border-radius: 18px; padding: 8px 14px;
               font-family: inherit; font-size: 13px; font-weight: 600; line-height: 1; white-space: nowrap;
               cursor: pointer; color: #fff; background: var(--accent); }
        .act.stop { background: var(--error-color, #db4437); }
        .act ha-icon { --mdc-icon-size: 18px; }
        .opt { display: inline-flex; align-items: center; gap: 4px; padding: 5px 10px; margin-right: 4px; border-radius: 14px;
               border: 1px solid var(--divider-color, rgba(127,127,127,.35)); background: transparent; cursor: pointer;
               font-family: inherit; font-size: 12px; color: var(--secondary-text-color); white-space: nowrap; }
        .opt.on { border-color: var(--accent); color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent); }
        .opt:disabled { opacity: .4; cursor: default; }
        .opt ha-icon { --mdc-icon-size: 14px; }
        .actions.col { flex-direction: column; align-items: stretch; gap: 10px; }
        .ctrls { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; }
        .opts { display: inline-flex; flex-wrap: wrap; gap: 4px; }
        .pickhint { font-size: 11px; color: var(--secondary-text-color); }
        .act.wide { justify-content: center; padding: 10px 14px; }
        .delay { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--secondary-text-color); }
        .delay b { min-width: 46px; text-align: center; color: var(--primary-text-color); font-size: 13px; }
        .dlabel { display: inline-flex; align-items: center; gap: 3px; }
        .dlabel ha-icon { --mdc-icon-size: 14px; }
        .step { width: 26px; height: 26px; border-radius: 50%; border: 1px solid var(--divider-color, rgba(127,127,127,.35));
                background: transparent; color: var(--primary-text-color); font: 600 15px/1 sans-serif; cursor: pointer; padding: 0; }
        .step:disabled { opacity: .35; cursor: default; }
        .prog.sel { background: var(--card-background-color, #fff); color: var(--accent);
                    box-shadow: 0 1px 3px rgba(0,0,0,.15); font-weight: 600; }
        .row { display: flex; align-items: center; gap: 16px; margin-top: 14px; }
        .phase { flex: 1; display: flex; align-items: center; gap: 8px; color: var(--accent); font-weight: 500; font-size: 15px; min-width: 0; }
        .phase ha-icon { --mdc-icon-size: 20px; flex: none; }
        .time { display: flex; flex-direction: column; align-items: flex-end; }
        .time b { font-size: 15px; font-weight: 500; color: var(--primary-text-color); }
        .cap { font-size: 11px; color: var(--secondary-text-color); }
        .bar { position: relative; height: 6px; margin-top: 12px; border-radius: 3px; overflow: hidden;
               background: var(--secondary-background-color); }
        .fill { height: 100%; border-radius: 3px; background: var(--accent); position: relative; overflow: hidden;
                transition: width .6s ease; }
        .fill.sweep::after { content: ""; position: absolute; inset: 0;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,.55), transparent);
                transform: translateX(-100%); animation: sweep 2.2s ease-in-out infinite; }
        .barcap { display: flex; justify-content: space-between; margin-top: 4px; font-size: 11px; color: var(--secondary-text-color); }
        .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
        .chips:empty { display: none; }
        .chip { display: inline-flex; align-items: center; gap: 4px; padding: 3px 9px; border-radius: 12px; font-size: 12px;
                color: var(--chip); background: color-mix(in srgb, var(--chip) 14%, transparent); }
        .chip ha-icon { --mdc-icon-size: 14px; }
        @keyframes sweep { to { transform: translateX(100%); } }
        @keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.12); } }
        @media (prefers-reduced-motion: reduce) {
          .fill.sweep::after, .badge.pulse ha-icon, .dw-bubble, .dw-led.blink { animation: none; }
        }
      </style>
      <ha-card>
        <div class="head">
          <div class="badge ${kind === "running" ? "pulse" : ""}"><ha-icon icon="mdi:dishwasher"></ha-icon></div>
          <div class="title">
            <div class="name">${this._config.name || T.name}</div>
            <div class="sub">${hasError ? T.error + " " + errCode : lbl(info)}${
              progName && kind !== "off" ? " · " + progName + (progTemp && progTemp !== "-" ? " " + progTemp + "°C" : "") : ""}</div>
          </div>
          ${power}
        </div>
        ${programs}
        ${kind === "off" ? "" : `
        <div class="row">
          <div class="phase"><ha-icon icon="${phaseIcon}"></ha-icon><span>${phaseLabel}</span></div>
          ${right}
        </div>`}
        ${bar}
        <div class="chips">${chips.join("")}</div>
        ${actions}
      </ha-card>`;

    this.shadowRoot.querySelectorAll("[data-key]").forEach((el) => el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      this._hass.callService("select", "select_option", { entity_id: this._ent.programma_avvio, option: el.dataset.key });
    }));
    this.shadowRoot.querySelectorAll("[data-delay]").forEach((el) => el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const cur = this._num(this._st("ritardo_avvio")) || 0;
      const value = Math.min(23, Math.max(0, cur + parseFloat(el.dataset.delay)));
      this._hass.callService("number", "set_value", { entity_id: this._ent.ritardo_avvio, value });
    }));
    this.shadowRoot.querySelectorAll("[data-toggle]").forEach((el) => el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      this._hass.callService("switch", "toggle", { entity_id: this._ent[el.dataset.toggle] });
    }));
    this.shadowRoot.querySelectorAll("[data-act]").forEach((el) => el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const start = el.dataset.act === "start";
      const msg = start ? T.confirm_start.replace("{p}", el.dataset.name) : T.confirm_stop;
      if (!window.confirm(msg)) return;
      this._hass.callService("button", "press", { entity_id: start ? this._ent.avvia : this._ent.ferma })
        .catch((err) => window.alert(err && err.message ? err.message : String(err)));
    }));
    this.shadowRoot.querySelector("ha-card").addEventListener("click", () => {
      this._moreInfo(this._config.tap_entity || this._ent.stato);
    });
  }
}

/* ---------- editor visuale minimo ---------- */
class CandySimplyFiPlusCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }
  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
  }
  _render() {
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) => {
        const T = TEXT[langOf(this._hass)];
        return { name: T.ed_name, show_programs: T.ed_programs, show_dishwasher: T.ed_dishwasher,
                 power_entity: T.ed_power }[s.name] || s.name;
      };
      this._form.schema = [
        { name: "name", selector: { text: {} } },
        { name: "show_programs", selector: { boolean: {} } },
        { name: "show_dishwasher", selector: { boolean: {} } },
        { name: "power_entity", selector: { entity: { domain: "sensor" } } },
      ];
      this._form.addEventListener("value-changed", (ev) => {
        const config = { ...this._config, ...ev.detail.value };
        if (!config.power_entity) delete config.power_entity;
        const e = new Event("config-changed", { bubbles: true, composed: true });
        e.detail = { config };
        this.dispatchEvent(e);
      });
      this.appendChild(this._form);
    }
    this._form.data = { show_programs: true, show_dishwasher: true, ...this._config };
    if (this._hass) this._form.hass = this._hass;
  }
}

if (!customElements.get("candy-simplyfi-plus-card")) {
  customElements.define("candy-simplyfi-plus-card", CandySimplyFiPlusCard);
  customElements.define("candy-simplyfi-plus-card-editor", CandySimplyFiPlusCardEditor);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "candy-simplyfi-plus-card",
    name: TEXT[langOf()].card_name,
    description: TEXT[langOf()].card_desc,
    preview: true,
  });
  console.info(`%c CANDY SIMPLY-FI PLUS CARD %c v${CARD_VERSION} `,
    "color:#fff;background:#2E7DD7;font-weight:700", "color:#2E7DD7");
}
