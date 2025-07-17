# MESA Custom Colors Lab: Synthetic Photometry in Stellar Evolution

## Overview

Welcome to the MESA Custom Colors lab! This hands-on tutorial will teach you how to integrate synthetic photometry calculations into your MESA stellar evolution models. By the end of this lab, you'll understand how to:

- Configure custom colors for different photometric systems
- Monitor photometric evolution in real-time using pgstar
- Analyze color-magnitude diagrams (CMDs) and spectral energy distributions (SEDs)
- Run batch stellar evolution models with photometry
- Perform advanced photometric analysis on stellar evolution tracks

The custom colors module allows MESA to compute synthetic magnitudes and colors throughout stellar evolution by interpolating stellar atmosphere models and convolving with filter transmission curves. This provides crucial observational diagnostics for comparing models with real stellar populations.

---

## Part 0: Installing Custom Colors

-- We are not going to be using the official release of MESA for this lab, we will be downloading an unofficial pre-release from Zenodo, changing our MESA path to is and installing it. 
-- This gives up the **custom colors** module which we can use to construct synthetic photometry with our MESA simulations. 

### Zenodo

### Extracting Download

### Changing MESA Path

### Installing

---

## Part 1: Understanding Custom Colors Configuration

### What Is Custom Colors?



The MESA custom colors module computes **synthetic photometry** during stellar evolution by:

1. **Interpolating stellar atmosphere models** (e.g., Kurucz 2003) to match your star's current Teff, log g, and metallicity
2. **Generating spectral energy distributions (SEDs)** for each evolutionary timestep
3. **Convolving with filter transmission curves** (e.g., GAIA, UBVRI, 2MASS)
4. **Computing magnitudes and colors** using standard photometric calibrations


### Key Configuration Parameters

Let's examine the custom colors configuration in your `inlist_project` file:

```fortran
&colors
   use_colors = .true.
   instrument = 'data/filters/GAIA/GAIA'
   vega_sed = 'data/stellar_models/vega_flam.csv'  
   stellar_atm = 'data/stellar_models/Kurucz2003all/'
   distance = 3.0857d17  ! 10 parsecs for absolute magnitudes
   make_csv = .false.
/
```

**Parameter Breakdown:**


...And what do each of these do?

- `use_colors = .true.`: Enables synthetic photometry calculations
- `instrument`: Specifies the filter system (GAIA, UBVRI, 2MASS, etc.)
- `stellar_atm`: Path to stellar atmosphere model grid (Kurucz, PHOENIX, etc.)
- `distance`: Distance in cm (10 pc = 3.0857d17 cm gives absolute magnitudes)
- `make_csv`: Whether to output detailed SED files (disable for performance)



### Physical Interpretation

The custom colors module bridges **stellar physics** and **observational astronomy**:

- **Teff, log g, [M/H]** from your MESA model are use to query a table of Stellar atmosphere models
- **Interpolate** between the closest SEDs to your input params to construct a synthetic SED
- **Convolve synthetic SED** with astronomical filters to obtain synthetic photometry (i.e. -- G, Gbp, Grp, etc.)
- **Bolometric correction** perform the above convolution task on a Vega SED to obtain the Vega corrected magnitudes. 
- **Profit** from the cool science you can now do!


---


## Part 2: Single Model with Real-Time Photometry

### Step 2.1: Configure Your Model

First, examine the provided `inlist_project` file. Notice it extends the Lab1 configuration with additional custom colors:

```bash
cat inlist_project
```

Ensure colors is turned on and 'make_csv' is enabled (As previously described, 'make_csv' will construct a csv for SED measured through each filter. This is good for live plotting.)

Now we need to navigate to the history file and enable the phase_of_evolution identifier ~ line 942. (Failing to do this wont crash the code but it will make your plots look cooler later on...)

```bash
!phase_of_evolution ! Integer mapping to the type of evolution see star_data/public/star_data_def.inc for definitions
```



### Step 2.2: Run the Model with Live Photometry

Start your evolution with pgstar enabled to watch the photometric evolution in real-time:

```bash
./rn
```

**What to Watch For:**

