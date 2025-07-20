# MESA Custom Colors Lab: Synthetic Photometry in Stellar Evolution
## Complete Summer School Guide

---
---

{{< cards >}}
  {{< card link="/downloads/customcol_lab.zip" title="📥 Download Lab Files" subtitle="Download all MESA simulation files, inlists, and Python scripts needed for this lab." >}}
{{< /cards >}}


---
## Overview and Learning Objectives

Welcome to the MESA Custom Colors lab! 
This tutorial teaches you to integrate synthetic photometry calculations into stellar evolution models, bridging theoretical stellar physics with observational astronomy.

### Learning Outcomes
By completing this lab, you will be able to:

   - Configure and run MESA with synthetic photometry calculations
   - Use Python tools for real-time monitoring and post-processing
   - Explain how stellar atmosphere models connect to observable photometry
   - Compare theoretical predictions with observational data
   - Generate synthetic stellar populations for comparison with surveys

### Lab Structure

| Part | Topic |
|------|-------|
| 0 | Installation & Setup |
| 1 | Configuration & Physics |
| 2 | Single Model Analysis |
| 3 | Interactive Visualization |
| 4 | Batch Model Studies |
| 5 | Advanced Analysis |

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

1. **Visit Zenodo**: Navigate to https://zenodo.org/records/16092864
2. **Download**: Click on `mesa-2025-summerschool-prerelease.tar.gz`

#### Extract the Archive

NOTE -- you cant just copy and paste these commands as you need to specify *your* filepath. 

```bash
# Navigate to download location (if it is in an awkward place you could move it to 'home' or put it in a directory along with your other MESA install.)
cd /path/to/your/mesa/installations/

# Extract the archive (this may take a few seconds)
tar -xzf mesa-2025-summerschool-prerelease.tar.gz

# Verify extraction
ls -la mesa-2025-summerschool-prerelease/
# Expected: Should see MESA directory structure with colors/ subdirectory

```

### Step 0.2: Environment Configuration

#### Update MESA_DIR

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

#### Verify Environment Setup

```bash
# Essential checks
echo "MESA_DIR: $MESA_DIR"
echo "MESA SDK: $MESASDK_ROOT"  # Should be set from previous MESA installations, this DOES NOT need to change. 

# Verify colors module files
ls -a $MESA_DIR/colors/
# Expected output: Makefile, src/, data/, test_suite/, README
```

### Step 0.3: Install MESA with Custom Colors

#### Prerequisites Check

```bash
# Verify system requirements
echo "System: $(uname -s)"
echo "Architecture: $(uname -m)"
echo "Available memory: $(free -h | grep Mem | awk '{print $2}')"  # Linux
echo "Available disk space: $(df -h . | tail -1 | awk '{print $4}')"

# Verify MESA SDK is loaded
echo $MESASDK_ROOT
# Should point to your MESA SDK installation
```

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

#If this is not here try to re install with 
cd $MESA_DIR
./clean; ./install
```


#### Verify Successful Installation

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

### Complete Installation Checklist

Verify each component before proceeding to the lab:

#### System Environment
- [ ] `$MESA_DIR` points to pre-release version
- [ ] MESA SDK properly loaded (`$MESASDK_ROOT` set)
- [ ] Fortran compiler available and compatible

#### MESA Installation
- [ ] `./install` completed successfully (exit code 0)
- [ ] Core MESA libraries present in `$MESA_DIR/lib/`
- [ ] Basic test case compiles and runs

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

# If this is not there, Check for permission issues or disk space and re-exrtact the zip file
```

For additional support or contact the lab instructor or contact Niall Miller (via mattermost or whatever is easy)

---

## Part 1: Understanding Custom Colors Physics

### The Synthetic Photometry Pipeline

The custom colors module implements a sophisticated pipeline that converts stellar physics into observable quantities:

```
Stellar Parameters    →    Atmosphere Model    →    SED    →    Photometry
(Teff, log g, [M/H])       Interpolation              Convolution    (Magnitudes)
```

### Step 1.1: Physical Foundation

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

### Step 1.2: Configuration Parameters

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

#### Parameter Descriptions

| Parameter | Purpose | Typical Values |
|-----------|---------|----------------|
| `use_colors` | Enable photometry calculations | `.true.` |
| `instrument` | Filter system directory | `'GAIA'`|
| `stellar_atm` | Atmosphere model grid path | `'Kurucz2003all/'` |
| `distance` | Distance for flux scaling | `3.0857d17` cm (10 pc) |
| `make_csv` | Output detailed SEDs as csv files | `.false.` (performance) |

---

## Part 2: Single Model with Real-Time Photometry

### Step 2.1: Model Configuration

#### Enable Evolutionary Phase Tracking

Edit your `inlist_project` to include photometric evolution diagnostics:

```fortran
! In &star_job namelist
history_columns_file = 'history_columns.list'

! In &controls namelist
photo_interval = 50        ! Frequency of detailed output
```

