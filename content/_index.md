+++
date = '2026-04-06T13:38:04+02:00'
draft = false
title = 'Synthetic Photometry Lab'
+++

*Authors: Niall Miller (lead TA), Eliza Frankel -- MESA Summer School 2026, Tetons, Wyoming*

In the Custom Colors lab we switched on the MESA `colors` module and watched a single track sweep across a synthetic color–magnitude diagram. This lab is the playground that follows. We are not building anything from scratch and we are not changing any stellar physics — we are going to *play* with the colors module: swap its inputs around, watch what changes, and make some fun plots and movies out of the results.

To make that fun, the star we ship is a **5 M☉ intermediate-mass model that performs a blue loop** during core helium burning, carrying it back and forth across the classical (Cepheid) **instability strip**. So the synthetic photometry doesn't just creep along a main sequence — it loops, brightens, and reddens, which makes for a much more interesting SED movie and color–magnitude diagram.

Along the way we will meet `colors`' companion tool, **SED_Tools**, which is where all of those filter and atmosphere inputs actually come from, and we will finish by meeting **SED_Model**, the pure-Python twin of MESA `colors`.

Everything here is safe to poke at. The working directory is its own self-contained copy, and every change is reversible — if a run goes sideways, you delete the output folder and try again. The goal is exploration, not a deliverable.

> [!NOTE]
> This lab assumes the colors-enabled MESA you set up in the Custom Colors lab is still your `$MESA_DIR`, with its filter and atmosphere data under `$MESA_DIR/data/colors_data/`. If you skipped that lab, run its installation section first.

{{< cards >}}
{{< card link="https://raw.githubusercontent.com/nialljmiller/custom-colors_mesa-school-labs/main/raw/main/synthphot_lab.zip" 
    title="Download Lab Files" 
    subtitle="The synthphot_lab work directory, inlist, and python_helpers scripts used throughout." >}}
{{< card link="https://github.com/nialljmiller/SED_Tools" title="SED_Tools" subtitle="Download and standardize filters and stellar atmosphere grids for the colors module." >}}
{{< card link="https://github.com/nialljmiller/SED_Model" title="SED_Model" subtitle="The Python twin of MESA colors — forward synthetic photometry and parameter fitting." >}}
{{< /cards >}}

---

## What you will do

| Part | Topic |
|------|-------|
| 1 | Setup and the blue-loop run |
| 2 | Altering the `colors` module inputs |
| 3 | SED_Tools — discover, download & process filters and atmospheres (the largest part) |
| 4 | Fun runs: plots and videos from the `python_helpers` scripts |
| 5 | SED_Model — the Python twin (forward *and* inverse) |

---

## Part 1: Setup and the blue-loop run

The colors module turns the things MESA already computes ($T_\mathrm{eff}$, $\log g$, $L$) into the things observers actually measure: synthetic magnitudes in a chosen filter system. It does this by interpolating a stellar atmosphere grid to get an SED, convolving that SED with each filter's transmission curve, and calibrating against a reference spectrum (Vega or AB).

Download and unzip the lab working directory, then build it:

```bash
unzip synthphot_lab.zip
cd synthphot_lab
./clean
./mk
```

Everything for this lab lives in a single file, `inlist_run`. When you run `./rn` it copies `inlist_run` to `inlist` and runs that, so `inlist_run` is the only file you edit — all the namelists (`&star_job`, `&colors`, `&controls`, `&pgstar`, …) are in there together.

Open `inlist_run` and find the `&colors` namelist. The shipped block runs as-is and looks like this:

```fortran
&colors
   use_colors = .true.
   instrument = '/data/colors_data/filters/GAIA/GAIA'           ! filter system directory
   stellar_atm = '/data/colors_data/stellar_models/Kurucz2003all/'  ! atmosphere grid
   vega_sed = '/data/colors_data/stellar_models/vega_flam.csv'      ! zero-point reference
   mag_system = 'Vega'          ! 'Vega' or 'AB'
   distance = 3.0857d19         ! 10 pc in cm -> absolute magnitudes
   make_csv = .true.            ! write a full SED per filter (needed for SED plots)
   colors_results_directory = 'SED'
/ ! end of colors namelist
```