1. **Terminal Output**: Look for custom colors initialization messages:
   ```
   Loading stellar atmosphere models from data/stellar_models/Kurucz2003all/
   Using GAIA photometric system: Gbp, G, Grp
   Computing synthetic photometry at each timestep...
   ```

2. **Pgstar Windows**: 
   - **Lab 1 Window**: You should see the pgplot from the first labs and...
   - **Light Curve Window**: You should also see a Gaia G band lightcurve. 
   
---


## Part 3: Interactive Analysis with Python Helpers

Now let's use the powerful Python visualization tools to explore your photometric results.

### Step 3.1: Real-Time CMD Monitoring

First, let's look at your stellar evolution in color-magnitude space:

```bash
cd python_analysis
python plot_cmd.py
```

This script creates:
- **2D CMD**: Classical color-magnitude diagram (Gbp-Grp vs G)
- **3D CMD**: Time-evolved CMD showing evolutionary tracks
- **Interactive features**: Zoom, rotate, and explore different evolutionary phases

**Physical Interpretation:**
- **Horizontal movement**: Temperature changes (color evolution)
- **Vertical movement**: Luminosity changes (magnitude evolution)  
- **Evolutionary speed**: Fast phases show closely spaced points


**Why this matters:**

- The HR diagram shows the "true" stellar evolution path in fundamental physics space
- The CMD shows what you'd actually observe if you pointed a telescope at this star
- This difference is why astronomers need stellar evolution models to interpret observational data!




### Step 3.2: Spectral Energy Distribution Analysis

Explore the detailed SEDs underlying your photometry:

```bash
python SED_check.py
```

This interactive tool shows:
- **SED evolution**: How your star's spectrum changes with time
- **Filter integration**: Visual representation of magnitude calculations
- **Atmosphere model quality**: Interpolation accuracy diagnostics

**Key Features:**
- Slide through evolutionary timesteps
- Compare observed vs synthetic photometry
- Understand wavelength dependence of stellar evolution

### Step 3.3: Live Monitoring During Evolution

For your next run, try the real-time monitoring:

```bash
# In one terminal
./rn

# In another terminal  
cd python_analysis
python HISTORY_check.py
```

This provides live updates of:
- Photometric evolution plots
- Color-color diagrams
- Magnitude vs time relationships

---











## Part 4: Batch Models and Parameter Studies

### Step 4.1: Understanding the Parameter Grid

Examine the batch model setup:

```bash
cd batch_runs
ls batch_inlists/ | head -10
```

The provided grid explores:
- **Stellar masses**: M = 2, 5, 15, 30 M☉
- **Metallicities**: Z = 0.0014, 0.0140 (roughly Z☉/10 and Z☉)
- **Overshooting**: Various fov and f values
- **Control models**: Some with "noovs" (no overshooting)

### Step 4.2: Running Batch Photometry

Execute the batch run pipeline:

```bash
# Check dependencies and setup
python 0_dependency_check.py

# Generate batch inlists with custom colors
python 1_make_batch.py

# Verify inlist configurations
python 2_verify_inlists.py

# Run the full grid (this takes time!)
python 3_run_batch.py

# Verify successful completion
python 4_verify_outlists.py

# Collect photometric results
python 5_construct_output.py
```

**Pro Tip**: Start with a smaller subset for testing:
```bash
# Edit 3_run_batch.py to run only a few models first
# Then scale up to the full grid
```

### Step 4.3: Batch Photometric Analysis

Once the batch runs complete, analyze the results:

```bash
cd ../python_analysis
python plot_cmd.py  # Now includes batch analysis
```

This creates:
- **Mass sequence CMDs**: Compare evolutionary tracks for different masses
- **Metallicity effects**: See how Z affects photometric evolution
- **Overshooting impact**: Quantify effects on main sequence and beyond

---





## Part 5: Advanced Analysis and Bonus Tasks

### Step 5.1: Color-Color Diagrams

Explore multi-dimensional color relationships:

```bash
python colorcolor_plot.py
```

Creates sophisticated diagnostic plots:
- **Multiple color combinations**: (Gbp-G) vs (G-Grp), etc.
- **Evolutionary phase mapping**: Color evolution through different phases
- **Theoretical isochrone comparison**: Compare to stellar population models

