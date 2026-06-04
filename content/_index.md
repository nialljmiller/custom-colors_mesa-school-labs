+++
date = '2026-04-06T13:38:04+02:00'
draft = false
title = 'Lab 4 - A Synthetic Photometry Playground: Colors, SED_Tools & SED_Model'
+++

*Authors: Niall Miller — MESA Summer School 2026, Tetons, Wyoming*

In [Lab 2](../lab-2) we switched on the MESA `colors` module and watched a single track sweep across a synthetic color–magnitude diagram. This lab is the playground that follows. We are not building anything from scratch and we are not changing any stellar physics — we are going to *play* with the colors module: swap its inputs around, watch what changes, and make some fun plots and movies out of the results. Along the way we will meet `colors`' companion tool, **SED_Tools**, which is where all of those filter and atmosphere inputs actually come from, and we will finish by meeting **SED_Model**, the pure-Python twin of MESA `colors`.

Everything here is safe to poke at. We work on a *copy* of a lab directory, every run is short, and every change is reversible — if a run goes sideways, you delete the output folder and try again. The goal is exploration, not a deliverable.

{{< cards >}}
{{< card link="https://github.com/nialljmiller/custom-colors_mesa-school-labs/raw/main/customcol_lab.zip" title="Download Lab Files" subtitle="The customcol_lab work directory, inlists, and python_analysis scripts used throughout." >}}
{{< card link="https://github.com/nialljmiller/SED_Tools" title="SED_Tools" subtitle="Download and standardize filters and stellar atmosphere grids for the colors module." >}}
{{< card link="https://github.com/nialljmiller/SED_Model" title="SED_Model" subtitle="The Python twin of MESA colors — forward synthetic photometry and parameter fitting." >}}
{{< /cards >}}

---

## What you will do

| Part | Topic |
|------|-------|
| 1 | Recap and a quick `colors` run |
| 2 | Altering the `colors` module inputs |
| 3 | SED_Tools — the companion that supplies those inputs |
| 4 | Fun runs: plots and videos from the `python_analysis` scripts |
| 5 | SED_Model — the Python twin (forward *and* inverse) |

---

## Part 1: Recap and a quick run

The colors module turns the things MESA already computes ($T_\mathrm{eff}$, $\log g$, $L$) into the things observers actually measure: synthetic magnitudes in a chosen filter system. It does this by interpolating a stellar atmosphere grid to get an SED, convolving that SED with each filter's transmission curve, and calibrating against a reference spectrum (Vega or AB).

Let's start from a fresh copy of the colors lab so nothing we do here touches your Lab 2 work:

```bash
cp -r customcol_lab playground_lab
cd playground_lab
./clean
./mk
```

Open `inlist_project` and find the `&colors` namelist. It should look like this:

```fortran
&colors
   use_colors = .true.                                 ! turn the module on
   instrument = '/colors/data/filters/GAIA/GAIA'       ! filter system directory
   stellar_atm = '/colors/data/stellar_models/Kurucz2003all/'  ! atmosphere grid
   vega_sed = '/colors/data/stellar_models/vega_flam.csv'      ! zero-point reference
   distance = 3.0857d19         ! 10 pc in cm -> absolute magnitudes
   make_csv = .true.            ! write a full SED per filter (needed for SED plots)
   colors_results_directory = 'SED'
/ ! end of colors namelist
```

> [!NOTE]
> Confirm `pgstar_flag = .true.` in `&star_job` so you get the live plots, then run a quick model:

```bash
./rn
```

You now have a baseline run with Gaia magnitudes in `LOGS/`, and a full SED written to `LOGS/SED/` at each step. That baseline is the thing we will spend the rest of the lab altering and visualizing.

---

## Part 2: Altering the colors module inputs

This is the heart of the lab. Every interesting thing the colors module does is controlled by a handful of lines in `&colors`. We will change them one at a time and rerun, so you can see exactly what each knob does. Make a habit of changing the output history name each time so your runs don't overwrite each other — that is what keeps this safe.

Here is the full menu of knobs:

| Parameter | What it controls | Try changing it to… |
|-----------|------------------|---------------------|
| `instrument` | which filter system you observe in | `2MASS`, `LSST`, `Generic/Johnson` |
| `stellar_atm` | the atmosphere grid that becomes the SED | a different Kurucz `alpha` set, or a grid from SED_Tools |
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

The `instrument` path points at a *directory* of filter transmission curves. The colors lab already ships with several. Point `instrument` at a different one and you are suddenly observing the same star with a different telescope.

**Task:** Observe your star in 2MASS (near-infrared $J$, $H$, $K_s$) instead of Gaia.

{{< details title="Solution" closed="true" >}}

```fortran
   instrument = '/colors/data/filters/2MASS/2MASS'
```

Your history file now has `J`, `H`, and `Ks` columns instead of `G`, `Gbp`, `Grp`. A cool star will look comparatively much brighter here than it did in Gaia — that is the whole point of going to the infrared.

