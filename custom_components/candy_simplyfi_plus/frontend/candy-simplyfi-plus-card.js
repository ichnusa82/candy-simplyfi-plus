/*
 * Candy Simply-Fi Plus Card – card per la lavastoviglie Candy (integrazione candy_simplyfi_plus)
 * Caricata automaticamente dall'integrazione: type: custom:candy-simplyfi-plus-card
 */

const CARD_VERSION = "2.6.0";

const PROGRAMS = [
  { code: "P8", min: 230, name: "Eco", en: "Eco", icon: "mdi:leaf" },
  { code: "P16", min: 95, name: "Auto", en: "Auto", icon: "mdi:refresh-auto" },
  { code: "P2", min: 130, name: "Intensivo", en: "Intensive", icon: "mdi:pot-steam" },
  { code: "P5", min: 120, name: "Universale", en: "Universal", icon: "mdi:silverware-fork-knife" },
  { code: "P17", min: 240, name: "Notte", en: "Night", icon: "mdi:weather-night" },
  { code: "P9", min: 85, name: "Delicato", en: "Delicate", icon: "mdi:glass-wine" },
  { code: "P19", min: 39, name: "Zoom", en: "Zoom", icon: "mdi:lightning-bolt" },
  { code: "P20", min: 24, name: "Rapido", en: "Rapid", icon: "mdi:run-fast" },
  { code: "P12", min: 5, name: "Prelavaggio", en: "Pre-wash", icon: "mdi:water-outline" },
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
                  "tabs", "smart_door", "in_consumo", "pulizia_filtro"],
};

// testi della card: italiano e inglese (scelti dalla lingua di Home Assistant)
const TEXT = {
  it: {
    name: "Lavastoviglie", not_found: "Nessuna entità di <b>Candy Simply-Fi Plus</b> trovata. Controlla che l'integrazione sia installata.",
    starts: "Parte alle", ends: "Fine alle", remaining: "Residuo", state: "Stato", ready_out: "Pronte da togliere",
    duration: "Durata", door: "Porta aperta", salt: "Manca sale", rinse: "Manca brillantante", consuming: "In consumo",
    kwh_done: "nel ciclo", kwh_now: "finora", filter: "Pulire il filtro", washes: "lavaggi", error: "Errore",
    ed_name: "Nome", ed_programs: "Mostra programmi",
    ed_power: "Sensore di potenza (facoltativo, sostituisce quello dell'integrazione)",
    card_name: "Candy Simply-Fi Plus – Lavastoviglie",
    card_desc: "Stato, programma, avanzamento e consumi della lavastoviglie Candy",
  },
  en: {
    name: "Dishwasher", not_found: "No <b>Candy Simply-Fi Plus</b> entities found. Check that the integration is installed.",
    starts: "Starts at", ends: "Ends at", remaining: "Remaining", state: "State", ready_out: "Ready to unload",
    duration: "Duration", door: "Door open", salt: "Salt missing", rinse: "Rinse aid missing", consuming: "Consuming",
    kwh_done: "this cycle", kwh_now: "so far", filter: "Clean the filter", washes: "washes", error: "Error",
    ed_name: "Name", ed_programs: "Show programs",
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

    /* striscia programmi */
    let programs = "";
    if (this._config.show_programs !== false && kind !== "off") {
      programs = `<div class="programs">` + PROGRAMS.map((p) => {
        const on = p.code === progCode;
        const pn = L === "en" ? p.en : p.name;
        return `<div class="prog ${on ? "sel" : ""}" title="${pn}">
                  <ha-icon icon="${p.icon}"></ha-icon><span>${pn}</span>
                </div>`;
      }).join("") + `</div>`;
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
        .prog { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
                height: 45px; border-radius: 10px; color: var(--secondary-text-color); font-size: 9px; text-align: center; }
        .prog ha-icon { --mdc-icon-size: 17px; }
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
          .fill.sweep::after, .badge.pulse ha-icon { animation: none; }
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
      </ha-card>`;

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
        return { name: T.ed_name, show_programs: T.ed_programs, power_entity: T.ed_power }[s.name] || s.name;
      };
      this._form.schema = [
        { name: "name", selector: { text: {} } },
        { name: "show_programs", selector: { boolean: {} } },
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
    this._form.data = { show_programs: true, ...this._config };
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
