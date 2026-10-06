# Research C: headless Blender capability tests (Blender 4.5.14 LTS, CPU only)

Date: 2026-10-06. Machine: 4 cores, 15 GB RAM, no GPU. All tests run as
`blender -b --python scripts/research/test_XX_*.py`; renders in `renders/research/t0X_*.png`.
NOTE: the CPU was shared with other researchers' Blender jobs the whole time (load average 5-10 on
4 cores), so all timings below are pessimistic by roughly 1.5-2x. Numbers are wall-clock seconds.

(sections filled in below as each test finished)
