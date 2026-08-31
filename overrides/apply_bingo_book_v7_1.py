import runpy

# Run the full existing v7.1/v8/main-polish stack first, then retire any final
# legacy Genjutsu-tree nodes against the assembled current source.
runpy.run_path("overrides/apply_bingo_book_v7_1_base.py", run_name="__main__")
runpy.run_path("overrides/apply_main_genjutsu_cleanup.py", run_name="__main__")
