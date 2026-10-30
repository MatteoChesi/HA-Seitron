# Home Assistant – Integrazione Seitron

Integrazione custom per Home Assistant che espone i termostati Wi-Fi Seitron
(es. **Wi-Time Wall**, gestiti dall'app *Hi, Comfort*) come entità `climate`,
usando la libreria ufficiale [`pyseitron`](https://github.com/seitronspa/pyseitron).

## Stato

Prima versione funzionante. La libreria `pyseitron` è alla versione `0.0.1` e
non documenta pubblicamente alcuni dettagli — in particolare l'endpoint di
login e i valori stringa usati per `mode` / `hvac_action`. L'integrazione li
rende configurabili / tolleranti alle differenze, ma potresti dover adattare
`custom_components/seitron/api.py` o `const.py` al tuo deployment.

## Installazione

### Manuale

1. Copia la cartella `custom_components/seitron` dentro
   `<config_dir>/custom_components/` della tua installazione Home Assistant.
2. Riavvia Home Assistant.
3. **Impostazioni → Dispositivi e Servizi → Aggiungi Integrazione → Seitron**.
4. Inserisci:
   - **API host** – URL base del cloud Seitron (default
     `https://api.seitron.cloud`; **da verificare col tuo setup**).
   - **Username / Password** – le stesse credenziali dell'app Hi, Comfort.

### Via HACS (custom repository)

1. In Home Assistant, apri **HACS**.
2. In alto a destra, menu `⋮` → **Custom repositories**.
3. Nel form:
   - **Repository**: URL completo del tuo repo GitHub (es. `https://github.com/<tuo-user>/HA-Seitron`).
   - **Type**: `Integration`.
4. Clicca **Add**. Il repo apparirà nell'elenco HACS → cerca "Seitron" e
   clicca **Download**.
5. Riavvia Home Assistant.
6. **Impostazioni → Dispositivi e Servizi → Aggiungi Integrazione → Seitron**.

> Perché HACS trovi la "latest version" è consigliato pubblicare almeno un
> *release* / tag sul repo (es. `v0.1.0`). In mancanza, HACS userà il branch
> di default (tipicamente `main`).

## Entità esposte

Per ogni termostato associato all'account:

| Attributo HA              | Fonte pyseitron                     |
| ------------------------- | ----------------------------------- |
| `current_temperature`     | `SeitronThermostat.temp_curr`       |
| `target_temperature`      | `SeitronThermostat.temp_target`     |
| `hvac_mode`               | `SeitronThermostat.mode` (mappato)  |
| `hvac_action`             | `SeitronThermostat.hvac_action`     |
| `device_info`             | `manuf / model / fw_ver / gmac`     |

### Mapping modi HVAC

Mapping di default in `const.py`:

| Stringa Seitron | HVAC Mode HA |
| --------------- | ------------ |
| `OFF`           | `off`        |
| `HEAT`          | `heat`       |
| `COOL`          | `cool`       |
| `AUTO`          | `auto`       |
| `HEAT_COOL`     | `heat_cool`  |

| Stringa Seitron | HVAC Action HA |
| --------------- | -------------- |
| `OFF`           | `off`          |
| `IDLE`          | `idle`         |
| `HEATING`       | `heating`      |
| `COOLING`       | `cooling`      |

Se il tuo termostato restituisce stringhe diverse (per esempio in italiano o
numeriche), aprirà un log `DEBUG` tipo `Unknown Seitron mode 'xxx'` — guarda i
log di Home Assistant e aggiorna i dict `HVAC_MODE_MAP` / `HVAC_ACTION_MAP`
in `const.py`.

## Come adattare l'autenticazione

Il modulo `api.py` fa una `POST` a `{host}/auth/login` con body
`{"username": ..., "password": ...}` e si aspetta una risposta JSON con
`access_token` (o `token`) ed eventualmente `refresh_token`, `expires_in`.

Se il cloud Seitron reale usa invece OAuth2 standard, Firebase, Cognito o un
altro flusso, modifica il metodo `_login()` in `custom_components/seitron/api.py`.

## Polling

Default: ogni **60 s** (`DEFAULT_SCAN_INTERVAL` in `const.py`). pyseitron non
espone (ancora) notifiche push.

## Troubleshooting

Abilita il debug per vedere le richieste e le risposte:

```yaml
logger:
  default: info
  logs:
    custom_components.seitron: debug
    pyseitron: debug
```

Errori frequenti:

- **`invalid_auth` in setup** → endpoint di login o payload sbagliati, vedi la
  sezione precedente.
- **`No Seitron devices discovered on this account`** → l'endpoint
  `GET /list_thermo` è OK ma l'account non ha dispositivi associati.
- **Mode / action che non cambia** → log `Unknown Seitron mode 'xxx'`:
  aggiorna i mapping.

## Licenza

MIT — allineato con la licenza di `pyseitron`.
