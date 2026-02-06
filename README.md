# HomeAssistant-EDC_Portal
Stažení dat z EDC Portálu do Home Assistant. Projekt je inspirován projektem [EdcReportAnalyzer](https://ondrejkarlik.github.io/EdcDataAnalyzer/dist/EdcReportAnalyzer.html)

Data se kalkulují pro tyto intervaly:
* `15m` - 15 minut
* `1h` - hodina
* `1d` - Den
- `1m` - Měsíc



Data jsou stažena do statistik, tudíž jsou k dispozici pro HA jenom tyto intervaly:
* `1h` - Hodina
* `1d` - Den
- `1m` - Měsíc

Ostatní intervaly HA neuloží. Pokud někdo zjistí jak tyto statistiky uložit tak mi dejte vědět :-).

Nejdříve se stáhnou data z EDC portálu a pak se vygeneruje CSV export, který je nahrán jako statistika do HA.

Jelikož se se statistiky nahrávají jako externí tak by v podstatě nebyla potřeba žádná entita. Ovšem pro zachování přehlednosti a jednoduššího hledání jsou vytvořeny také entity pod stejným jménem.

Systém má statické entity:
* **edc_script_duration** - Doba běhu skriptu
* **edc_script_status** - Parametry skriptu
* **edc_producer_eans** - Seznam EANů produkujících elektřinu
* **edc_consumer_eans** - Seznam EANů konzumujících
* **edc_running** - Binární senzor při běhu skriptu = `on`

Systém má dynamické entity pro jednotlivé intervaly. Jméno intervalu je použito jako `suffix` jména entity.
* **fluent** - 15 minut
* **hourly** - hodina
* **daily** - den
* **monthly** - Měsíc

Dynamické entity:
* **edc_data_shared_\<consumer EAN\>_\<interval\>** - Sdílená elektřina odběrovým EAN-em
* **edc_data_producer_missed_\<producer EAN\>_\<interval\>** - Elektřina prodána producentem do sítě, která ovšem mohla být sdílená. (Spotřebitelé měli dostatečný odběr ovšem pravděpodobně z důvodu nastaveni nebyla sdílená)
* **edc_data_producer_sold_network_\<producer EAN\>_\<interval\>** - Elektřina prodána producentem do sítě pro kterou nebyl odběr o konzumentů.
* **edc_data_consumer_missed_\<consumer EAN\>_\<interval\>** - Elektřina u odběratele, která mohla být sdílena, tedy existovala dostatečná kapacita u výrobce.
* **edc_data_consumer_purchased_\<consumer EAN\>_\<interval\>** - Nakoupená elektřina odběratelem ze sítě.

> [!IMPORTANT]
> Všechny hodnoty v `missed` jsou již také započteny do hodnot v `sold/purchased` a není je tedy potřeba připočítávat.


## Požadavky
* AppDaemon addon https://github.com/hassio-addons/addon-appdaemon
> [!IMPORTANT]
> Minimální verze AppDaemon Addonu je **0.17.3**

* Integrace `homeassistant-statistics` - https://github.com/klausj1/homeassistant-statistics
Registrace na EDC portálu https://www.edc-cr.cz

## Instalace