The `&controls` namelist is set to evolve the 5 M☉ star through core helium burning (it stops near central He exhaustion), which is what gives us the blue loop.

> [!NOTE]
> Confirm `pgstar_flag = .true.` in `&star_job` (it already is), then run:

```bash
./rn
```

This is a longer run than a quick main-sequence test — it carries the star from the pre-main sequence, through the main sequence and the red giant branch, and into core helium burning where the blue loop happens. Watch the HR diagram: the track will move redward to the giant branch and then loop back toward the blue, crossing the instability strip.

> [!CAUTION]
> Blue-loop morphology is genuinely sensitive to mass, metallicity, overshoot, and mixing. The shipped 5 M☉ / Z = 0.0014 / step-overshoot model is set up to loop, but if your loop comes out short or absent, that is a feature to explore, not a bug — try nudging `initial_mass` up to 6–7 M☉ or adjusting `overshoot_f(1)` in `&controls`.

When it finishes you have a run with Gaia magnitudes in `LOGS/` and a full SED written at each profile step to the `SED/` output folder (the one named by `colors_results_directory`). That is the thing we spend the rest of the lab altering and visualizing.

---

## Part 2: Altering the colors module inputs

This is the heart of the lab. Every interesting thing the colors module does is controlled by a handful of lines in `&colors`. We will change them one at a time and rerun, so you can see exactly what each knob does. A good habit: change `star_history_name` (or copy the `LOGS/` folder aside) between runs so they don't overwrite each other.

| Parameter | What it controls | Try changing it to… |
|-----------|------------------|---------------------|
| `instrument` | which filter system you observe in | `2MASS`, `JWST`, `TESS`, `Generic` |
| `stellar_atm` | the atmosphere grid that becomes the SED | `Kurucz2003all__alpha_04`, `bbody` |
| `vega_sed` | the zero-point reference spectrum | leave as-is unless you change `mag_system` |
| `mag_system` | the magnitude system | `'Vega'` or `'AB'` |
| `distance` | flux scaling → apparent vs absolute mags | `3.0857d19` (10 pc) for absolute |
| `make_csv` | write the full SED to disk per filter | `.true.` to enable SED plotting/movies |

### 2a — Distance: absolute vs apparent

`distance` is the simplest knob and the one with the clearest meaning. At exactly 10 parsecs ($3.0857\times10^{19}$ cm) the magnitudes come out on the **absolute** scale. At any other distance you get **apparent** magnitudes, following the distance modulus:

$$m - M = 5\log_{10}\left(\frac{d}{10\ \mathrm{pc}}\right)$$

**Task:** Move your star out to 100 pc and rerun.

{{< details title="Solution" closed="true" >}}

```fortran
   distance = 3.0857d20   ! 100 pc in cm -> apparent magnitudes, 5 mag fainter
```

Every magnitude in the history file should shift fainter by exactly 5 magnitudes relative to your 10 pc run. The *colors* (differences between bands) are unchanged — distance moves the whole SED up and down, it doesn't reshape it.

{{< /details >}}

### 2b — Magnitude system: Vega vs AB

The `mag_system` knob picks the zero-point convention. `'Vega'` defines Vega to be 0.0 in every band; `'AB'` uses a flat reference in frequency. Same SED, same filters — different numbers.

**Task:** Switch to the AB system and rerun. Compare the Gaia magnitudes to your Vega run.

```fortran
   mag_system = 'AB'
```

> [!TIP]
> The AB–Vega offset is different for every filter because it depends on where in wavelength the band sits. This is exactly why observers are always careful to state which system a magnitude is in.

### 2c — Swapping the filter system

