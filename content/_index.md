# MESA Custom Colors Lab: Synthetic Photometry in Stellar Evolution
## Complete Summer School Guide

---
{{< cards >}}
{{< card link="https://github.com/nialljmiller/custom-colors_mesa-school-labs/raw/main/customcol_lab.zip" title="📥 Download Lab Files" subtitle="Download all MESA simulation files, inlists, and Python scripts needed for this lab." >}}
{{< card link="https://zenodo.org/records/16092864" title="🌈 Download MESA Color System" subtitle="Get the mesa-2025-summerschool-prerelease.zip with photometric color calculations from Zenodo." >}}
{{< /cards >}}
---

## Overview

This tutorial teaches you to integrate synthetic photometry calculations into stellar evolution models, bridging theoretical stellar physics with observational astronomy.

### Lab Structure

| Part | Topic |
|------|-------|
| 0 | Installation & Setup |
| 1 | Configuration & Physics |
| 2 | Running a Model |
| 3 | Python Visualization |
| 4 | Batch Runs |
| 5 | More Python Visualization |

---

### Why Custom Colors?

Standard MESA provides fundamental stellar properties ($T_\text{eff}$, $\log g$, $L_\text{bol}$), but observers measure **magnitudes** and **colors** through specific filters. The custom colors module bridges this gap by:

- Computing synthetic spectral energy distributions (SEDs)
- Convolving with astronomical filter transmission curves
- Providing magnitudes in standard photometric systems

This enables direct comparison between stellar evolution models and observational surveys like Gaia, SDSS, and 2MASS.

---

## Part 0: Installation and Setup

### Step 0.1: Download Pre-Release Version

**Important**: This lab uses an unofficial MESA pre-release with the custom colors module. The module will be integrated into the main MESA distribution in a future release **very** soon.

Ensure you have downloaded both files from the links above.


#### Extract the Archive

**You cant just copy and paste these commands as you need to specify *your* filepath.**

```bash
# Navigate to download location (If it is in an awkward place you could move it to 'home' or put it in a directory along with your other MESA install.)
cd /path/to/your/mesa/installations/

# Extract the zip archive
unzip mesa-2025-summerschool-prerelease.zip

# Verify extraction
ls -la mesa-2025-summerschool-prerelease/
# Expected: Should see MESA directory structure with colors/ subdirectory
```

### Step 0.2: Environment Config

#### Update MESA_DIR

**!!Read Carefully!!**
The **most critical** step is pointing your environment to the pre-release version:

```bash
# Store current MESA_DIR (for rollback if needed)
echo "Previous MESA_DIR: $MESA_DIR"

# Update to pre-release version (adjust path as needed)
export MESA_DIR=/path/to/mesa-2025-summerschool-prerelease

# Verify the change
echo "New MESA_DIR: $MESA_DIR"
ls $MESA_DIR/colors  # Should show colors directory
```

This step is critical and it is important to ensure you have correctly completed it. 
If you are struggling or unsure, ask a TA. 


#### Make Changes Persistent (optional)

The export command is temporary and will not persist through multiple terminal windows. You can save these changes by adding/changing them in your ".[shell]rc" file.

YOU WILL NEED TO CHANGE THIS BACK TO THE OFFICIAL RELEASE FOR THE REST OF THE LABS THIS WEEK.

Choose your shell and add the export command to the appropriate configuration file:

```bash
# For bash users (.bashrc or .bash_profile)
echo 'export MESA_DIR=/path/to/mesa-2025-summerschool-prerelease' >> ~/.bashrc

# For zsh users (.zshrc)
echo 'export MESA_DIR=/path/to/mesa-2025-summerschool-prerelease' >> ~/.zshrc

# For csh/tcsh users (.cshrc)
echo 'setenv MESA_DIR /path/to/mesa-2025-summerschool-prerelease' >> ~/.cshrc

# Reload your shell configuration
source ~/.bashrc  # or appropriate file
```