{{< /details >}}

> [!CAUTION]
> Syntax matters. The `instrument` path should **not** end in a `/`, but the `stellar_atm` path **should**. If the module can't find your filters, a stray slash is the first thing to check.

### 2d — Swapping the atmosphere grid

`stellar_atm` points at the grid that gets interpolated into an SED. Different grids cover different parameter ranges and use different physics (for example, different $\alpha$-enhancement). Swapping the grid changes the underlying spectrum before it ever hits a filter.

**Task:** Try a different Kurucz `alpha` set that ships with the lab and rerun.

```fortran
   stellar_atm = '/colors/data/stellar_models/Kurucz2003all__alpha_04/'
```

If you compare a low-metallicity star across the two grids you should see small but real differences in the colors — the $\alpha$ elements reshape the SED in the blue.

> [!NOTE]
> What if you want a grid or a filter set that *doesn't* ship with the lab? That is exactly what Part 3 is for.

---

## Part 3: SED_Tools — where the inputs come from

Every `instrument` and `stellar_atm` path you just played with points at a directory of files. **SED_Tools** is the companion package that downloads, standardizes, and builds those directories. If the colors module is the consumer, SED_Tools is the supplier. It also has a Python API, so you can explore synthetic photometry interactively *without running MESA at all* — which is the fastest, safest way to get a feel for how colors behave.

Install it:

```bash
pip install sed-tools
```

### 3a — Getting new filters and atmospheres for `colors`

SED_Tools has both an interactive menu and direct commands. The two you care about for feeding the colors module are `filters` and `spectra`:

```bash
# Download a filter transmission set (e.g. LSST)
sed-tools filters

# Download a stellar atmosphere grid
sed-tools spectra

# Build the flux cube + lookup table the colors module expects
sed-tools rebuild
```

The download lands under `data/filters/<Facility>/<Instrument>/` and `data/stellar_models/<Grid>/`, which is exactly the layout the colors module reads. To use a freshly downloaded set, copy (or symlink) it into your MESA install and point your inlist at it:

```bash
# symlink is recommended so you don't duplicate large grids
ln -s $(pwd)/data/filters/LSST/LSST $MESA_DIR/colors/data/filters/LSST/LSST
```

```fortran
   instrument = '/colors/data/filters/LSST/LSST'
```

That closes the loop on Part 2: SED_Tools is how you get *new* inputs to alter the colors module with.

### 3b — Exploring photometry in Python (no MESA needed)

The same data works directly from Python through the SED_Tools API. This is the playground inside the playground — you can interpolate a spectrum and compute synthetic magnitudes in a couple of lines. The companion notebooks (`jupyter_notebooks/01`–`09`) walk through every method; here is the gist.

```python
from sed_tools.api import SED, Filters

# Load a local grid and make sure some filters are present
sed = SED.local('Kurucz2003all')
Filters.fetch('GAIA', 'GAIA')

# Interpolate the Sun's spectrum, then get synthetic Gaia magnitudes
spectrum = sed(teff=5777, logg=4.44, metallicity=0.0)
phot = spectrum.photometry('Gbp', 'Grp', system='AB')

for band, result in phot.items():
    print(f"{band:4s}: {result.magnitude:.4f} AB mag")
```

**Task:** Sweep temperature at fixed $\log g$ and metallicity to build a synthetic color–temperature relation — the simplest possible "fun colors run," and it takes seconds.

```python
import numpy as np
import matplotlib.pyplot as plt

teffs = np.arange(4000, 10001, 250)
bp_rp = []
for t in teffs:
    spec = sed(teff=float(t), logg=4.5, metallicity=0.0)
    p = spec.photometry('Gbp', 'Grp', system='AB')
    bp_rp.append(p['Gbp'].magnitude - p['Grp'].magnitude)

plt.plot(teffs, bp_rp)
plt.gca().invert_xaxis()
plt.xlabel('Teff (K)'); plt.ylabel('BP - RP')
plt.show()
```

> [!TIP]
> `SED.query()` lists every grid available to download, and `Filters.query(include_remote=False)` lists what you already have locally. Notebook `09_synthetic_photometry.ipynb` extends this exact sweep into a full synthetic CMD from a catalog subset.

---

## Part 4: Fun runs — plots and videos

Now the payoff. The lab ships a `python_analysis/` folder full of scripts that turn your colors output into plots and movies. None of them need any setup beyond a completed run with `make_csv = .true.`. Run them from inside `python_analysis/`.

```bash
cd python_analysis
ls
# SED_check.py  plot_cmd.py  plot_colorcolor.py  plot_isochrone.py
```

### 4a — Watch the SED evolve (movie!)

`SED_check.py` reads the per-step SEDs in `LOGS/SED/` and animates them. It can either pop up a live, refreshing window or render the whole thing to a video file. This is the single most satisfying thing to watch — the spectrum visibly reddens and dims as the star evolves.

```bash
python SED_check.py
```