The `instrument` path points at a *directory* of filter transmission curves. The prerelease ships several: `GAIA`, `2MASS`, `Generic`, `JWST`, and `TESS`. Point `instrument` at a different one and you are suddenly observing the same star with a different telescope.

**Task:** Observe your star in 2MASS (near-infrared $J$, $H$, $K_s$) instead of Gaia.

{{< details title="Solution" closed="true" >}}

```fortran
   instrument = '/data/colors_data/filters/2MASS/2MASS'
```

Your history file now has `J`, `H`, and `Ks` columns instead of `G`, `Gbp`, `Grp`. A cool, evolved star will look comparatively much brighter here than it did in Gaia — that is the whole point of going to the infrared. For a fun contrast, also try `JWST` to see the star far into the IR.

{{< /details >}}

> [!CAUTION]
> Syntax matters. The `instrument` path should **not** end in a `/`, but the `stellar_atm` path **should**. If the module can't find your filters, a stray slash is the first thing to check.

### 2d — Swapping the atmosphere grid

`stellar_atm` points at the grid that gets interpolated into an SED. Different grids cover different parameter ranges and physics. The prerelease ships `Kurucz2003all`, an $\alpha$-enhanced variant `Kurucz2003all__alpha_04`, and a simple blackbody grid `bbody`.

**Task:** Swap to the $\alpha$-enhanced grid and rerun.

```fortran
   stellar_atm = '/data/colors_data/stellar_models/Kurucz2003all__alpha_04/'
```

The $\alpha$ elements reshape the SED in the blue, so the colors shift slightly. For a more dramatic comparison, try `bbody/` — a pure blackbody has no spectral lines at all, so the colors show you exactly how much the real atmosphere's line blanketing was doing.

> [!NOTE]
> What if you want a grid or a filter set that *doesn't* ship with the prerelease (say, LSST)? That is exactly what Part 3 is for.

---

## Part 3: SED_Tools — building the inputs the colors module eats

Every `instrument` and `stellar_atm` path you played with in Part 2 points at a directory of files that someone had to download, standardize, and pack into the `flux_cube.bin` the colors module reads. **SED_Tools** is the companion package that does all of that. If the colors module is the *consumer* of filters and atmosphere grids, SED_Tools is the *supplier*: it discovers what exists, downloads it from the major archives (SVO, MSG/Townsend, MAST, and a pre-processed NJM mirror), standardizes units, builds the lookup tables and flux cubes, and can hand a clean folder straight to MESA. It also has a Python API so you can compute synthetic photometry interactively without running MESA at all.

This is the largest single part of the lab, because getting comfortable adding your *own* filters and atmospheres is what turns the colors module from a fixed black box into something you can point at any instrument you like.

Install it:

```bash
pip install sed-tools
```

Everything below also exists as an interactive menu — just run `sed-tools` with no arguments — and as a set of companion notebooks (`jupyter_notebooks/01`–`12`) that walk through each step in detail.

### 3a — Discover what's available

Before downloading anything, see what's out there. The Python API queries every configured source at once:

```python
from sed_tools.api import SED, Filters

# Atmosphere grids: ask all sources, or narrow by parameter coverage
for c in SED.query(teff_min=4000, teff_max=8000):
    print(c)

# Filter sets already installed locally
for f in Filters.query(include_remote=False):
    print(f)
```

`SED.query()` returns `CatalogInfo` objects describing each grid and the parameter range it covers; passing `teff_min/max`, `logg_min/max`, or `metallicity_min/max` keeps only the grids that span what you need.

### 3b — Download a new atmosphere grid

Say you want a PHOENIX grid (cooler, more line-blanketed atmospheres than Kurucz). One command downloads it and builds the lookup table, HDF5 bundle, and flux cube in one go:

```bash
sed-tools spectra --source svo --models PHOENIX --workers 8
```

Or from Python, with parameter-range filtering so you only pull the slice you need (downloads are much smaller this way):

