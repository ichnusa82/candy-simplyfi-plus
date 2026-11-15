"""Costanti."""
from datetime import timedelta

DOMAIN = "candy_simplyfi_plus"
CONF_KEY = "key"
CONF_MODE = "mode"
CONF_POWER = "power_entity"
CONF_POWER_THRESHOLD = "power_threshold"
DEFAULT_POWER_THRESHOLD = 5.0
SCAN_INTERVAL = timedelta(seconds=30)

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
    "rinse", "drying", "finished", "unknown",
]

# Program -> nome (verificati sul CDIMN 4D622PBE)
PROGRAMS = {
    "P2": "Intensivo",
    "P5": "Universale",
    "P8": "Eco",
    "P9": "Delicato",
    "P12": "Prelavaggio",
    "P16": "Auto",
    "P17": "Notte",
    "P19": "Zoom",
    "P20": "Rapido",
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

# Dal manuale: codici errore
ERRORS = {
    "E0": "Nessun errore",
    "E2": "Non carica acqua",
    "E3": "Non scarica l'acqua",
    "E4": "Perdita d'acqua",
    "E8": "Resistenza o piastra filtro intasata",
    "Ei": "Resistenza o piastra filtro intasata",
}

