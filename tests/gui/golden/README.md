# Golden (snapshot) tests

Regression tests for **chart SVG output**. A fixed radix chart (Amsterdam, 1990-06-15) is rendered; the normalized SHA-256 digest is compared to `baselines/radix_amsterdam_1990.sha256`.

## Updating baselines

```bash
make update-golden
git add tests/gui/golden/baselines/
```

Normalization logic: `tests/helpers/svg_normalize.py`.

Marked `golden` and `gui`.