#### Verify Setup

```bash
# Essential checks
echo "MESA_DIR: $MESA_DIR"
echo "MESA SDK: $MESASDK_ROOT"  # Should be set from previous MESA installations, this DOES NOT need to change. 

# Verify colors module files
ls -a $MESA_DIR/colors/private
# Expected output: Makefile, src/, data/, test_suite/, README
```

### Step 0.3: Install MESA with Custom Colors

#### Installation Process

```bash
cd $MESA_DIR

# Clean any previous builds (optional but recommended)
./clean

# Install MESA with colors module
./install

# Verify install by looking to see if colors was properly extracted.
cd $MESA_DIR/colors/data
ls -a
#You should see a hidden extracted flag file. 
```

```bash
#If this is not here try to re install with 
echo $MESA_DIR
cd $MESA_DIR
./clean; ./install
```


#### Verify Installation

```bash
# Check for successful completion
echo "Installation status: $?"  # Should be 0
ls $MESA_DIR/lib/  # Should contain many .a library files

# Test basic MESA functionality
cd $MESA_DIR/star/test_suite/custom_colors
./mk  # Should compile without errorsCustom colours has been made
```

And then hopefully:

```bash
Custom colours has been made
```

You can then edit the project_inlist file:

```bash
pgstar_flag = .true.  ! Enable real-time plotting (This is set to .false. for test hub -- .true. will enable a CMD and Light curves!!)
```

Save this and then:

```bash
./rn
```

Some synthetic lightcurve should pop up from pgstar


### Complete Installation Checklist

Verify each component before proceeding to the lab:

#### System Environment
- `$MESA_DIR` points to pre-release version
- MESA SDK properly loaded (`$MESASDK_ROOT` set)
- Fortran compiler available and compatible

#### MESA Installation
- `./install` completed successfully (exit code 0)
- Core MESA libraries present in `$MESA_DIR/lib/`
- Basic test case compiles and runs


### Troubleshooting Common Issues

#### Installation Failures

**Problem**: `./install` fails with compiler errors
```bash
# Solution: Check compiler setup
echo $MESASDK_ROOT
# Reload MESA SDK if needed
source $MESASDK_ROOT/bin/mesasdk_init.sh
```

**Problem**: Colors module not found during installation
```bash
# Solution: Verify directory structure
ls $MESA_DIR/colors/private/
# Should contain these files: colors_ctrls_io.f90  hermite_interp.f90  knn_interp.f90  linear_interp.f90  shared_funcs.f90
```

#### Data Extraction Issues

**Problem**: Photometric data extraction fails
```bash
# Solution: Manual extraction with verbose output
ls -a $MESA_DIR/colors/data
#.  ..  colors_data.txz  .extraction_complete  filters  .gitattributes  stellar_models

ls $MESA_DIR/colors/data/filters/GAIA/GAIA/ 
#GAIA  Gbp_bright.dat  Gbp.dat  Gbp_faint.dat  G.dat  Grp.dat  Grvs.dat

# If this is not there, Check for permission issues or disk space and re-install

#If you have issues with data, it is advised to delete the '.extraction_complete' file
```

For additional support or contact the lab instructor or contact Niall Miller (via mattermost or whatever is easy)

---

## Part 1: Understanding Custom Colors

### The Synthetic Photometry Pipeline

The custom colors module implements a sophisticated pipeline that converts stellar physics into observable quantities:

```
Stellar Parameters    →    Atmosphere Model    →    SED          →    Photometry
(Teff, log g, [M/H])       Interpolation            Convolution      (Magnitudes)
```

#### Stellar Atmosphere Models

For this implementation, we are using the **Kurucz 2003** atmosphere model grid covering:
- **Temperature**: 3,500 K ≤ $T_\text{eff}$ ≤ 50,000 K
- **Surface Gravity**: 0.0 ≤ $\log g$ ≤ 5.0
- **Metallicity**: -5.0 ≤ [M/H] ≤ +1.0