### Step 5.2: Physics-Photometry Correlations

Connect stellar physics to observable properties:

```bash
python colors_physics.py
```

Analyzes relationships between:
- **Core hydrogen abundance** vs photometric colors
- **Surface gravity** vs magnitude evolution
- **Effective temperature** vs multi-band photometry
- **Mass-radius relationships** via photometric diagnostics

### Step 5.3: Light Curve Analysis

For variable stars and evolutionary transitions:

```bash
python lc_plot.py
```

Generates:
- **Multi-band light curves**: Simultaneous evolution in all filters
- **Color variability**: How colors change during rapid phases
- **Pulsation analysis**: For models that show instabilities

### Step 5.4: Custom Analysis (Your Turn!)

Use the analysis templates to explore:

1. **Metallicity sequences**: How does [M/H] affect observable properties?
2. **Mass-luminosity relationships**: Compare synthetic vs observational relations
3. **Stellar population synthesis**: Combine models to simulate clusters
4. **Observational planning**: Which filters best distinguish evolutionary phases?







---

## Interpretation Guide

### Physical Understanding

**Main Sequence Evolution:**
- Colors slowly evolve as core hydrogen depletes
- Magnitude changes primarily reflect mass loss (if any)
- Different masses show distinct photometric signatures

**Post-Main Sequence:**
- **Subgiant Branch**: Rapid color evolution, moderate magnitude changes  
- **Red Giant Branch**: Dramatic reddening, significant brightening
- **Horizontal Branch**: Blue evolution, complex magnitude behavior

**Metallicity Effects:**
- Lower metallicity → bluer colors (less line blanketing)
- Different atmosphere structure → modified magnitude relationships
- Evolutionary timescale differences reflected in photometric tracks

### Observational Connections

**Real Stellar Populations:**
- Your synthetic CMDs can be compared directly to observed clusters
- Color distributions constrain stellar formation histories
- Magnitude functions probe stellar mass distributions

**Survey Astronomy:**
- GAIA DR3 provides precisely the photometry you're computing
- Large sky surveys (SDSS, 2MASS, etc.) use these filter systems
- Your models predict what space missions will observe

### Computational Impacts and pitfalls

**Performance Considerations:**
- Custom colors adds <10% computational overhead
- Atmosphere model interpolation is the main cost
- Filter convolution is fast compared to evolution calculation

**Atmosphere model grid coverage and resolution**
- Stellar atmosphere models have no universal agreed upon data format 
- Stellar atmosphere models do not guarantee an even and fully sampled parameter space
- Your MESA simulation **CAN** produce inputs outside of the stellar atmosphere range without warning


---

## Troubleshooting

### Common Issues

**No photometric output:**
- Check `use_colors = .true.` in namelist
- Check you correctly changed your MESA path `echo $MESA_DIR`

**Python plotting errors:**
- Install required packages: `mesa_reader`, `matplotlib`, `numpy`
- Check Python path includes analysis scripts
- Verify LOGS directory structure


---

## Learning Objectives Summary

After completing this lab, you should understand:

-- **Conceptual**: How synthetic photometry connects stellar physics to observations  
-- **Technical**: Custom colors configuration and workflow integration  
-- **Practical**: Real-time monitoring and analysis of photometric evolution  
-- **Scientific**: Interpretation of color-magnitude diagrams and evolutionary tracks  


### Next Steps

Consider extending this work by:
- Comparing to real cluster CMDs from GAIA or HST
- Implementing additional filter systems (JWST, Roman, etc.)
- Connecting to stellar population synthesis codes

---

## Data and Code References

**Stellar Atmosphere Models:** Kurucz 2003 (http://svo2.cab.inta-csic.es/theory/newov2/)  
**Filter Systems:** SVO Filter Profile Service (http://svo2.cab.inta-csic.es/theory/fps/)  
**MESA Documentation:** https://docs.mesastar.org/  
**Custom Colors Module:** MESA test_suite/custom_colors/  

**Questions?** Consult the MESA forum (https://lists.mesastar.org/) or Niall Miller (nmille39@uwyo.edu) or ask the summer school instructors.
