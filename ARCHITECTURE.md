# Architecture

YoUniverse Astrology is a **GTK 4 desktop application** written in Python 3.12+. It computes charts with the **Swiss Ephemeris** (`pysweph`) and renders wheels as **SVG** inside a GTK window.

> Mermaid diagrams render on GitHub. For prose guides see [docs/architecture.rst](docs/architecture.rst) and the [Sphinx docs](docs/index.rst).

## Package overview

```mermaid
flowchart TB
    subgraph Entry["Entry"]
        CLI["astrology script"]
        APP["AstrologyApplication"]
    end

    subgraph AppPkg["astrology_app"]
        MW["ui/main_window.py"]
        CHART["chart.py — AstrologyInstance"]
        DB["db.py — AstrologySqlite"]
        CFG["config.py — AstrologyCfg"]
        I18N["i18n.py — gettext"]
    end

    subgraph ModPkg["astrologymod"]
        SWISS["swiss.py — ephData"]
        VEDIC["vedic/ — Jyotish layer"]
        TZ["timezone_utils.py"]
        GEO["geoname.py + zonetab.py"]
        IMP["importfile.py"]
        GTK["gtkcompat.py + appmenu.py"]
        BRAND["branding.py"]
    end

    subgraph Data["Bundled / user data"]
        SE["share/swisseph/*.se1"]
        SQL["geonames.sql / famous.sql"]
        UCFG["~/.config/com.youniverse.astrology/ SQLite"]
    end

    CLI --> APP
    APP --> CFG
    APP --> DB
    APP --> CHART
    APP --> MW
    MW --> CHART
    MW --> DB
    CHART --> SWISS
    CHART --> IMP
    CHART --> GEO
    CHART --> TZ
    MW --> GTK
    SWISS --> SE
    DB --> SQL
    DB --> UCFG
    CFG --> BRAND
```

## Chart calculation flow

```mermaid
sequenceDiagram
    actor User
    participant UI as MainWindow
    participant Chart as AstrologyInstance
    participant Swiss as ephData
    participant DB as AstrologySqlite
    participant SVG as SVG templates

    User->>UI: Set date, time, place
    UI->>Chart: update fields / makeSVG()
    Chart->>DB: getSettingsPlanet(), getSettingsAspect()
    Chart->>Swiss: ephData(utc, lat, lon, cfg)
    Note over Swiss: pysweph calc_ut, houses,<br/>Arabic parts, Lilith, lunar phase
    Swiss-->>Chart: planets_degree_ut[], houses_degree_ut[]
    Chart->>Chart: aspect matrix, dignities, elements
    Chart->>SVG: fill astrology-svg.xml templates
    SVG-->>UI: Rsvg → GTK drawing area
    UI-->>User: display wheel / table
```

## Core types

```mermaid
classDiagram
    class AstrologyApplication {
        +main()
        +do_activate()
    }
    class AstrologyMainWindow {
        +makeSVG()
        +eventData()
        +openDatabase()
    }
    class AstrologyInstance {
        +year month day hour
        +geolat geolon
        +makeSVG()
        +planets_degree_ut
        +aspects
    }
    class ephData {
        +jul_day_UT
        +planets_degree_ut[0..34]
        +houses_degree_ut[0..11]
        +lunar_phase
    }
    class AstrologySqlite {
        +getSettingsPlanet()
        +getSettingsAspect()
        +getDatabase()
    }

    AstrologyApplication --> AstrologyMainWindow : creates
    AstrologyApplication --> AstrologyInstance : singleton
    AstrologyApplication --> AstrologySqlite : singleton
    AstrologyMainWindow --> AstrologyInstance : uses
    AstrologyInstance --> ephData : computes via
    AstrologyInstance --> AstrologySqlite : settings
```

## Chart modes

```mermaid
stateDiagram-v2
    [*] --> Radix
    Radix --> Transit : overlay second ephData
    Radix --> Synastry : two charts + inter-aspects
    Radix --> Composite : midpoints
    Radix --> Solar : solar return datetime
    Radix --> SecondaryProgression : years_diff + houses_override
    Radix --> Combine : dual ephData merge
```

## Install layout

```mermaid
flowchart LR
    subgraph Source["Repository"]
        SRC["src/"]
        SCR["scripts/"]
    end

    subgraph Venv[".venv (dev)"]
        PY["python + pysweph"]
        SHARE["share/astrology + share/swisseph"]
    end

    subgraph System["System packages"]
        DEB[".deb → /usr/"]
        RPM[".rpm → /usr/"]
    end

    SRC -->|pip install / install.sh| Venv
    SRC -->|make package-deb/rpm| System
```

## Extension points

| Module | Purpose |
|--------|---------|
| `astrologymod.importfile` | Import Oroboros, Astrolog32, Skylendar, Zet8, XML |
| `astrologymod.dignities` | Essential dignity scores |
| `astrologymod.branding` | App id, homepage, config directory name |
| `astrologymod.vedic` | Nakshatra, 16 vargas, dashas, panchanga, yogas, muhurta, chart SVG |
| `astrology_app.db` | Planets, aspects, colors, labels (SQLite) |
| `locale/*/LC_MESSAGES/` | UI translations (gettext) |

## Dependencies

```mermaid
flowchart BT
    APP[YoUniverse Astrology]
    GTK[GTK 4 / PyGObject]
    RSvg[librsvg]
    SWE[pysweph / Swiss Ephemeris]
    PY[Python 3.12+ stdlib zoneinfo]

    APP --> GTK
    APP --> RSvg
    APP --> SWE
    APP --> PY
```