#### Mathematical Framework

The synthetic magnitude in filter $X$ is computed as:

$$m_X = -2.5 \log_{10}\left(\frac{\int F_\lambda(\lambda) S_X(\lambda) d\lambda}{\int F_\text{Vega}(\lambda) S_X(\lambda) d\lambda}\right)$$

Where:
- $F_\lambda(\lambda)$ = stellar flux density
- $S_X(\lambda)$ = filter transmission function
- $F_\text{Vega}(\lambda)$ = Vega reference spectrum

### Config Params

Examine the colors namelist in your `inlist_project`:

```fortran
&colors
   use_colors = .true.
   instrument = 'data/filters/GAIA/GAIA'
   vega_sed = 'data/stellar_models/vega_flam.csv'  
   stellar_atm = 'data/stellar_models/Kurucz2003all/'
   distance = 3.0857d17  ! 10 parsecs for absolute magnitudes
   make_csv = .false.     ! Enable for detailed SED output
/
```

| Parameter | Purpose | Typical Values |
|-----------|---------|----------------|
| `use_colors` | Enable photometry calculations | `.true.` |
| `instrument` | Filter system directory | `'GAIA'`|
| `vega_sed` | Vega calibration file | `vega_flam.csv` |
| `stellar_atm` | Atmosphere model grid path | `'Kurucz2003all/'` |
| `distance` | Distance for flux scaling | `3.0857d17` cm (10 pc) |
| `make_csv` | Output detailed SEDs as csv files | `.false.` (performance) |

---

## Part 2: Single Model with Real-Time Photometry

### Learning Objectives
- Configure and analyze MESA's colors module for synthetic photometry
- Execute systematic real-time monitoring of stellar evolution
- Integrate pgstar visualization with Python-based spectroscopic analysis
- Develop proficiency in multi-terminal computational astrophysics workflows

---

### Step 2.1: Config Check

Before initiating model evolution, examine the sophisticated photometric configuration embedded in `inlist_project`:

```fortran
&colors
      ! Enable synthetic photometry during evolution
      use_colors = .true.
      
      ! GAIA photometric system specification
      instrument = '/colors/data/filters/GAIA/GAIA'
      
      ! Vega zero-point calibration spectrum
      vega_sed = '/colors/data/stellar_models/vega_flam.csv'
      
      ! Kurucz 2003 stellar atmosphere model grid
      stellar_atm = '/colors/data/stellar_models/Kurucz2003all/'
      
      ! Observational parameters
      distance = 3.0857d16         ! 1 parsec in cm
      make_csv = .true.            ! Enable detailed SED output
/ ! end of colors namelist
```

| Configuration Component | Physical Implementation | Computational Output |
|------------------------|------------------------|---------------------|
| **Filter System** | GAIA transmission curves | G, G_BP, G_RP, G_RVS magnitudes |
| **Atmosphere Grid** | Kurucz T_eff: 3500-50000 K | Interpolated surface flux |
| **Calibration** | Vega spectrum reference | Magnitude zero-point: 0.0 |
| **Distance Scaling** | $m - M = 5\log_{10}(d/10\text{pc})$ | Apparent magnitude conversion |

---

### Step 2.2: Model Execution

Execute the stellar evolution calculation with integrated photometric output:

```bash
./rn
```

#### Expected Terminal Output Sequence

```
Loading stellar atmosphere models from data/stellar_models/Kurucz2003all/
Model grid spans: Teff [3500-50000], log_g [0.0-5.0], [M/H] [-5.0,+1.0]
Using GAIA photometric system: Gbp, G, Grp
Computing synthetic photometry at each timestep...

model    age/yr    log_Teff    log_L    Gbp      G        Grp
    1   0.000E+00     3.764   -0.023   4.832   4.721   4.598
   50   1.234E+06     3.763   -0.021   4.829   4.719   4.596
  100   2.501E+06     3.762   -0.019   4.826   4.717   4.594
```

