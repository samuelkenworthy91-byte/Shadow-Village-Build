# Bingo Book unique battle assets

Repository source assets are compact transparent WebP files. Transport-only `.webp.b64` files are also accepted so binary payloads can be staged through text-only tooling, but runtime generation happens in one batch pass rather than one image at a time.

Stable asset IDs are `bingo_001` through `bingo_080`; runtime paths are `/bingo/bingo_###.png`.

## Fast batch workflow

1. Prepare/crop all available sprites first.
2. Stage the whole group together (target 10–20 assets per Git commit, not one commit per sprite).
3. Run one conversion pass:

```bash
python overrides/bingo_assets_v1/import_batch.py --start 1 --end 80
```

The importer decodes every staged Base64 transport file, converts available sprites in parallel, and reports the complete missing-ID set together instead of aborting on the first missing image.

For final release validation, require all 80:

```bash
python overrides/bingo_assets_v1/import_batch.py --start 1 --end 80 --require-complete
```

The legacy `import_batch_001_020.py` wrapper remains for compatibility but now delegates to the batch importer.