### homeassistant-statistics
Nainstalujte si doplněk [homeassistant-statistics](https://github.com/klausj1/homeassistant-statistics)

### Long-lived access token
Nejdříve je potřeba vygenerovat `Long-lived access token`. Token se vygeneruje v profilu (Ikona vlevo dole) a pak v `Security` tabu. [Návod](https://community.home-assistant.io/t/how-to-get-long-lived-access-token/162159/5)

### AppDaemon
1. V nastavení HA zvolte "Doplňky" a dále pak "Obchod s doplňky"
2. Vyhledejte AppDaemon, zvolte jej a klikněte na "Nainstalovat". Instalace dle rychlosti vašeho HW a internetu je hotova do několika minut.

3. Po instalaci přejděte do nastavení AppDaemon
	* v části "System Packages" přidejte `chromium-chromedriver` a `chromium`. Pozn.: pokaždé vložte jeden název a stiskněte enter, je nutné přidávat postupně
 
	* v části "Python packages" přidejte _selenium_, _pandas_, _numpy==1.26.4_ a _bs4_. Pozn.: pokaždé vložte jeden název a stiskněte enter, je nutné přidávat postupně
	* Klikněte na "Uložit". Konfigurace by měla odpovídat obrázku níže -> 


![Appdaemon configuration](/images/app_daemon_config.png)

4. Konfigurace Appdaemon se nachází v adresáři `addon_configs/a0d7b954_appdaemon/appdaemon.yaml`. Konfigurace by měla vypadat takto:

```
---
logs:
  access_log:
    filename: /homeassistant/appdaemon/logs/access.log
  error_log:
    filename: /homeassistant/appdaemon/logs/error.log
  main_log:
    filename: /homeassistant/appdaemon/logs/appdaemon.log
  diag_log:
    filename: /homeassistant/appdaemon/logs/diag.log
  pnd:
    filename: /homeassistant/appdaemon/logs/pnd.log
    name: pnd

secrets: /homeassistant/secrets.yaml
appdaemon:
  latitude: 52.379189
  longitude: 4.899431
  elevation: 2
  time_zone: Europe/Amsterdam
  app_dir: /homeassistant/appdaemon/apps
  plugins:
    HASS:
      type: hass
      ha_url: https://<HA_IP>:8123
      token: <long lived token>

      cert_verify: false
http:
  url: http://127.0.0.1:5050
  transport: socketio
admin:
api:
hadashboard:

```

> [!TIP]
> Hodnoty v `<...>` zaměňte dle Vašeho systému.

Dále v souboru `config/configuration.yaml` přidejte následující snippet:

```
homeassistant:
  packages: !include_dir_named packages
```


 **Restartujte HA**

### Skript
Nejdříve si v souboru `config/secrets.yaml` přidejte konfiguraci:

```
edc_username: ***
edc_password: ***
edc_import_group: ***

```

> [!TIP]
> Do `edc_import_group` zadejte skupinu z EDC kterou chcete exportovat

Stáhnete si poslední [Release](https://github.com/tkupka/HomeAssistant-EDC_Portal/releases)

Následně zkopírujte následující adresáře do adresáře `config` na **HA**:
* **appdaemon**
* **packages**
 
 
Poté zkontrolujte zdali se v **HA** vytvořily statické entity.
`Settings -> Devices... -> Entities`

![EDC Entities](/images/entities.png )

## Spuštění

Aplikace reaguje na `eventy` kterými se stahují data. Pokud si chcete stáhnout data tak jsou k dispozici následující možnosti.

> [!TIP]
> Data pro aktuální měsíc a předchozí den se stahují každý den v náhodném čase, ve výchozím nastavení mezi `10:15` a `11:00` (distribuce zátěže na EDC portál).
> Čas spuštění a velikost náhodné odchylky lze nastavit v Home Assistantu (Settings > Devices&Services > Entities):
> - `input_datetime.edc_daily_run_time` (EDC Daily Run Base Time) - Čas spuštění (výchozí: 10:15)
> - `input_number.edc_daily_run_randomization` (EDC Randomization Window) - Velikost náhodné odchylky v minutách (výchozí: 45)
>
> Změny času spuštění nebo velikosti náhodné odchylky se projeví okamžitě bez nutnosti restartu AppDaemona.

### Stažení aktuálních dat
Pro stažení aktuálních dat lze spustit entitu/skript "EDC Import daily data" (Settings > Devices & Services > Entities)
nebo
lze spustit event `edc_import_daily` (Developer tools > Events) bez parametrů. Stáhne se aktuální a předchozí měsíc

![EDC start Event](/images/event_edc_start.png )

### Stažení dat pro libovolný měsíc
Pro stažení dat pro libovolný měsíc lze spustit entitu/skript "EDC Import Custom Month/Year" (Settings > Devices & Services > Entities). Skript se zeptá na požadovaný měsíc a rok.
nebo
lze spustit event `edc_import_month`, který akceptuje následující parametry:
* month
* year

> [!TIP]
> Pokud parametry neuvedete berou se dle aktuálního data

![EDC start Event](/images/event_edc_start_month.png )

> [!WARNING]
> Po restartu HA se může stát, že entity zmizí, jelikož se neupdatují. Pak stačí jen spustit znova stahování dat pro jakýkoliv měsíc a veškerá data se zase vrátí. (Statistiky se v tomto případě nemažou)



## Dashboard
Pro zobrazení dat je možno použít jakoukoli komponentu, která má přístup ke statistikám. V dalším textu budu používat [`apexcharts-card`](https://github.com/RomRider/apexcharts-card)

Data jde zobrazit z pohledu producenta a nebo konzumenta. v obou pohledech jsou k dispozici denní a měsíční data.

#### Data Producenta
Z pohledu producenta lze zobrazit:
* Sdílenou energii pro jednotlivé EANy.
* Energii prodanou do sítě, která se nepodařila nasdílet.
* Ušlou příležitost pro jednotlivé EANy.

![Producer Hourly](/images/chart_producer_hourly.png )

```
type: custom:apexcharts-card
stacked: false
graph_span: 1w
span:
  end: day
  offset: "-24h"
header:
  title: EDC Producer Hourly
  show: true
  show_states: false
  colorize_states: true
now:
  show: true
  color: red
  label: Now
apex_config:
  chart:
    height: 350
    zoom:
      type: x
      enabled: true
      autoScaleYaxis: false
    toolbar:
      show: true
      autoSelected: zoom
  xaxis:
    labels:
      show: true
    type: datetime
    stepSizeX: 1
    rangeX: 990000000
  legend:
    show: true
  dataLabels:
    style:
      fontSize: 11px
    offsetX: 5
    offsetY: -8
    background:
      enabled: true
      padding: 5
      borderRadius: 1
      opacity: 0.4
    dropShadow:
      enabled: true
all_series_config:
  unit: kW
  show:
    extremas: true
  stroke_width: 2
  curve: smooth
  type: area
  opacity: 0.4
  statistics:
    type: state
    period: hour
    align: start
experimental:
  color_threshold: false
  brush: false
yaxis:
  - id: high
    decimals: 0
    min: 0
    max: 6
  - id: low
    max: 1
    min: 0
    opposite: true
    decimals: 1
series:
  - entity: input_number.edc_data_shared_<Consumer EAN>_hourly
    name: Shared
    color: rgb(92, 196, 159)
    yaxis_id: low
  - entity: input_number.edc_data_producer_missed_<Producer EAN>_hourly
    name: Missed Oportunity
    color: rgb(251, 110, 108)
    yaxis_id: low
  - entity: input_number.edc_data_producer_sold_network_<Producer EAN>_hourly
    name: Sold To Network
    color: rgb(96, 172, 252)
    yaxis_id: high


```

![Producer Daily](/images/chart_producer_daily.png )

```
type: custom:apexcharts-card
stacked: true
graph_span: 1month
span:
  end: day
header:
  title: EDC Producer Daily
  show: true
  show_states: true
  colorize_states: true
now:
  show: true
  color: red
  label: Now
apex_config:
  chart:
    height: 350
    zoom:
      type: x
      enabled: true
      autoScaleYaxis: false
    toolbar:
      show: true
      autoSelected: zoom
    xaxis.type: datetime
  dataLabels:
    style:
      fontSize: 11px
    offsetX: 5
    offsetY: -8
    background:
      enabled: true
      padding: 5
      borderRadius: 1
      opacity: 0.4
    dropShadow:
      enabled: true
all_series_config:
  unit: kW
  show:
    extremas: false
  stroke_width: 2
  curve: smooth
  type: column
  opacity: 0.4
  statistics:
    type: state
    period: day
    align: middle
experimental:
  color_threshold: false
  brush: false
series:
  - entity: input_number.edc_data_shared_<Consumer EAN>_daily
    name: Shared
    color: rgb(92, 196, 159)
  - entity: input_number.edc_data_producer_missed_<Producer EAN>_daily
    name: Missed Oportunity
    color: rgb(251, 110, 108)
  - entity: input_number.edc_data_producer_sold_network_<Producer EAN>_daily
    name: Sold To Network
    color: rgb(96, 172, 252)

```

> [!TIP]
> Pokud v entitách změníte interval **daily** na **monthly** například `input_number.edc_data_producer_sold_network_<Producer EAN>_monthly` tak získáte graf s měsíční agregací

![Producer Monthly ](/images/chart_producer_monthly.png )

```
type: custom:apexcharts-card
stacked: true
graph_span: 1year
span:
  end: month
header:
  title: EDC Producer Monthly
  show: true
  show_states: false
  colorize_states: true
now:
  show: true
  color: red
  label: Now
apex_config:
  chart:
    height: 350
    zoom:
      type: x
      enabled: true
      autoScaleYaxis: false
    toolbar:
      show: true
      autoSelected: zoom
    xaxis.type: datetime
  dataLabels:
    style:
      fontSize: 11px
    offsetX: 5
    offsetY: -8
    background:
      enabled: true
      padding: 5
      borderRadius: 1
      opacity: 0.4
    dropShadow:
      enabled: true
all_series_config:
  stroke_width: 2
  curve: smooth
  type: column
  opacity: 0.4
  show:
    extremas: false
  statistics:
    type: state
    period: month
    align: middle
experimental:
  color_threshold: false
series:
  - entity: input_number.edc_data_shared_<Consumer EAN>_monthly
    name: Shared
    invert: false
    show:
      datalabels: true
    color: rgb(92, 196, 159)

  - entity: input_number.edc_data_producer_missed_<Producer EAN>_monthly
    name: Missed Oportunity
    color: rgb(251, 110, 108)

  - entity: input_number.edc_data_producer_sold_network_<Producer EAN>_monthly
    name: Sold To Network
    show:
      datalabels: true
      header_color_threshold: true
    color: rgb(196, 201, 204)
    


```

#### Data Konzumenta
Z pohledu konzumenta lze zobrazit:
* Sdílenou energii pro jednotlivé EANy.
* Energii nakoupenou ze sítě, která se nepodařila nasdílet.
* Ušlou příležitost pro jednotlivé EANy.



![Consumer Hourly](/images/chart_consumer_hourly.png )

```
type: custom:apexcharts-card
stacked: false
graph_span: 1w
span:
  end: day
  offset: "-24h"
header:
  title: EDC Consumer Hourly
  show: true
  show_states: false
  colorize_states: true
now:
  show: true
  color: red
  label: Now
apex_config:
  chart:
    height: 350
    zoom:
      type: x
      enabled: true
      autoScaleYaxis: false
    toolbar:
      show: true
      autoSelected: zoom
    xaxis.type: datetime
  legend:
    show: true
    dataLabels:
      style:
        fontSize: 9px
      background:
        enabled: true
        padding: 2
        borderRadius: 1
  yaxis:
    decimals: 2
all_series_config:
  unit: kW
  show:
    extremas: true
  stroke_width: 2
  curve: smooth
  type: area
  opacity: 0.4
  statistics:
    type: state
    period: hour
    align: start
experimental:
  color_threshold: false
  brush: false
series:
  - entity: input_number.edc_data_shared_<Consumer EAN>_hourly
    name: Shared
    color: rgb(92, 196, 159)
  - entity: input_number.edc_data_consumer_missed_<Consumer EAN>_hourly
    name: Missed Oportunity
    color: rgb(251, 110, 108)
  - entity: input_number.edc_data_consumer_purchased_<Consumer EAN>_hourly
    name: Purchased from Network
    color: rgb(96, 172, 252)


```


![Consumer Daily](/images/chart_consumer_daily.png )

```
type: custom:apexcharts-card
stacked: true
graph_span: 1month
span:
  end: hour
show:
  last_updated: true
header:
  title: EDC Consumer Daily
  show: true
  show_states: false
  colorize_states: true
now:
  show: true
  color: red
  label: Now
apex_config:
  chart:
    height: 350
    zoom:
      type: x
      enabled: true
      autoScaleYaxis: false
    toolbar:
      show: true
      autoSelected: zoom
    xaxis.type: datetime
  dataLabels:
    style:
      fontSize: 11px
    offsetX: 5
    offsetY: -8
    background:
      enabled: true
      padding: 5
      borderRadius: 1
      opacity: 0.4
    dropShadow:
      enabled: true
all_series_config:
  unit: kW
  show:
    extremas: false
  stroke_width: 2
  curve: smooth
  type: column
  opacity: 0.4
  statistics:
    type: state
    period: day
    align: middle
experimental:
  color_threshold: false
  brush: false
series:
  - entity: input_number.edc_data_shared_<Consumer EAN>_daily
    name: Shared
    invert: false
    curve: smooth
    color: rgb(92, 196, 159)
  - entity: input_number.edc_data_consumer_missed_<Consumer EAN>_daily
    name: Missed Oportunity
    color: rgb(255, 159, 105)
    invert: false
    curve: smooth
  - entity: input_number.edc_data_consumer_purchased_<Consumer EAN>_daily
    name: Purchased from Network
    color: rgb(251, 110, 108)
    invert: false
    curve: smooth

```

> [!TIP]
> Pokud v entitách změníte interval **daily** na **monthly** například `input_number.edc_data_consumer_purchased_<Consumer EAN>_monthly` tak získáte graf s měsíční agregací

![Producer Monthly ](/images/chart_consumer_monthly.png )

```
type: custom:apexcharts-card
stacked: true
graph_span: 1y
span:
  end: month
header:
  title: EDC Consumer Monthly
  show: true
  show_states: false
  colorize_states: true
now:
  show: true
  color: red
  label: Now
apex_config:
  chart:
    height: 350
    zoom:
      type: x
      enabled: true
      autoScaleYaxis: false
    toolbar:
      show: true
      autoSelected: zoom
    xaxis.type: datetime
  dataLabels:
    style:
      fontSize: 11px
    offsetX: 5
    offsetY: -8
    background:
      enabled: true
      padding: 5
      borderRadius: 1
      opacity: 0.4
    dropShadow:
      enabled: true
all_series_config:
  stroke_width: 2
  curve: smooth
  type: column
  opacity: 0.4
  show:
    extremas: false
  statistics:
    type: state
    period: month
    align: middle
experimental:
  color_threshold: false
series:
  - entity: input_number.edc_data_shared_<Consumer EAN>_monthly
    name: Shared
    show:
      datalabels: true
    invert: false
    color: rgb(92, 196, 159)

  - entity: input_number.edc_data_consumer_missed_<Consumer EAN>_monthly
    name: Missed Oportunity
    color: rgb(181, 166, 66)

  - entity: input_number.edc_data_consumer_purchased_<Consumer EAN>_monthly
    name: Purchased from Network
    color: rgb(251, 110, 108)
    show:
      datalabels: true
    
    

```

Veškeré entity s měsíční agregací jak pro producenta, tak pro konzumenta, tedy například `input_number.edc_data_consumer_purchased_<Producer EAN>_monthly` při importu také mění svůj aktuální stav. Můžete je tedy použít k zobrazení aktuálního stavu.

![Current Status](/images/current_status.png )

```
type: custom:config-template-card
variables:
entities:
  - input_number.edc_data_shared_<Producer EAN>_monthly
card:
  type: custom:canvas-gauge-card
  entity: input_number.edc_data_shared_<Producer EAN>_monthly
  card_height: 130
  gauge:
    type: radial-gauge
    title: >-
      ${'Production: ' +
      Math.round(states['input_number.edc_data_shared_<Producer EAN>_monthly'].state)
      + ' kWh'}
    width: 220
    height: 220
    borderShadowWidth: 0
    borderOuterWidth: 0
    borderMiddleWidth: 0
    borderInnerWidth: 0
    minValue: 0
    maxValue: 1000
    startAngle: 90
    ticksAngle: 180
    valueBox: false
    majorTicks:
      - "0"
      - "100"
      - "200"
      - "300"
      - "400"
      - "500"
      - "600"
      - "800"
      - "900"
      - "1000"
    minorTicks: 2
    strokeTicks: true
    highlights:
      - from: 0
        to: 100
        color: rgba(200, 50, 50, .75)
      - from: 100
        to: 300
        color: rgba(255, 153, 51, .75)
      - from: 300
        to: 1000
        color: rgba(76, 153, 0, .75)
    borders: false
  view_layout:
    grid-area: month1

```

> [!TIP]
> Pokud máte nainstalované [Mushroom cards](https://github.com/piitaya/lovelace-mushroom), tak si můžete udělat malý toolbar, kde jde vidět stav aplikace.

![State Toolbar](/images/state_toolbar.png )

```
type: custom:mushroom-chips-card
chips:
  - type: action
    tap_action:
      action: perform-action
      perform_action: script.edc_import_current_month
      target: {}
    icon: mdi:calendar-start-outline
  - type: entity
    entity: binary_sensor.edc_running
    content_info: name
    icon_color: accent
    use_entity_picture: false
  - type: entity
    entity: input_text.edc_script_parameters
  - type: entity
    entity: input_text.edc_script_status
    content_info: state
    use_entity_picture: false
    icon_color: accent
  - type: entity
    entity: input_text.edc_script_duration
  - type: spacer
  - type: entity
    entity: input_text.edc_version
alignment: center

```


## Řešení problémů

### Aplikační Log

V `Settings -> Addon -> AppDaemon` v záložce **Log** uvidíte detailní log aplikace:

![Appdaemon Log](/images/appdaemon_log.png )


### Stahování dat


V datovém adresáři aplikace se nachází podadresář debug kde je možné vidět screenshoty z prohlížeče pro jednotlivé kroky

```
dataDirectory: "/homeassistant/appdaemon/apps/edc_importer/data"
```

![Export Form](/images/export_data.png )


### Entity
V případě, že stahování dat skončí chybou, tak chybu najdete v atributu `error` u entity `input_text.edc_script_status`

### Import statistik
V případě problémů s importem statistik [homeassistant-statistics](https://github.com/klausj1/homeassistant-statistics) si lze vypsat veškeré servisy, co AppDaemon vidí.

Toto provedete událostí `edc_print_services` a v logu AppDaemon byste měli najít:

```
{'namespace': 'default', 'domain': 'import_statistics', 'service': 'import_from_file'}
```
Pak je AppDaemon schopen zavolat import dat do HA