---

### Step 2.3: Pgstar Real-Time Plots

**Observe the pgstar interface** as it displays multi-panel evolutionary diagnostics:

#### Window 1:

| Panel Position | Diagnostic Function | Physical Interpretation |
|----------------|-------------------|------------------------|
| **Top Span** | Text Summary | Real-time parameter monitoring |
| **Middle Left** | HR Diagram | L vs T_eff evolutionary track |
| **Middle Right** | History Panels | Convective core mass evolution |
| **Bottom Left** | Kippenhahn | Temporal convective structure |
| **Bottom Right** | Mixing Profile | Current internal composition |

#### Window 2: G-Band Evolution

The dedicated photometric window displays:
- **X-axis**: Stellar age (years)
- **Y-axis**: GAIA G magnitude
- **Real-time updates**: Magnitude evolution during stellar phases
- **Physical significance**: Direct connection between internal physics and observables

**Key observation targets during pgstar monitoring**:
1. **Pre-main sequence contraction**: Rapid T_eff and L evolution
2. **ZAMS arrival**: Stabilization of nuclear burning
3. **Main sequence evolution**: Gradual photometric changes
4. **Convective core development**: Mass coordinate evolution

---

### Step 2.4: Python Analysis

**Open a new terminal** while the MESA model is still running:

```bash
# Navigate to analysis directory
cd python_analysis
```

#### Directory Structure

```
python_analysis/
├── SED_check.py           # Real-time spectroscopic analysis
├── HISTORY_check.py       # Multi-panel evolutionary monitoring
└── [additional tools]     # Extended analysis capabilities
```

---

## Part 3: Live Python Plots

---

### Step 3.1: Real-Time SED

**Run the SED tool** while MESA continues evolution:

```bash
python SED_check.py
```

#### Advanced SED Analysis Framework

The `SED_check.py` tool plots the csv output from custom colors:

```python
# Core monitoring parameters
class SEDChecker:
    wavelength_range = [600, 10000]    # Optical/near-IR coverage (Å)
    refresh_interval = 1               # Update frequency (seconds)
    directory = "../LOGS/SED/"         # MESA SED output location
    xlim = [600, 10000]               # Spectral window
    ylim = None                        # Automatic flux scaling
```

#### Some Spectroscopic Features to Monitor

**Balmer Jump Evolution** (λ ≈ 3646 Å):
- **Physical origin**: Hydrogen opacity discontinuity
- **Evolutionary signature**: Varies with surface gravity and temperature
- **Photometric impact**: Affects blue magnitude calibrations

**Paschen Continuum** (λ > 8200 Å):
- **Physical origin**: Near-infrared hydrogen opacity
- **Temperature sensitivity**: Strong T_eff dependence
- **Color index impact**: Drives red photometric evolution

---

### Step 3.2: Evolution Monitoring

**Launch the python history visualizer**:

```bash
python HISTORY_check.py
```


The `HISTORY_check.py` system provides real-time evolutionary tracking:

```python
# Multi-panel configuration (2×2 grid)
panel_layout = {
    'top_left': 'Color_Magnitude_Diagram',     # Observational plane
    'top_right': 'Classical_HR_Diagram',       # Physical parameter space
    'bottom_left': 'Color_Evolution',          # Temporal color analysis
    'bottom_right': 'Multi_Band_Lightcurves'   # Filter-specific evolution
}
```

#### Panel-Specific Analysis Guidelines

**Top-Left: Color-Magnitude Diagram**
```python
# Automated filter detection and color construction
if 'Gbp' in filter_columns and 'Grp' in filter_columns:
    color_index = md.Gbp - md.Grp      # GAIA color
    magnitude = md.G                    # GAIA magnitude
```

