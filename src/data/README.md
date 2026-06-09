# Bundled data files

| File | Description |
|------|-------------|
| `geonames.sql` | Offline geonames database (~80k cities, from [geonames.org](https://www.geonames.org) cities1000 dump) |
| `famous.sql` | Famous people / events database |

Swiss Ephemeris files (`*.se1`, `fixstars.cat`) live in `../swisseph/` and install to `share/swisseph/`.

Planet/moon `.se1` files should be the **DE441** set from upstream Swiss Ephemeris (see repo `swisseph/readme.md`). Refresh from the project root:

```bash
make update-ephemeris
```

**Attribution:** Geonames data is used under their terms; see the project `COPYING` and https://www.geonames.org .
