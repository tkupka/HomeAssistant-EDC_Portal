# HomeAssistant-EDC_Portal
Stažení dat z EDC Portálu do Home Assistent. Projekt je inspirovan projektem [EdcReportAnalyzer](https://ondrejkarlik.github.io/EdcDataAnalyzer/dist/EdcReportAnalyzer.html)

Stažení dat z EDC portálu do Home Assistenta. Data se kalkulují pro tyto intervaly:
* `15m` - 15 minut
* `1h` - hodina
* `1d` - Den
- `1m` - Měsíc



Data jsou stažena do statistik, tudíž jsou k dispozici pro HA jenom tyto intervaly:
* `1h` - Hodina
* `1d` - Den
- `1m` - Měsíc

Ostatní intervaly HA neuloží. Pokud někdo zjistí jak tyto statistiky uložit tak mi dejte vědět :-).

Nejdříve se stáhnoout data z EDC portálu a pak se vygeneruje CSV export, který je nahrán jako statistika do HA.

Jelikož se se statistiky nahrávají jako externí tak by v podstatě nebyla potřeba žádná entita. Ovšem pro zachování přehlednosti a jednoduššího hledání jsou vytvořeny také entity pod stejným jménem.

Systém má statické entity:
* **edc_script_duration** - Doba běhu skriptu
* **edc_script_status** - Parametry skriptu
* **edc_producer_eans** -Seznam EANu produkujících elektřinu
* **edc_consumer_eans** - Seznam EANu konzumujících  
* **running** - Binární senzor při pěhu skriptu = `on`

Systém má dynamické entity pro jednotlivé intervaly. Jméno intervalu je použito jako `suffix` jme entity.
* **fluent** - 15 minut
* **hourly** - hodina
* **daily** - den
* **monthly** - Měsíc

Dynamické entity:
* **edc_data_shared_<consumer EAN>_<interval>** - Sdílená elektřina odběrovým EAN-em
* **edc_data_producer_missed_<producer EAN>_<interval>** - Elektřina prodána producentem do sítě, která ovšem mohla být sdílená. (Spotřebitelé měli dostatečný odběr ovšem pravděpodobně z důvodu nastaveni nebyla sdílená)
* **edc_data_producer_sold_network__<producer EAN>_<interval>** - Elektřina prodána producentem do sítě pro kterou nebyl odběr o konzumentů.
* **edc_data_consumer_missed_<consumer EAN>_<interval>** - Elektřina u odběratele, která mohla být sdílena. tedy existovala  dostatečná kapacita u výrobce.
* **edc_data_consumer_purchased_<consumer EAN>_<interval>** - Nakoupená elektrina odběratelem ze sítě.

> [!IMPORTANT]
> Všechny hodnoty v `missed` jsou již také započteny do hodnot v `sold/purchsed` a není je tedy potřeba připočítávat.


## Požadavky
* AppDaemon addon https://github.com/hassio-addons/addon-appdaemon
* Integrace `homeassistant-statistics` - https://github.com/klausj1/homeassistant-statistics
Registraci na EDC potrálu https://www.edc-cr.cz

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


4.Konfigurace Appdaemon se nachazí v adresáři `addon_configs/a0d7b954_appdaemon/appdaemon.yaml` . Konfigurace by měla vypadat takto:

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
      ha_url: https://<HA_IP>>:8123
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

Dále v soboru `config/configuration.yaml` přidejte následující snippet:

```
homeassistant:
  packages: !include_dir_named packages
```


 **Restartujte HA**

### Skript
Nejdrříve si v souboru `config/secrets.yaml` přidejte konfiguraci:

```
edc_username: ***
edc_password: ***
edc_exportGroup: ***

```

Následně zkopírujte následující adresáře do adresáře `config` na **HA**:
* **appdaemon**
* **packages**
 
 
Poté zkontrolujte zdali se v **HA** vytvořily statické entity.
`Settings -> Devices... -> Entities`

![EDC Entities](/images/entities.png )

### Dashboard
Pro zobrazení dat je možno použí jakoukoli komponentu která má přístup ke statistikám. V dalším textu budu používat [`apexcharts-card`](https://github.com/RomRider/apexcharts-card)

Data jde zobrazit z pohledu producenta a nebo konzumenta. v obou pohledech jsou k dispozici denní a měsíční data.

#### Data Producenta
Z pohledu producenta lze zobrazit:
* Sdílenou energii pro jednotlivé EANy.
* Energii prodanou do sítě, která se nepodařila nasdílet.
* Ušlou příležitostpro jednotlivé EANy.

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
  group_by:
    func: avg
    duration: 1h
  statistics:
    type: state
    period: hour
    align: middle
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
  end: hour
header:
  title: EDC Producer Daily
  show: true
  show_states: true
  colorize_states: true
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
  group_by:
    func: avg
    duration: 1d
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
graph_span: 1y
span:
  end: month
header:
  title: EDC Producer Monthly
  show: true
  show_states: true
  colorize_states: true
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
  group_by:
    func: avg
    duration: 1month
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
all_series_config:
  unit: kW
  show:
    extremas: true
  stroke_width: 2
  curve: smooth
  type: area
  opacity: 0.4
  group_by:
    func: avg
    duration: 1h
  statistics:
    type: state
    period: hour
    align: middle
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
  group_by:
    func: avg
    duration: 1d
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
  group_by:
    func: avg
    duration: 1month
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
    color: rgb(251, 110, 108)

  - entity: input_number.edc_data_consumer_purchased_<Consumer EAN>_monthly
    name: Sold To Network
    show:
      datalabels: true
    color: rgb(196, 201, 204)
    

```