#### Configure History Output

Edit `history_columns.list` around line 942:

```fortran
! Add this line for phase identification
phase_of_evolution     ! Integer mapping to evolution phases

! Ensure these are included
model_number
star_age
log_dt
log_Teff
log_L
log_g
```

### Step 2.2: Understanding Pgstar Integration

The custom colors module integrates with pgstar for real-time visualization:

```fortran
! In &pgstar namelist
Kipp_win_flag = .true.
Kipp_win_width = 12
Kipp_win_aspect_ratio = 0.75

! Enable custom colors plots
History_Panels1_win_flag = .true.
History_Panels1_title = 'Photometric Evolution'
```

### Step 2.3: Run the Model

```bash
./rn
```

#### Expected Terminal Output

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

#### Pgstar Windows to Monitor

1. **HR Diagram**: Track evolution in fundamental parameter space
2. **Photometric Panel**: Real-time color-magnitude diagram
3. **Kippenhahn Diagram**: Internal structure evolution

### Step 2.4: Physical Interpretation

#### Main Sequence Evolution

During core hydrogen burning, observe:
- **Slow color evolution**: Colors change gradually as $T_\text{eff}$ decreases
- **Luminosity increase**: Main sequence brightening due to core evolution
- **Filter dependence**: Blue filters show larger magnitude changes

#### Post-Main Sequence Changes

Watch for rapid transitions:
- **Subgiant branch**: Accelerated reddening
- **Red giant branch**: Dramatic magnitude changes
- **Helium flash**: Potential photometric signatures

---

## Part 3: Interactive Analysis with Python Tools

### Step 3.1: Real-Time CMD Monitoring

Launch the interactive color-magnitude diagram viewer:

```bash
cd python_analysis
python plot_cmd.py
```

#### Features and Controls

The script automatically detects your photometric system and creates:

- **2D CMD**: Classical color-magnitude diagram with evolutionary track
- **3D CMD**: Time-evolved diagram showing age progression
- **Phase Coloring**: MESA's built-in evolutionary phase identification

#### Scientific Analysis Questions

1. **Color Evolution**: How does $G_{BP} - G_{RP}$ change during main sequence evolution?
2. **Luminosity Function**: What determines the magnitude range?
3. **Evolutionary Speed**: Where does your star spend most time in CMD space?

### Step 3.2: Spectral Energy Distribution Analysis

Explore the underlying stellar spectra:

```bash
python SED_check.py
```

#### Interactive Features

- **Wavelength Range**: Zoom into specific spectral regions
- **Filter Overlay**: Visualize how filters sample the spectrum
- **Time Evolution**: See how the SED shape changes

#### Physical Interpretation

- **Blackbody Comparison**: How does the stellar SED differ from a perfect blackbody?
- **Line Effects**: Where do absorption lines affect photometry?
- **Filter Sensitivity**: Which filters are most sensitive to $T_\text{eff}$ changes?

### Step 3.3: Live Evolution Monitoring

For ongoing simulations, monitor evolution in real-time:

```bash
# Terminal 1: Run MESA
./rn

# Terminal 2: Live monitoring
cd python_analysis
python HISTORY_check.py
```

#### Live Analysis Capabilities

- **Automatic Updates**: Plots refresh as new data becomes available
- **Multi-Panel Display**: Simultaneous HR diagram and CMD views
- **Phase Identification**: Color-coded evolutionary phases
- **Export Functionality**: Save key evolutionary moments

---

## Part 4: Batch Models and Parameter Studies

### Step 4.1: Understanding the Parameter Grid

Systematic studies require exploring parameter space efficiently. Examine the provided batch setup:

```bash
cd batch_runs
ls batch_inlists/ | head -10

# Expected output:
inlist_M15_Z0140_exponential_fov010
inlist_M15_Z0140_exponential_fov020
inlist_M15_Z0140_step_fov010
inlist_M15_Z0140_noovs
inlist_M2_Z0014_exponential_fov010
...
```

#### Parameter Grid Design

| Parameter | Values | Physical Significance |
|-----------|--------|----------------------|
| **Mass** | 2, 5, 15, 30 M☉ | Main sequence lifetime, final fate |
| **Metallicity** | Z = 0.0014, 0.0140 | Opacity effects, stellar winds |
| **Overshooting** | None, exponential, step | Convective mixing efficiency |
| **$f_\text{ov}$** | 0.01, 0.02, 0.03 | Overshooting parameter |

### Step 4.2: Running Batch Photometry

Execute the automated batch pipeline:

```bash
# Verify dependencies
python 0_dependency_check.py

# Generate inlists with colors configuration
python 1_make_batch.py

# Verify all configurations
python 2_verify_inlists.py

# Execute the full grid (computationally intensive!)
python 3_run_batch.py

# Validate completion
python 4_verify_outlists.py

# Collect photometric data
python 5_construct_output.py
```

#### Performance Considerations

