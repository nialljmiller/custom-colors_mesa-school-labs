# MESA Custom Colors Lab: Synthetic Photometry in Stellar Evolution
## Complete Summer School Guide

---
{{< cards >}}
{{< card link="https://github.com/nialljmiller/custom-colors_mesa-school-labs/raw/main/customcol_lab.zip" title="Download Lab Files" subtitle="Download all MESA simulation files, inlists, and Python scripts needed for this lab." >}}
{{< card link="https://zenodo.org/records/16092864" title="Download MESA Color System" subtitle="Get the mesa-2025-summerschool-prerelease.zip with photometric color calculations from Zenodo." >}}
{{< /cards >}}
---

## Overview

This lab shows you how to add synthetic photometry to stellar evolution models, linking MESA outputs to real observational data.

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

With this, you can directly compare your models to real observations from Gaia, SDSS, or 2MASS.

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

**YOU WILL NEED TO CHANGE THIS BACK TO THE OFFICIAL RELEASE FOR THE REST OF THE LABS THIS WEEK.**

Open your rc file (.bashrc, .zshrc, etc.) in your preferred editor and add this function:

```bash
function mesa-colors {
    export MESA_DIR=/path/to/mesa-2025-summerschool-prerelease
    export MESASDK_ROOT=/path/to/mesasdk
    source $MESASDK_ROOT/bin/mesasdk_init.sh
    export OMP_NUM_THREADS=16
    echo "environment set for 2025 Custom Colors pre-release"
    echo "OMP_NUM_THREADS set to 16"
}
```

Then reload your shell configuration:
```bash
source ~/.bashrc  # or appropriate file
```

After adding this function, you can type `mesa-colors` and `mesa-24081` in termial to switch between releases.

#### Verify Setup

```bash
# Essential checks
echo "MESA_DIR: $MESA_DIR"
echo "MESA SDK: $MESASDK_ROOT"  # Should be set from previous MESA installations, this DOES NOT need to change. 

# Verify colors module files
ls $MESA_DIR/colors/private
# You should see: colors_ctrls_io.f90  hermite_interp.f90  knn_interp.f90  linear_interp.f90  shared_funcs.f90
#These are new functions that the colors module uses. 
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
ls $MESA_DIR/colors/data/filters/GAIA/GAIA #There should be a bunch of filter files G.dat, Gbp.dat ...

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

A synthetic lightcurve should pop up from pgstar


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
# Check compiler setup
echo $MESASDK_ROOT
# Reload MESA SDK if needed
source $MESASDK_ROOT/bin/mesasdk_init.sh
```

**Problem**: Colors module not found during installation
```bash
ls $MESA_DIR/colors/private/
# Should contain these files: colors_ctrls_io.f90  hermite_interp.f90  knn_interp.f90  linear_interp.f90  shared_funcs.f90
```

#### Data Extraction Issues

**Problem**: Photometric data extraction fails
```bash
ls -a $MESA_DIR/colors/data
#.  ..  colors_data.txz  .extraction_complete  filters  .gitattributes  stellar_models

ls $MESA_DIR/colors/data/filters/GAIA/GAIA/ 
#GAIA  Gbp_bright.dat  Gbp.dat  Gbp_faint.dat  G.dat  Grp.dat  Grvs.dat

# If this is not there, Check for permission issues or disk space and re-install

#If you have issues with data, it is advised to delete the '.extraction_complete' file
```

For additional support or contact the lab instructor or contact Niall Miller 

---

## Part 1: Understanding Custom Colors

### The Synthetic Photometry Pipeline

The custom colors module turns model parameters into observable magnitudes using atmosphere models and filters:

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

Open the colors namelist in your `inlist_project`:

```fortran
&colors
   use_colors = .true.
   instrument = '/colors/data/filters/GAIA/GAIA'
   vega_sed = '/colors/data/stellar_models/vega_flam.csv'  
   stellar_atm = '/colors/data/stellar_models/Kurucz2003all/'
   distance = 3.0857d17  ! 10 parsecs for absolute magnitudes
   make_csv = .false.     ! You can enable this for SED output
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

### Step 2.1: Config Check

Before running the model, open the configuration in `inlist_project`:

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
      distance = 3.0857d17         ! 10 parsec in cm
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
### Step 2.2 Running The Custom Colors Lab


Download and extract the custom colors lab from the link at the top of this page. 
Use the terminal to move to the lab.

```bash
cd path/to/customcol_mesa-school-labs/customcol_lab
ls
```
You should see this:

```bash
batch_runs  clean  completed_inlists  inlist  inlist_pgstar  inlist_project  LOGS  make  mk  my_history_columns.list  my_profile_columns.list  photos  python_analysis  re  rn  src  star

```


### Step 2.3: Model Execution

Execute the stellar evolution calculation with integrated photometric output:

```bash
./clean
./mk
```

You should go into the inlist_project file and ensure pgstar_flag is set to true as we did before. 

```bash
./rn
```


---

### Step 2.4: Pgstar Real-Time Plots


#### Window 1 (from previous labs):

| Panel Position | Diagnostic Function | Physical Interpretation |
|----------------|-------------------|------------------------|
| **Top Span** | Text Summary | Real-time parameter monitoring |
| **Middle Left** | HR Diagram | L vs T_eff evolutionary track |
| **Middle Right** | History Panels | Convective core mass evolution |
| **Bottom Left** | Kippenhahn | Temporal convective structure |
| **Bottom Right** | Mixing Profile | Current internal composition |

#### Window 2: G-Band Evolution

Window 2 shows a real-time G-band light curve: age vs GAIA G magnitude
- **X-axis**: Stellar age (years)
- **Y-axis**: GAIA G magnitude
- **Real-time updates**: Magnitude evolution during stellar phases
- **Physical significance**: Direct connection between internal physics and observables


---

### Step 2.5: Python Analysis

**Open a new terminal** while the MESA model is still running:

```bash
# Navigate to analysis directory from within your custom colors lab folder 

cd path/to/customcol_mesa-school-labs/customcol_lab/python_analysis
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

After completing all previous steps, navigate to the batch runs directory to look at the pre-configured parameter space

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

**Interactive 2D Evolution Plot:**

* **Age Slider**: Drag to view a population snapshot at a specific stellar age
* **Stellar Positions**: Interpolated from evolutionary tracks at the selected age
* **Color Coding**: Different stellar masses shown in as colors
* **Marker Shapes**: Circle (no overshooting), triangle (exponential), square (step)
* Each frame represents a constant-age cut through all models

**Interactive 3D Evolutionary Tracks:**

* **Full Tracks**: Continuous paths through color–magnitude–age space
* **Age Window**: Slider shows evolutionary progress up to selected age
* **Viewing Controls**: Rotate and zoom to inspect 3D stellar trajectories

**Generated Files:**

```
plots/
├── isochrone_hr_age_[X.X]Myr.png      # 2D evolution plot
├── isochrone_3d_hr_age_[X.X]Myr.png   # 3D evolutionary snapshots
└── isochrone_hr_evolution.gif         # Animation of population evolution
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
