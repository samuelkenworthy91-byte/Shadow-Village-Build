import runpy

# Run the full existing v7.1/v8/main-polish stack first, then retire any final
# legacy Genjutsu-tree nodes against the assembled current source.
runpy.run_path("overrides/apply_bingo_book_v7_1_base.py", run_name="__main__")
runpy.run_path("overrides/apply_main_genjutsu_cleanup.py", run_name="__main__")

# Kage Life is now the canonical product identity. Apply the save-scoped village
# naming refactor only after the complete Bingo Book/main-polish source exists,
# then install the supplied app artwork and final player-facing copy.
runpy.run_path("overrides/apply_kage_life_rename.py", run_name="__main__")
runpy.run_path("overrides/finalize_kage_life.py", run_name="__main__")