```python
sed = SED.fetch('PHOENIX', source='svo',
                teff_min=4000, teff_max=8000,
                logg_min=1.0, logg_max=5.0,
                metallicity_min=-1.0, metallicity_max=0.5)
```

The result lands under SED_Tools' models directory as `PHOENIX/` containing the per-model SED files, `lookup_table.csv`, and `flux_cube.bin` — exactly the layout the colors module expects.

### 3c — Download a new filter set

Filters work the same way. The interactive picker browses SVO's filter profile service:

```bash
sed-tools filters
```

or fetch a specific facility/instrument directly from Python:

```python
Filters.fetch('LSST', 'LSST')        # a set that does NOT ship with the prerelease
Filters.fetch('Generic', 'Johnson')  # classic Johnson UBVRI
```

Each lands under `filters/<Facility>/<Instrument>/` as individual `.dat` transmission curves.

### 3d — Process and refine grids

Downloading is only half of it; SED_Tools also *processes* grids, which is where the real power is:

- `sed-tools rebuild --models PHOENIX` — regenerate the lookup table, HDF5 bundle, and flux cube after you've edited or added SED files.
- `sed-tools combine` — merge several grids (e.g. Kurucz for hot stars + PHOENIX for cool stars) onto a common wavelength grid into one unified "omni" grid. Also available as `SED.combine(['Kurucz2003all', 'PHOENIX'], output='omni')`.
- `sed-tools densify` — fill coarse $T_\mathrm{eff}$ gaps in an existing `flux_cube.bin` so interpolation is smoother.
- `sed-tools ml_completer` / `ml_generator` — train a model to fill missing SEDs or generate new ones (advanced; see notebooks 05–06).

### 3e — Hand it to MESA

This is the step that closes the loop with Part 2. `mesa_prepare` exports one clean, MESA-ready variant of a grid (just its `flux_cube.bin` and `lookup_table.csv`):

```bash
sed-tools mesa_prepare --model PHOENIX --output PHOENIX_mesa
```

Drop (or symlink) the result into your colors data and point `inlist_run` at it:

```bash
ln -s "$(pwd)/PHOENIX_mesa" "$MESA_DIR/data/colors_data/stellar_models/PHOENIX"
```

```fortran
   stellar_atm = '/data/colors_data/stellar_models/PHOENIX/'
```

The same idea applies to a downloaded filter set — symlink it under `$MESA_DIR/data/colors_data/filters/<Facility>/<Instrument>` and set `instrument`. Now your Part 2 run is observing through a brand-new instrument or atmosphere that wasn't in the prerelease.

### 3f — Compute photometry in Python (no MESA needed)

The same data works directly from Python, which is the fastest, safest way to build intuition. Load a local grid, interpolate a spectrum at any $(T_\mathrm{eff}, \log g, [\mathrm{M/H}])$, and convolve it with a filter set:

```python
sed = SED.local('PHOENIX')                              # or 'Kurucz2003all'
spec = sed(teff=6000, logg=2.0, metallicity=-1.0)       # a point on the blue loop
phot = spec.photometry('GAIA', system='AB')             # dict: band -> PhotometryResult

for band, res in phot.items():
    print(f"{band:6s} {res.magnitude:8.4f} {res.system}")
```

Each `PhotometryResult` carries `.magnitude`, `.flux_density`, `.system`, and `.filter_name`.

**Task:** Sweep temperature at fixed $\log g$ and metallicity to build a synthetic color–temperature relation — it takes seconds, and the instability strip your MESA star loops through sits roughly between 5000 K and 7500 K, so watch the color there.