To save it as a movie instead of watching live, set `save_video=True` in the `SEDChecker(...)` call at the bottom of the script. It writes an `.mp4` of the SED with the filter convolution overlaid.

### 4b — Color–magnitude diagram

`plot_cmd.py` builds a CMD from your run and colors the track by a physics parameter of your choice (evolutionary phase, core hydrogen, age…). It saves a 2D CMD and, optionally, a 3D version with age on the vertical axis.

```bash
python plot_cmd.py
```

### 4c — Color–color diagram

`plot_colorcolor.py` plots one color against another — for a Gaia run that's $(G_{BP}-G_{RP})$ vs $(G_{RP}-G_{RVS})$. Color–color space is where stellar populations separate cleanly, so this is a good one to run after you've made several runs in Part 2.

```bash
python plot_colorcolor.py
```

### 4d — Animated isochrones (GIF!)

`plot_isochrone.py` works across a *batch* of runs at different masses and stitches them into an isochrone, then animates how that isochrone changes with age into a GIF. If you've collected a few runs (or use the `batch_runs/` directory that ships with the lab) this produces a genuinely lovely little movie.

```bash
python plot_isochrone.py
```

It will ask whether you want HR-diagram coordinates, a 3D version, and an animated GIF — say yes to the GIF.

> [!TIP]
> All of these scripts save into a `plots/` directory. Mix and match: run the same star through Gaia and 2MASS (Part 2c), then make a CMD for each and put them side by side.

---

## Part 5: SED_Model — the Python twin

Everything so far has run *inside* MESA. **SED_Model** is the same synthetic-photometry calculation lifted out into pure Python — the twin of MESA `colors` — with one big addition: it runs in **both directions**. Its forward model is validated against the MESA colors reference outputs, so it is genuinely the same engine; its inverse model is the new superpower.

```bash
git clone https://github.com/nialljmiller/SED_Model.git
cd SED_Model
python -m pip install -e .
python setup.py build_ext --inplace   # builds the Fortran kernels
```

It reads the *same* grids and filter directories that SED_Tools builds and the colors module consumes, so all the inputs you've been playing with carry straight over.

### 5a — Forward direction: parameters → photometry

This is the colors module, in Python. Hand it stellar parameters and it returns the SED, bolometric quantities, and synthetic magnitudes in any loaded filters.

```python
from sed_model import load_grid, load_filters_from_instrument_dir, run_forward

grid = load_grid("~/SED_Tools/data/stellar_models/Kurucz2003all")
filters = load_filters_from_instrument_dir("~/SED_Tools/data/filters/Generic/Johnson")

result = run_forward(
    teff=5778, logg=4.44, meta=0.0,
    R=6.957e10,        # 1 R_sun, in cm
    d=3.0857e19,       # 10 pc -> absolute magnitudes
    grid=grid, filters=filters,
    mag_system="Vega",
)

print(result.magnitudes)   # dict of band -> magnitude
print(result.bol_mag)      # bolometric magnitude
```

The ready-to-run `demos/demo_forward.py` does exactly this and plots the SED with the filter pivot wavelengths and a magnitude bar chart. Compare its numbers to a MESA `colors` run with the same parameters — they should agree.

### 5b — Inverse direction: photometry → parameters

This is what MESA `colors` *cannot* do. Give SED_Model a set of observed magnitudes with uncertainties and it runs an MCMC to recover a posterior over $(T_\mathrm{eff}, \log g, [\mathrm{M/H}])$ — and optionally $A_V$ and distance.

```python
from sed_model import run_inverse

posterior = run_inverse(
    obs_magnitudes=[5.03, 4.17],
    obs_uncertainties=[0.01, 0.02],
    filter_names=["G", "J"],
    R=6.957e10, d=3.0857e19,
    grid=grid, filters=filters,
    mag_system="Vega",
    n_walkers=32, n_steps=1000, n_burn=300,
)

posterior.print_summary()
```

The free/fixed/bounded behaviour of each parameter is controlled through a shared `FitParams` object, so the *same* parameter language flows in both directions — forward and inverse are two views of one model. `demos/demo_inverse.py` synthesizes observations from known parameters and shows the recovery as a corner plot, so it runs out of the box even before you have real data.

> [!NOTE]
> The two directions share `FitParams`, the grid, and the filters. A clean way to convince yourself it all hangs together: run `run_forward` to make magnitudes, feed those magnitudes straight into `run_inverse`, and check that the posterior recovers the parameters you started with. That round-trip is the heart of the SED_Model test suite.

---

## Where to go next

You now have the full toolchain: **SED_Tools** builds the inputs, the MESA **colors** module consumes them during evolution, the `python_analysis` scripts visualize the output, and **SED_Model** reproduces the whole calculation in Python while adding parameter fitting. Pick a filter system you've never used, download it with SED_Tools, run a track through it, make a movie of the SED, and then fit the final magnitudes back with SED_Model — that single loop touches every tool in this lab.
