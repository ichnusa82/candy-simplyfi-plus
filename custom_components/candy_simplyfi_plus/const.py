"""Costanti."""
from datetime import timedelta

DOMAIN = "candy_simplyfi_plus"
CONF_KEY = "key"
CONF_MODE = "mode"
CONF_POWER = "power_entity"
CONF_POWER_THRESHOLD = "power_threshold"
DEFAULT_POWER_THRESHOLD = 5.0
CONF_PRICE = "energy_price"            # prezzo fisso per kWh
CONF_PRICE_ENTITY = "price_entity"     # oppure sensore del prezzo
CONF_FILTER_EVERY = "filter_every"     # lavaggi tra una pulizia del filtro e l'altra
DEFAULT_FILTER_EVERY = 30
CONF_SCAN = "scan_interval"            # secondi tra una lettura e l'altra
DEFAULT_SCAN = 30
CONF_LOG = "data_log"                  # registro CSV attivo
DEFAULT_LOG = True
SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN)

ONLINE = "_online"

# Campi JSON della lavastoviglie simply-Fi
F_STATE = "StatoDWash"
F_PROGRAM = "Program"
F_REMAINING = "RemTime"
F_DELAY = "DelayStart"
F_ERROR = "CodiceErrore"
F_DOOR = "OpenDoor"
F_SALT = "MissSalt"
F_RINSE = "MissRinse"
F_ECO = "Eco"
F_HALF_LOAD = "MetaCarico"
F_EXTRA_DRY = "ExtraDry"
F_START_STOP = "StartStop"
F_WIFI = "StatoWiFi"
F_TABS = "TreinUno"
F_SMART_DOOR = "OpenDoorOpt"
F_SOFTENER = "r7"      # livello decalcificatore S0-S7
F_BEEP = "r6"          # segnali acustici
F_MEMO = "r8"          # funzione memo

# StatoDWash -> chiave di traduzione (solo codici verificati sul CDIMN 4D622PBE)
# 2 = accesa, nessun programma confermato
# 5 = ciclo terminato
# 3 = programma avviato: in attesa se DelayStart > 0, altrimenti in lavaggio
# 4 = programma selezionato, pronta
# Le fasi di lavaggio e la fine ciclo si aggiungono dopo un lavaggio vero:
# nel frattempo, con StartStop = 1 lo stato è "running".
STATES = {
    "1": "reset",     # programma annullato (Program = P0, Reset = 1), dura pochi secondi
    "2": "idle",
    "3": "running",
    "4": "ready",
    "5": "finished",
}

# Campo r2 durante il lavaggio = fase (verificato con un ciclo Intensivo)
F_PHASE = "r2"
PHASES = {
    "1": "prewash",   # da confermare (non visto: l'Intensivo è partito da 2)
    "2": "wash",
    "3": "rinse",
    "4": "drying",
}
STATE_OPTIONS = [
    "off", "reset", "idle", "ready", "delayed", "running", "prewash", "wash",
    "rinse", "drying", "paused", "finished", "unknown",
]

# Program -> nome (verificati sul CDIMN 4D622PBE)
# Program -> chiave del programma (nomi tradotti in translations/*.json)
PROGRAMS = {
    "P2": "intensive",
    "P5": "universal",
    "P8": "eco",
    "P9": "delicate",
    "P12": "prewash",
    "P16": "auto",
    "P17": "night",
    "P19": "zoom",
    "P20": "rapid",
}
PROGRAM_OPTIONS = [*PROGRAMS.values(), "none", "other"]
# nomi italiani usati fino alla 2.6.0 di sviluppo, per convertire i dati salvati
PROGRAM_OLD_NAMES = {
    "Intensivo": "intensive", "Universale": "universal", "Eco": "eco", "Delicato": "delicate",
    "Prelavaggio": "prewash", "Auto": "auto", "Notte": "night", "Zoom": "zoom", "Rapido": "rapid",
    "Sconosciuto": "other",
}

# Dal manuale: temperatura (°C) e durata media (min)
PROGRAM_INFO = {
    "P8": ("45", 232),
    "P2": ("75", 130),
    "P17": ("55", 240),
    "P5": ("60", 120),
    "P16": ("55-65", 95),
    "P9": ("45", 85),
    "P19": ("60", 39),
    "P20": ("50", 24),
    "P12": ("-", 5),
}

# Dal manuale: codici errore -> chiave (testi tradotti in translations/*.json)
ERRORS = {
    "E0": "none",
    "E2": "no_water",
    "E3": "no_drain",
    "E4": "leak",
    "E8": "heater_filter",
    "Ei": "heater_filter",
}
ERROR_OPTIONS = ["none", "no_water", "no_drain", "leak", "heater_filter", "other"]