```python
import numpy as np
import matplotlib.pyplot as plt

teffs = np.arange(4000, 10001, 250)
colours = []
for t in teffs:
    p = sed(teff=float(t), logg=2.0, metallicity=-1.0).photometry('GAIA', system='AB')
    mags = {res.filter_name: res.magnitude for res in p.values()}
    bp = next(m for n, m in mags.items() if 'bp' in n.lower())
    rp = next(m for n, m in mags.items() if 'rp' in n.lower())
    colours.append(bp - rp)

plt.plot(teffs, colours)
plt.axvspan(5000, 7500, alpha=0.15, label='instability strip')
plt.gca().invert_xaxis()
plt.xlabel('Teff (K)'); plt.ylabel('BP - RP'); plt.legend()
plt.show()
```

> [!TIP]
> Notebook `09_synthetic_photometry.ipynb` extends this sweep into a full synthetic CMD, and `07_catalog_and_spectrum.ipynb` shows how to iterate over a whole grid as a `Catalog` of `Spectrum` objects.

---

## Part 4: Fun runs — plots and videos

Now the payoff. The lab ships a `python_helpers/` folder full of scripts that turn your colors output into plots and movies. None of them need any setup beyond a completed run with `make_csv = .true.`. Run them from inside `python_helpers/`.

```bash
cd python_helpers
ls
# plot_sed.py  plot_sed_live.py  plot_lc.py  plot_cmd.py  plot_cmd_3d.py
# movie_cmd_3d.py  plot_colorcolor.py  plot_history.py  plot_history_live.py
# movie_history.py  plot_isochrone.py
```

> [!NOTE]
> The script names below are matched to the `python_helpers/` directory; each script's exact options live in its own header. Run them from inside `python_helpers/` (they look one level up for your run's output).

### 4a — Watch the SED evolve

`plot_sed_live.py` reads the per-step SEDs your run wrote out and refreshes a window as new ones appear — run it in a second terminal *while MESA is still running* and watch the spectrum evolve in real time. As the star climbs the giant branch and loops back, the SED visibly reddens and brightens, then walks back across the instability strip. `plot_sed.py` makes a static SED figure from a finished run.

```bash
python plot_sed_live.py    # live, run alongside ./rn
python plot_sed.py         # static snapshot from a finished run
```

> [!TIP]
> For a smoother live SED across the blue loop, lower `profile_interval` in `&controls` before your run so MESA writes more SED snapshots through the loop.

### 4b — The light curve (your variable star!)

This is the one to look at first for a blue-loop star. `plot_lc.py` plots a synthetic magnitude against age — the Gaia $G$ light curve. As the star crosses and re-crosses the instability strip, $G$ brightens and fades, which is exactly the observable signature that makes these stars interesting.

```bash
python plot_lc.py
```

### 4c — Color–magnitude diagram

`plot_cmd.py` builds a CMD from your run; `plot_cmd_3d.py` adds age as a third axis and `movie_cmd_3d.py` animates it. The blue loop shows up as a hook in the CMD — the clearest single picture of the excursion.

```bash
python plot_cmd.py
python movie_cmd_3d.py     # animated 3D version
```

### 4d — Color–color diagram

`plot_colorcolor.py` plots one color against another — for a Gaia run that's $(G_{BP}-G_{RP})$ vs $(G_{RP}-G_{RVS})$. The loop traces a little hook here too, a clean way to see the excursion.

```bash
python plot_colorcolor.py
```

### 4e — History plots

`plot_history.py`, `plot_history_live.py`, and `movie_history.py` plot and animate the standard history quantities (and the magnitude columns) against age or model number — handy for lining up the photometric changes with what the interior is doing.

> [!TIP]
> All of these scripts save into the `plots/` directory. Mix and match: run the same star through Gaia and 2MASS (Part 2c), then make a light curve and a CMD for each and put them side by side.

> [!NOTE]
> **Optional bonus — animated isochrones.** `plot_isochrone.py` stitches a *grid* of runs at different masses into an isochrone and animates how it changes with age. Unlike everything above, this needs more than your single run — a set of completed runs at different masses to interpolate across. It's a heavier, self-contained detour; treat it as an extension rather than part of the core lab.