**Top-Right: Classical HR Diagram**
- T_eff vs Log L with inverted temperature axis
- Direct stellar physics visualization

**Bottom-Left: Color Evolution**
- Temporal color index analysis: $\frac{d(\text{color})}{dt}$

**Bottom-Right: Multi-Band Light Curves**
- Simultaneous G, G_BP, G_RP evolution

---
You are free to change the parameters of the inlist and re run this set up.

Move on to Part 4 and/or 5 if you are ready to move on to population analysis using cutom colors.

---
---

## Part 4: Batch Models and Parameter Studies (OPTIONAL)

### Step 4.1: Preparing the Parameter Grid

After completing all previous steps, navigate to the batch runs directory to examine the pre-configured parameter space

You do not actually need to run part 4, the plotting scripts in part 5 will still produce some figures with just the output from part 3.

```bash
cd batch_runs
cat ../Lab1.csv
```

#### Parameter Grid
The `Lab1.csv` contains a focused parameter study designed for efficient exploration:

| Parameter | Values | Physical Impact |
|-----------|--------|----------------|
| **Mass** | 2, 5, 7, 10 M☉ | Evolutionary timescales, final outcomes |
| **Metallicity** | Z = 0.0014, 0.014 | Opacity, stellar winds |
| **Overshooting** | None, exponential, step | Convective mixing efficiency |

**Optional**: Edit `Lab1.csv` to customize your parameter space:
- Add/remove mass values, metallicity values, overshooting parameters...


### Step 4.2: Batch Execution Pipeline

Execute the automated workflow (run one by one):

```bash
# Verify environment setup
python 0_dependency_check.py

# Generate individual inlists from CSV
python 1_make_batch.py ../Lab1.csv

# Validate inlist creation
python 2_verify_inlists.py ../Lab1.csv

# Execute full parameter grid
python 3_run_batch.py

# Check run completion status
python 4_verify_outlists.py ../Lab1.csv

# Extract photometric data
python 5_construct_output.py
```

---

## Part 5: More Python Plots!!


After batch has finished, move to the python analysis folder:

```bash
cd ../python_analysis
ls *.py
```


### Color Magnitude Diagram
```bash
python plot_cmd.py
```

**Single Model Output:**
- **2D CMD Plot**: Shows evolutionary track colored by central hydrogen abundance (center_h1)
  - Red circle: Main sequence start
  - Blue square: Final evolutionary state
  - Color progression shows hydrogen depletion over time
  
- **3D CMD Plot**: Same track with age as vertical axis
  - Green dot: Zero-age main sequence
  - Red square: Terminal point
  - Trajectory shows how color and magnitude evolve simultaneously

**Batch Model Output:**
- **Comparative 2D CMD**: Multiple evolutionary tracks overlaid
  - Different colors represent different stellar masses
  - Line styles distinguish overshooting prescriptions:
    - Dashed lines: No overshooting
    - Solid lines: Exponential overshooting  
    - Dotted lines: Step overshooting

- **3D Batch Visualization**: All tracks in age-color-magnitude space

**Generated Files:**
```
plots/
├── cmd_gaia_center_h1.png     # Single model 2D
├── cmd_3d_gaia_age.png        # Single model 3D
├── batch_cmd_gaia.png         # Batch 2D comparison
└── batch_cmd_3d_gaia_age.png  # Batch 3D comparison
```


### Color-Color Plots
```bash
python plot_colorcolor.py
```

**Single Model Output:**
- **2D Color-Color Plot**: GAIA (Gbp-Grp) vs (Grp-Grvs) colored by central hydrogen abundance
  - Red circle: Evolutionary start point
  - Blue square: Final state
  - Track reveals temperature-metallicity degeneracies

- **3D Color-Color Plot**: Same colors with age as vertical axis
  - Green dot: Zero-age main sequence
  - Red square: Terminal point
  - Shows color evolution timing