| Grid Size | Estimated Time | Recommendations |
|-----------|----------------|-----------------|
| 4 models | 1-4 hours | Initial testing |
| 16 models | 4-12 hours | Partial parameter study |
| 64 models | 1-3 days | Full grid (varies by system) |

### Step 4.3: Batch Analysis and Interpretation

#### Mass Sequence Analysis

```bash
python plot_cmd.py  # Now includes batch mode
```

Creates comparative visualizations:
- **Mass-dependent tracks**: Different evolutionary paths
- **Metallicity effects**: Systematic shifts in CMD position
- **Overshooting impact**: Main sequence width variations

#### Scientific Questions for Investigation

1. **Mass-Luminosity Relation**: How does photometry reveal the M-L relationship?
2. **Metallicity Degeneracy**: Can colors break age-metallicity degeneracy?
3. **Convective Efficiency**: What photometric signatures indicate overshooting?

---

## Part 5: Advanced Analysis and Research Applications

### Step 5.1: Color-Color Diagrams

Multi-dimensional color analysis reveals subtle evolutionary effects:

```bash
python plot_colorcolor.py
```

#### Advanced Diagnostics

- **Temperature Sensitivity**: $(G_{BP} - G)$ vs $(G - G_{RP})$
- **Metallicity Indicators**: Color combinations sensitive to [M/H]
- **Evolutionary Phase Mapping**: Distinct regions for different phases

### Step 5.2: Isochrone Construction

Generate theoretical stellar populations:

```bash
python plot_isochrone.py
```

#### Interactive Features

- **Age Slider**: Explore population evolution
- **3D Visualization**: Age-color-magnitude relationships
- **Animation Export**: Create evolutionary movies

#### Research Applications

- **Cluster Dating**: Compare with observed CMDs
- **Star Formation History**: Constrain stellar populations
- **Distance Determination**: Isochrone fitting techniques

### Step 5.3: Lightcurve Analysis

Time-domain photometry for variable stars:

```bash
python plot_lc.py
```

#### Applications

- **Pulsation Studies**: Intrinsic variability
- **Eclipse Modeling**: Binary star systems
- **Evolutionary Timescales**: Rapid transition phases

### Step 5.4: Physics-Photometry Correlations

Connect internal physics to observable properties:

```bash
python colors_physics.py
```

#### Correlation Analysis

- **Core Hydrogen vs Color**: Evolutionary phase indicators
- **Convective Core Mass**: Relationship to photometric properties
- **Surface Gravity**: Connection to magnitude evolution

---

## Troubleshooting and FAQs

### Common Installation Issues

**Problem**: MESA_DIR not updated correctly
```bash
# Solution: Verify environment
echo $MESA_DIR
source ~/.bashrc  # Reload shell configuration
```

**Problem**: Missing stellar atmosphere data
```bash
# Solution: Manual data extraction
cd $MESA_DIR/colors/data
tar -xf colors_data.txz
```

### Runtime Errors

**Problem**: "Interpolation outside grid bounds"
- **Cause**: Stellar parameters exceed atmosphere model coverage
- **Solution**: Check $T_\text{eff}$, $\log g$, [M/H] ranges in terminal output

**Problem**: Python plotting failures
```bash
# Install required packages
pip install mesa_reader matplotlib numpy scipy pandas
```

### Performance Optimization

| Issue | Solution | Impact |
|-------|----------|--------|
| Slow SED calculation | Set `make_csv = .false.` | 50% speedup |
| Memory usage | Reduce `photo_interval` | Lower memory |
| Grid size | Start with subset | Faster testing |

### Advanced Configuration

#### Custom Filter Systems

Add new photometric systems:
```bash
# Create filter directory
mkdir $MESA_DIR/colors/data/filters/CUSTOM/

# Add transmission curves (wavelength, transmission)
# Format: ASCII files with .dat extension
```

#### Atmosphere Model Alternatives

Replace Kurucz models with PHOENIX or MARCS:
- Update `stellar_atm` parameter
- Ensure consistent metallicity scales
- Validate interpolation accuracy

---

## Appendix: Quick Reference

### Essential Commands

```bash
# Installation
export MESA_DIR=/path/to/prerelease
./install

# Single model
./rn

# Batch processing
python 1_make_batch.py
python 3_run_batch.py

# Analysis
python plot_cmd.py
python plot_colorcolor.py
python plot_isochrone.py
```

### Key Configuration Parameters

```fortran
&colors
   use_colors = .true.
   instrument = 'data/filters/GAIA/GAIA'
   stellar_atm = 'data/stellar_models/Kurucz2003all/'
   distance = 3.0857d17
   make_csv = .false.
/
```

### Python Dependencies

```bash
pip install mesa_reader matplotlib numpy scipy pandas
```

### Help

- **MESA Forum**: https://lists.mesastar.org/
- **Lab Developer**: Niall Miller (nmille39@uwyo.edu)
- **Summer School Instructors** 