---

## Part 5: SED_Model — the Python twin

Everything so far has run *inside* MESA. **SED_Model** is the same synthetic-photometry calculation lifted out into pure Python — the twin of MESA `colors` — with one big addition: it runs in **both directions**. Its forward model is validated against the MESA colors reference outputs, so it is genuinely the same engine; its inverse model is the new superpower.

```bash
git clone https://github.com/nialljmiller/SED_Model.git
cd SED_Model
python -m pip install -e .
python setup.py build_ext --inplace   # builds the Fortran kernels
```

It reads the *same* grids and filter directories that the colors module consumes, so the inputs you've been playing with carry straight over.

### 5a — Forward direction: parameters → photometry

This is the colors module, in Python. Hand it stellar parameters and it returns the SED, bolometric quantities, and synthetic magnitudes in any loaded filters. Let's evaluate a point near the middle of the blue loop, where the star sits inside the instability strip.

```python
import os
from sed_model import load_grid, load_filters_from_instrument_dir, run_forward

# Use any grid/filters SED_Tools built — e.g. the colors data, or your PHOENIX download
cdir = os.path.expandvars("$MESA_DIR/data/colors_data")
grid = load_grid(f"{cdir}/stellar_models/Kurucz2003all")
filters = load_filters_from_instrument_dir(f"{cdir}/filters/GAIA/GAIA")

result = run_forward(
    teff=6000, logg=2.0, meta=-1.0,   # a Cepheid-like point on the loop
    R=2.5e12,          # ~36 R_sun, in cm
    d=3.0857e19,       # 10 pc -> absolute magnitudes
    grid=grid, filters=filters,
    mag_system="Vega",
)

print(result.magnitudes)   # dict of band -> magnitude
print(result.bol_mag)      # bolometric magnitude
```

The ready-to-run `demos/demo_forward.py` does exactly this and plots the SED with the filter pivot wavelengths and a magnitude bar chart. Compare its numbers to your MESA `colors` history at the same point on the loop — they should agree.

### 5b — Inverse direction: photometry → parameters

This is what MESA `colors` *cannot* do. Give SED_Model a set of observed magnitudes with uncertainties and it runs an MCMC to recover a posterior over $(T_\mathrm{eff}, \log g, [\mathrm{M/H}])$ — and optionally $A_V$ and distance.

```python
from sed_model import run_inverse

posterior = run_inverse(
    obs_magnitudes=[ ... ],          # e.g. the G, Gbp, Grp you just produced
    obs_uncertainties=[0.02, 0.02, 0.02],
    filter_names=["G", "Gbp", "Grp"],
    R=2.5e12, d=3.0857e19,
    grid=grid, filters=filters,
    mag_system="Vega",
    n_walkers=32, n_steps=1000, n_burn=300,
)

posterior.print_summary()
```

The free/fixed/bounded behaviour of each parameter is controlled through a shared `FitParams` object, so the *same* parameter language flows in both directions — forward and inverse are two views of one model. `demos/demo_inverse.py` synthesizes observations from known parameters and shows the recovery as a corner plot, so it runs out of the box even before you have real data.

> [!NOTE]
> The two directions share `FitParams`, the grid, and the filters. A clean way to convince yourself it all hangs together: take the magnitudes you made in 5a, feed them straight into `run_inverse`, and check that the posterior recovers $T_\mathrm{eff}=6000$ K. That round-trip is the heart of the SED_Model test suite.

---

## Where to go next

You now have the full toolchain: **SED_Tools** builds the inputs, the MESA **colors** module consumes them while the star loops across the instability strip, the `python_helpers` scripts visualize the output, and **SED_Model** reproduces the whole calculation in Python while adding parameter fitting. Pick a filter system you've never used, download it with SED_Tools, run the blue loop through it, watch the light curve and SED, and then fit the magnitudes back with SED_Model — that single loop touches every tool in this lab.
