#!/usr/bin/env python3
"""
cmd_isochrones.py - Interactive Isochrone CMD Generator for MESA Batch Runs
Shows stellar populations as points at specific ages with time slider
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import mesa_reader as mr
import glob
from matplotlib.widgets import Slider
from matplotlib.colors import Normalize
import matplotlib.cm as cm

def read_header_columns(history_file):
    """Read column headers from history file to find available filters."""
    header_line = None
    with open(history_file, "r") as fp:
        for line in fp:
            if "model_number" in line:
                header_line = line.strip()
                break
    
    if header_line is None:
        print("Warning: Could not find header line with 'model_number'")
        return [], []
    
    all_cols = header_line.split()
    
    # Find filter columns after Flux_bol
    try:
        flux_index = all_cols.index("Flux_bol")
        filter_columns = all_cols[flux_index + 1:]
    except ValueError:
        print("Warning: Could not find 'Flux_bol' column in header")
        filter_columns = []
    
    return all_cols, filter_columns

def setup_cmd_params(md, filter_columns):
    """Set up CMD parameters based on available filters with priority system."""
    
    # Priority 1: GAIA colors (Gbp - Grp vs G)
    if "Gbp" in filter_columns and "Grp" in filter_columns and "G" in filter_columns:
        color_index = md.Gbp - md.Grp
        magnitude = md.G
        color_label = "Gbp - Grp"
        mag_label = "G"
        system = "GAIA"
        print("Using GAIA CMD: Gbp-Grp vs G")
        
    # Priority 2: Johnson-Cousins (B-V vs V)
    elif "B" in filter_columns and "V" in filter_columns:
        color_index = md.B - md.V
        magnitude = md.V
        color_label = "B - V"
        mag_label = "V"
        system = "Johnson"
        print("Using Johnson CMD: B-V vs V")
        
    # Priority 3: 2MASS (J-K vs K)
    elif "J" in filter_columns and "K" in filter_columns:
        color_index = md.J - md.K
        magnitude = md.K
        color_label = "J - K"
        mag_label = "K"
        system = "2MASS"
        print("Using 2MASS CMD: J-K vs K")
        
    # Priority 4: SDSS (g-r vs r)
    elif "g" in filter_columns and "r" in filter_columns:
        color_index = getattr(md, 'g') - getattr(md, 'r')
        magnitude = getattr(md, 'r')
        color_label = "g - r"
        mag_label = "r"
        system = "SDSS"
        print("Using SDSS CMD: g-r vs r")
        
    # Fallback: Use first two available filters
    elif len(filter_columns) >= 2:
        f1, f2 = filter_columns[0], filter_columns[1]
        try:
            col1 = getattr(md, f1)
            col2 = getattr(md, f2)
        except AttributeError:
            col1 = md.data(f1)
            col2 = md.data(f2)
            
        color_index = col1 - col2
        magnitude = col1
        color_label = f"{f1} - {f2}"
        mag_label = f1
        system = "Custom"
        print(f"Using custom CMD: {color_label} vs {mag_label}")
        
    else:
        # No filters available - fall back to traditional HR diagram
        print("Warning: No photometric filters found, falling back to HR diagram")
        color_index = md.log_Teff
        magnitude = md.log_L
        color_label = "log Teff"
        mag_label = "log L/L☉"
        system = "HR"
    
    return color_index, magnitude, color_label, mag_label, system

def interpolate_stellar_data(age_array, data_arrays, target_age):
    """Interpolate stellar data to a specific age."""
    if target_age <= age_array[0]:
        return [data[0] for data in data_arrays]
    elif target_age >= age_array[-1]:
        return [data[-1] for data in data_arrays]
    else:
        # Find interpolation indices
        idx = np.searchsorted(age_array, target_age)
        if idx == 0:
            return [data[0] for data in data_arrays]
        
        # Linear interpolation
        t = (target_age - age_array[idx-1]) / (age_array[idx] - age_array[idx-1])
        interpolated = []
        for data in data_arrays:
            value = data[idx-1] + t * (data[idx] - data[idx-1])
            interpolated.append(value)
        return interpolated

def load_batch_data(runs_dir="../runs"):
    """Load all batch run data and organize by stellar parameters."""
    
    if not os.path.isdir(runs_dir):
        print(f"Error: Could not find {runs_dir} directory")
        return None, None
        
    # Find all run directories
    run_dirs = [d for d in os.listdir(runs_dir) 
                if os.path.isdir(os.path.join(runs_dir, d)) and d.startswith("inlist_")]
    
    if not run_dirs:
        print("No batch run directories found")
        return None, None
        
    # Parse run parameters and collect data
    all_data = []
    
    for run_dir in run_dirs:
        history_path = os.path.join(runs_dir, run_dir, "LOGS", "history.data")
        
        if not os.path.exists(history_path):
            print(f"Warning: No history file in {run_dir}")
            continue
            
        try:
            # Parse parameters from directory name
            parts = run_dir.replace('inlist_M', '').split('_')
            mass = float(parts[0])
            metallicity = float(parts[1][1:])  # Remove 'Z'
            
            if 'noovs' in run_dir:
                scheme = 'none'
                fov = 0.0
            else:
                scheme = parts[2]
                fov = float(parts[3][3:])  # Remove 'fov'
                
            # Load data
            data = mr.MesaData(history_path)
            all_cols, filter_columns = read_header_columns(history_path)
            color_index, magnitude, color_label, mag_label, system = setup_cmd_params(data, filter_columns)
            
            if color_index is None or not hasattr(data, 'star_age'):
                continue
            
            # Store data
            run_info = {
                'data': data,
                'mass': mass,
                'metallicity': metallicity,
                'scheme': scheme,
                'fov': fov,
                'color_index': color_index,
                'magnitude': magnitude,
                'color_label': color_label,
                'mag_label': mag_label,
                'system': system,
                'run_dir': run_dir,
                'age_myr': data.star_age / 1e6  # Convert to Myr
            }
            all_data.append(run_info)
            
        except Exception as e:
            print(f"Error processing {run_dir}: {e}")
            continue
    
    if not all_data:
        print("No valid data found in batch runs")
        return None, None
        
    # Determine the primary photometric system
    systems = [d['system'] for d in all_data]
    primary_system = max(set(systems), key=systems.count)
    primary_data = [d for d in all_data if d['system'] == primary_system]
    
    print(f"Loaded {len(primary_data)} models with {primary_system} photometry")
    
    # Determine age range for slider
    min_age = min(d['age_myr'][0] for d in primary_data)
    max_age = max(d['age_myr'][-1] for d in primary_data)
    
    return primary_data, (min_age, max_age)

def get_evolutionary_stages(data):
    """Identify key evolutionary stages based on physics parameters."""
    stages = {}
    
    if hasattr(data, 'center_h1'):
        # ZAMS: Initial hydrogen abundance
        zams_idx = 0
        stages['ZAMS'] = zams_idx
        
        # TAMS: Hydrogen exhaustion in core
        h1_threshold = 0.01
        tams_candidates = np.where(data.center_h1 < h1_threshold)[0]
        if len(tams_candidates) > 0:
            stages['TAMS'] = tams_candidates[0]
    
    if hasattr(data, 'log_L'):
        # RGB Tip: Maximum luminosity (for low-mass stars)
        max_lum_idx = np.argmax(data.log_L)
        if max_lum_idx > len(data.log_L) * 0.5:  # Only if it's in latter half of evolution
            stages['RGB Tip'] = max_lum_idx
    
    return stages

def create_isochrone_plot(runs_dir="../runs", use_hr_coords=True):
    """Create interactive isochrone CMD plot with time slider."""
    
    # Load data
    stellar_data, age_range = load_batch_data(runs_dir)
    if stellar_data is None:
        return False
    
    min_age, max_age = age_range
    
    # Option to use HR diagram coordinates for standardized scale
    if use_hr_coords:
        print("Using HR diagram coordinates (log Teff vs log L) for standardized scale")
        for run_info in stellar_data:
            if hasattr(run_info['data'], 'log_Teff') and hasattr(run_info['data'], 'log_L'):
                run_info['color_index'] = run_info['data'].log_Teff
                run_info['magnitude'] = run_info['data'].log_L
                run_info['color_label'] = r"$\log(T_{\mathrm{eff}}/\mathrm{K})$"
                run_info['mag_label'] = r"$\log(L/L_{\odot})$"
                run_info['system'] = "HR"
    
    # Set up color mapping by mass (same as HR diagram example)
    masses = sorted(set(d["mass"] for d in stellar_data))
    mass_colors = plt.cm.brg(np.linspace(0, 1, len(masses)))
    mass_color_map = {mass: mass_colors[i] for i, mass in enumerate(masses)}
    
    # Set up markers by scheme
    scheme_markers = {'none': 'o', 'exponential': '^', 'step': 's'}
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(14, 10))
    plt.subplots_adjust(bottom=0.15)
    
    # Create slider
    ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
    slider = Slider(ax_slider, 'Age (Myr)', min_age, max_age, 
                   valinit=min_age, valfmt='%.1f')
    
    # Initialize plot elements
    scatter_plots = []
    
    def update_plot(age):
        """Update plot for given age."""
        ax.clear()
        
        # Get system info from first model
        system = stellar_data[0]['system']
        color_label = stellar_data[0]['color_label']
        mag_label = stellar_data[0]['mag_label']
        
        # Plot each stellar model at the current age
        for run_info in stellar_data:
            # Interpolate data to current age
            if age < run_info['age_myr'][0] or age > run_info['age_myr'][-1]:
                continue  # Skip if age is outside model range
                
            color_interp, mag_interp = interpolate_stellar_data(
                run_info['age_myr'], 
                [run_info['color_index'], run_info['magnitude']], 
                age
            )
            
            # Get styling
            base_color = mass_color_map[run_info["mass"]]
            marker = scheme_markers.get(run_info["scheme"], 'o')
            
            # Alpha based on fov (same as HR diagram)
            fov_alpha = 0.3 + 0.7 * run_info["fov"] if run_info["scheme"] != "none" else 1.0
            
            # Plot point
            ax.scatter(color_interp, mag_interp, 
                      color=base_color, marker=marker, 
                      s=80, alpha=fov_alpha, edgecolors='black', linewidth=0.5)
        
        # Set up plot appearance
        ax.set_xlabel(color_label, fontsize=14)
        ax.set_ylabel(mag_label, fontsize=14)
        ax.invert_yaxis()
        
        if system == "HR":
            ax.invert_xaxis()
            # Set standard HR diagram limits for better comparison
            ax.set_xlim(4.6, 3.2)  # log Teff range
            ax.set_ylim(-2, 6)     # log L range
        
        ax.grid(alpha=0.3)
        ax.set_title(f"{system} CMD Isochrone at Age = {age:.1f} Myr", fontsize=16)
        
        # Add evolutionary stage markers for HR diagrams
        if system == "HR" and age > min_age + 0.1:
            # Add stage reference lines
            ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5, label='Solar Luminosity')
            ax.axvline(x=np.log10(5778), color='gray', linestyle=':', alpha=0.5, label='Solar Teff')
        
        # Create legend (same style as HR diagram)
        # Mass legend
        for mass in masses:
            ax.scatter([], [], color=mass_color_map[mass], s=80, 
                      label=f"{mass}M☉", alpha=0.8)
        
        # Scheme legend  
        for scheme, marker in scheme_markers.items():
            ax.scatter([], [], marker=marker, color='gray', s=80,
                      label=f"{scheme} scheme", alpha=0.8)
        
        if len(stellar_data) > 15:
            ax.legend(fontsize=9, loc='upper left', bbox_to_anchor=(1.01, 1.0))
        else:
            ax.legend(fontsize=10, loc='best')
        
        plt.draw()
    
    # Set up slider callback
    def on_slider_change(val):
        update_plot(val)
    
    slider.on_changed(on_slider_change)
    
    # Initial plot
    update_plot(min_age)
    
    # Save static version at different ages
    os.makedirs("plots", exist_ok=True)
    
    # Save snapshots at key evolutionary phases
    key_ages = np.linspace(min_age, max_age, 5)
    for i, age in enumerate(key_ages):
        update_plot(age)
        system = stellar_data[0]['system']
        plt.savefig(f"plots/isochrone_{system.lower()}_age_{age:.1f}Myr.png", 
                   dpi=300, bbox_inches='tight')
    
    print(f"Saved isochrone snapshots to plots/ directory")
    print(f"Interactive plot: Use slider to explore evolution from {min_age:.1f} to {max_age:.1f} Myr")
    
    plt.show()
    return True

def create_3d_isochrone_plot(runs_dir="../runs", use_hr_coords=True):
    """Create interactive 3D isochrone plot with age as z-axis and time slider."""
    
    # Load data
    stellar_data, age_range = load_batch_data(runs_dir)
    if stellar_data is None:
        return False
    
    min_age, max_age = age_range
    
    # Option to use HR diagram coordinates
    if use_hr_coords:
        print("Using HR diagram coordinates for 3D plot")
        for run_info in stellar_data:
            if hasattr(run_info['data'], 'log_Teff') and hasattr(run_info['data'], 'log_L'):
                run_info['color_index'] = run_info['data'].log_Teff
                run_info['magnitude'] = run_info['data'].log_L
                run_info['color_label'] = r"$\log(T_{\mathrm{eff}}/\mathrm{K})$"
                run_info['mag_label'] = r"$\log(L/L_{\odot})$"
                run_info['system'] = "HR"
    
    # Set up color mapping
    masses = sorted(set(d["mass"] for d in stellar_data))
    mass_colors = plt.cm.brg(np.linspace(0, 1, len(masses)))
    mass_color_map = {mass: mass_colors[i] for i, mass in enumerate(masses)}
    scheme_markers = {'none': 'o', 'exponential': '^', 'step': 's'}
    
    # Create 3D figure
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')
    plt.subplots_adjust(bottom=0.15)
    
    # Create slider
    ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
    slider = Slider(ax_slider, 'Age Window (Myr)', min_age, max_age, 
                   valinit=min_age, valfmt='%.1f')
    
    def update_3d_plot(current_age):
        """Update 3D plot showing evolution up to current age."""
        ax.clear()
        
        system = stellar_data[0]['system']
        color_label = stellar_data[0]['color_label']
        mag_label = stellar_data[0]['mag_label']
        
        # Plot evolutionary tracks up to current age
        for run_info in stellar_data:
            # Get all points up to current age
            age_mask = run_info['age_myr'] <= current_age
            if not np.any(age_mask):
                continue
                
            ages_subset = run_info['age_myr'][age_mask]
            colors_subset = run_info['color_index'][age_mask]
            mags_subset = run_info['magnitude'][age_mask]
            
            # Get styling
            base_color = mass_color_map[run_info["mass"]]
            fov_alpha = 0.3 + 0.7 * run_info["fov"] if run_info["scheme"] != "none" else 1.0
            
            # Plot evolutionary track
            ax.plot(colors_subset, mags_subset, ages_subset,
                   color=base_color, linewidth=2, alpha=fov_alpha)
            
            # Mark start point
            ax.scatter(colors_subset[0], mags_subset[0], ages_subset[0],
                      color=base_color, marker='o', s=50, alpha=fov_alpha)
            
            # Mark current position
            if len(colors_subset) > 1:
                ax.scatter(colors_subset[-1], mags_subset[-1], ages_subset[-1],
                          color=base_color, marker='s', s=80, alpha=fov_alpha,
                          edgecolors='black', linewidth=1)
        
        # Set up 3D plot appearance
        ax.set_xlabel(color_label, fontsize=12)
        ax.set_ylabel(mag_label, fontsize=12)
        ax.set_zlabel('Age (Myr)', fontsize=12)
        ax.invert_yaxis()
        
        if system == "HR":
            ax.invert_xaxis()
            # Set standard limits
            ax.set_xlim(4.6, 3.2)
            ax.set_ylim(-2, 6)
        
        ax.set_zlim(min_age, max_age)
        ax.set_title(f"3D {system} Evolution up to Age = {current_age:.1f} Myr", fontsize=14)
        
        # Set viewing angle for better perspective
        ax.view_init(elev=20, azim=-60)
        
        # Create legend
        for mass in masses:
            ax.plot([], [], [], color=mass_color_map[mass], linewidth=3, 
                   label=f"{mass}M☉", alpha=0.8)
        
        for scheme, marker in scheme_markers.items():
            ax.plot([], [], [], color='gray', linewidth=2,
                   linestyle='-' if scheme == 'exponential' else '--' if scheme == 'none' else ':',
                   label=f"{scheme} scheme")
        
        if len(stellar_data) > 15:
            ax.legend(fontsize=8, loc='upper left', bbox_to_anchor=(1.01, 1.0))
        else:
            ax.legend(fontsize=9, loc='best')
        
        plt.draw()
    
    # Set up slider callback
    def on_3d_slider_change(val):
        update_3d_plot(val)
    
    slider.on_changed(on_3d_slider_change)
    
    # Initial plot
    update_3d_plot(min_age + (max_age - min_age) * 0.3)  # Start at 30% through evolution
    
    # Save static versions
    os.makedirs("plots", exist_ok=True)
    key_ages = np.linspace(min_age, max_age, 4)
    for age in key_ages:
        update_3d_plot(age)
        system = stellar_data[0]['system']
        plt.savefig(f"plots/isochrone_3d_{system.lower()}_age_{age:.1f}Myr.png", 
                   dpi=300, bbox_inches='tight')
    
    print(f"Saved 3D isochrone snapshots to plots/ directory")
    print(f"Interactive 3D plot: Use slider to see evolution unfold in 3D space")
    
    plt.show()
    return True

def create_animated_isochrone_gif(runs_dir="../runs", n_frames=50, use_hr_coords=True):
    """Create an animated GIF of the isochrone evolution."""
    try:
        from matplotlib.animation import FuncAnimation, PillowWriter
    except ImportError:
        print("Warning: Animation requires matplotlib with PillowWriter. Skipping GIF creation.")
        return False
    
    # Load data
    stellar_data, age_range = load_batch_data(runs_dir)
    if stellar_data is None:
        return False
    
    min_age, max_age = age_range
    
    # Option to use HR diagram coordinates
    if use_hr_coords:
        for run_info in stellar_data:
            if hasattr(run_info['data'], 'log_Teff') and hasattr(run_info['data'], 'log_L'):
                run_info['color_index'] = run_info['data'].log_Teff
                run_info['magnitude'] = run_info['data'].log_L
                run_info['color_label'] = r"$\log(T_{\mathrm{eff}}/\mathrm{K})$"
                run_info['mag_label'] = r"$\log(L/L_{\odot})$"
                run_info['system'] = "HR"
    
    # Set up color mapping
    masses = sorted(set(d["mass"] for d in stellar_data))
    mass_colors = plt.cm.brg(np.linspace(0, 1, len(masses)))
    mass_color_map = {mass: mass_colors[i] for i, mass in enumerate(masses)}
    scheme_markers = {'none': 'o', 'exponential': '^', 'step': 's'}
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Age points for animation
    ages = np.linspace(min_age, max_age, n_frames)
    
    def animate(frame):
        age = ages[frame]
        ax.clear()
        
        system = stellar_data[0]['system']
        color_label = stellar_data[0]['color_label']
        mag_label = stellar_data[0]['mag_label']
        
        for run_info in stellar_data:
            if age < run_info['age_myr'][0] or age > run_info['age_myr'][-1]:
                continue
                
            color_interp, mag_interp = interpolate_stellar_data(
                run_info['age_myr'], 
                [run_info['color_index'], run_info['magnitude']], 
                age
            )
            
            base_color = mass_color_map[run_info["mass"]]
            marker = scheme_markers.get(run_info["scheme"], 'o')
            fov_alpha = 0.3 + 0.7 * run_info["fov"] if run_info["scheme"] != "none" else 1.0
            
            ax.scatter(color_interp, mag_interp, 
                      color=base_color, marker=marker, 
                      s=80, alpha=fov_alpha, edgecolors='black', linewidth=0.5)
        
        ax.set_xlabel(color_label, fontsize=12)
        ax.set_ylabel(mag_label, fontsize=12)
        ax.invert_yaxis()
        
        if system == "HR":
            ax.invert_xaxis()
            # Set standard HR diagram limits
            ax.set_xlim(4.6, 3.2)
            ax.set_ylim(-2, 6)
        
        ax.grid(alpha=0.3)
        ax.set_title(f"{system} CMD Isochrone Evolution\nAge = {age:.1f} Myr", fontsize=14)
        
        return ax.collections
    
    # Create animation
    anim = FuncAnimation(fig, animate, frames=n_frames, interval=200, blit=False)
    
    # Save as GIF
    os.makedirs("plots", exist_ok=True)
    system = stellar_data[0]['system']
    writer = PillowWriter(fps=5)
    anim.save(f"plots/isochrone_{system.lower()}_evolution.gif", writer=writer)
    print(f"Saved animated isochrone to plots/isochrone_{system.lower()}_evolution.gif")
    
    plt.close()
    return True

def main():
    """Main function to create isochrone plots."""
    
    # Check for batch runs
    batch_run_found = False
    for runs_path in ["../runs", "runs"]:
        if os.path.isdir(runs_path):
            print(f"Found batch runs directory at {runs_path}.")
            print("Creating interactive isochrone CMD plots...")
            
            # Ask user for coordinate system
            coord_choice = input("\nUse HR diagram coordinates (log Teff vs log L) for standard scaling? (y/n): ").lower().strip()
            use_hr = coord_choice == 'y'
            
            if use_hr:
                print("Using standardized HR diagram coordinates with evolutionary reference lines")
            else:
                print("Using photometric colors from MESA output")
            
            # Create 2D interactive isochrone plot
            print("\nCreating 2D interactive isochrone plot...")
            if create_isochrone_plot(runs_path, use_hr_coords=use_hr):
                print("2D interactive isochrone plot created successfully!")
            
            # Ask for 3D plot
            create_3d = input("\nCreate 3D isochrone plot? (y/n): ").lower().strip()
            if create_3d == 'y':
                print("Creating 3D interactive isochrone plot...")
                if create_3d_isochrone_plot(runs_path, use_hr_coords=use_hr):
                    print("3D interactive isochrone plot created successfully!")
            
            # Ask for animated GIF
            create_gif = input("\nCreate animated GIF? (y/n): ").lower().strip()
            if create_gif == 'y':
                create_animated_isochrone_gif(runs_path, use_hr_coords=use_hr)
            
            batch_run_found = True
            break
    
    if not batch_run_found:
        print("Error: Could not find batch runs directory.")
        print("This script only works with batch runs (multiple stellar models).")
        print("Make sure you have a 'runs' or '../runs' directory with MESA batch runs.")

if __name__ == "__main__":
    main()