**Batch Model Output:**
- **Comparative 2D Plots**: Multiple evolutionary tracks in color-color space
  - Color coding represents stellar mass
  - Same as before, line styles distinguish overshooting prescriptions:
    - Solid lines: No overshooting
    - Dashed lines: Exponential overshooting
    - Dash-dot lines: Step overshooting

- **3D Batch Visualization**: All tracks with effective temperature as vertical axis

**Generated Files:**
```
plots/
├── colorcolor_gaia_center_h1.png     # Single model 2D
├── colorcolor_3d_gaia_center_h1.png  # Single model 3D
├── batch_colorcolor_gaia_mass.png    # Batch 2D comparison
└── batch_colorcolor_3d_gaia_mass.png # Batch 3D comparison
```


### Light Curves

```bash
python plot_lc.py
```

**Single Model Output:**
- **2D Lightcurve**: G-band magnitude vs age colored by central hydrogen abundance
  - Red circle: Evolutionary start point
  - Blue square: Final state  
  - Inverted y-axis (fainter stars higher)

- **3D Multi-Filter Plot**: Multiple photometric bands with wavelength as vertical axis
  - Shows how different filters evolve simultaneously

**Batch Model Output:**
- **Comparative Lightcurves**
  - Color coding represents stellar mass
  - Line styles distinguish overshooting prescriptions:
    - Solid lines: No overshooting
    - Dashed lines: Exponential overshooting
    - Dash-dot lines: Step overshooting

- **3D Batch Visualization**: All tracks with effective temperature as vertical axis
  - Reveals temperature-brightness evolution relationships

**Generated Files:**
```
plots/
├── lightcurve_g_center_h1.png           # Single model 2D
├── lightcurve_3d_multifilter_center_h1.png # Single model 3D
├── batch_lightcurve_g_mass.png          # Batch 2D comparison  
└── batch_lightcurve_3d_g_mass.png       # Batch 3D comparison
```


### Isochrones and Tracks

```bash
python plot_isochrone.py
```

**Interactive 2D Isochrone Plot:**

* **Age Slider**: Drag to view a population snapshot at a specific stellar age
* **Stellar Positions**: Interpolated from evolutionary tracks at the selected age
* **Color Coding**: Different stellar masses shown in distinct colors
* **Marker Shapes**: Circle (no overshooting), triangle (exponential), square (step)
* **Note**: Each frame represents a proper **isochrone** — i.e., a constant-age cut through all models

**Interactive 3D Evolutionary Tracks:**

* **Full Tracks**: Continuous paths through color–magnitude–age space
* **Age Window**: Slider reveals evolutionary progress up to selected age
* **Viewing Controls**: Rotate and zoom to inspect 3D stellar trajectories

**Animated Isochrone Evolution:**

* **GIF Export**: Sequence of isochrones across time rendered as animation
* **Population Aging**: Observe the changing CMD/HRD morphology with age
* **Note**: Each frame is a snapshot isochrone; animation shows their progression

**Generated Files:**

```
plots/
├── isochrone_hr_age_[X.X]Myr.png      # 2D isochrones at key ages
├── isochrone_3d_hr_age_[X.X]Myr.png   # 3D evolutionary snapshots
└── isochrone_hr_evolution.gif         # Animated sequence of isochrones
```

---



## Troubleshooting and FAQs

### Common Installation Issues

**Problem**: MESA_DIR not updated correctly
```bash
# Solution: Verify environment
echo $MESA_DIR
source ~/.bashrc  # Reload shell configuration
```

**Problem**: Python plotting failures

Ensure each of the require python packages are installed 

```bash
# Install required packages
pip install mesa_reader
pip install matplotlib 
pip install numpy 
pip install scipy 
pip install pandas
```

### Help

- **MESA Forum**: https://lists.mesastar.org/
- **Lab Developer**: Niall Miller (nmille39@uwyo.edu)
- **Summer School Instructors** 
