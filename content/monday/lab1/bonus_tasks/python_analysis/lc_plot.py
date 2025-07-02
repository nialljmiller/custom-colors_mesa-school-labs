#!/usr/bin/env python3
"""
lightcurve_batch.py - Batch Synthetic Photometry Lightcurves for Multiple MESA Models
Compare custom colors evolution across different stellar masses and overshooting parameters
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import mesa_reader as mr
import matplotlib.gridspec as gridspec
import glob

def read_header_columns(history_file):
    """Read column headers from history file to find available filters."""
    header_line = None
    with open(history_file, "r") as fp:
        for line in fp:
            if "model_number" in line:
                header_line = line.strip()
                break
    
    if header_line is None:
        return [], []
    
    all_cols = header_line.split()
    
    try:
        flux_index = all_cols.index("Flux_bol")
        filter_columns = all_cols[flux_index + 1:]
    except ValueError:
        filter_columns = []
    
    return all_cols, filter_columns

def setup_photometric_system(md, filter_columns):
    """Choose the best available photometric system."""
    
    # Priority 1: GAIA
    if all(f in filter_columns for f in ['Gbp', 'G', 'Grp']):
        return {
            'name': 'GAIA',
            'filters': ['Gbp', 'G', 'Grp'],
            'primary_color': 'Gbp-Grp',
            'primary_mag': 'G',
            'colors': ['Gbp-Grp', 'Gbp-G', 'G-Grp']
        }
    
    # Priority 2: Johnson-Cousins
    elif all(f in filter_columns for f in ['B', 'V']):
        available = [f for f in ['U', 'B', 'V', 'R', 'I'] if f in filter_columns]
        colors = []
        if 'B' in available and 'V' in available:
            colors.append('B-V')
        if 'V' in available and 'R' in available:
            colors.append('V-R')
        if 'U' in available and 'B' in available:
            colors.append('U-B')
        
        return {
            'name': 'Johnson',
            'filters': available,
            'primary_color': 'B-V',
            'primary_mag': 'V',
            'colors': colors
        }
    
    # Priority 3: 2MASS
    elif all(f in filter_columns for f in ['J', 'K']):
        available = [f for f in ['J', 'H', 'K'] if f in filter_columns]
        colors = []
        if 'J' in available and 'K' in available:
            colors.append('J-K')
        if 'H' in available and 'K' in available:
            colors.append('H-K')
        
        return {
            'name': '2MASS',
            'filters': available,
            'primary_color': 'J-K',
            'primary_mag': 'K',
            'colors': colors
        }
    
    # Priority 4: SDSS
    elif all(f in filter_columns for f in ['g', 'r']):
        available = [f for f in ['u', 'g', 'r', 'i', 'z'] if f in filter_columns]
        colors = []
        if 'g' in available and 'r' in available:
            colors.append('g-r')
        if 'r' in available and 'i' in available:
            colors.append('r-i')
        
        return {
            'name': 'SDSS',
            'filters': available,
            'primary_color': 'g-r',
            'primary_mag': 'r',
            'colors': colors
        }
    
    return None

def plot_batch_lightcurves(runs_dir="../runs"):
    """Create comparative lightcurve plots for batch MESA runs."""
    
    if not os.path.isdir(runs_dir):
        print(f"Error: Could not find runs directory: {runs_dir}")
        return
    
    # Find all run directories
    run_dirs = [d for d in os.listdir(runs_dir) 
                if d.startswith('inlist_M') and os.path.isdir(os.path.join(runs_dir, d))]
    
    if not run_dirs:
        print("No batch run directories found")
        return
    
    print(f"Found {len(run_dirs)} model runs")
    
    # Parse run parameters and collect data
    all_data = []
    mass_colors = {}
    scheme_linestyles = {}
    
    for run_dir in run_dirs:
        history_path = os.path.join(runs_dir, run_dir, "LOGS", "history.data")
        
        if not os.path.exists(history_path):
            print(f"Warning: No history file in {run_dir}")
            continue
        
        try:
            # Parse parameters from directory name
            parts = run_dir.replace('inlist_M', '').split('_')
            mass = float(parts[0])
            metallicity = float(parts[1][1:]) if len(parts) > 1 else 0.014
            
            if 'noovs' in run_dir:
                scheme = 'none'
                fov = 0.0
            else:
                scheme = parts[2] if len(parts) > 2 else 'unknown'
                fov = float(parts[3][3:]) if len(parts) > 3 else 0.0
            
            # Load data
            md = mr.MesaData(history_path)
            
            # Get filter information
            all_cols, filter_columns = read_header_columns(history_path)
            
            if not filter_columns:
                print(f"No photometric filters in {run_dir}, skipping...")
                continue
            
            # Set up photometric system
            phot_system = setup_photometric_system(md, filter_columns)
            
            if phot_system is None:
                print(f"No compatible photometric system in {run_dir}, skipping...")
                continue
            
            # Store data
            run_info = {
                'data': md,
                'mass': mass,
                'metallicity': metallicity,
                'scheme': scheme,
                'fov': fov,
                'phot_system': phot_system,
                'filter_columns': filter_columns,
                'run_dir': run_dir
            }
            all_data.append(run_info)
            
            # Assign colors by mass
            if mass not in mass_colors:
                mass_colors[mass] = plt.cm.viridis(len(mass_colors) / 10.0)
            
            # Assign line styles by scheme
            if scheme not in scheme_linestyles:
                styles = ['-', '--', '-.', ':']
                scheme_linestyles[scheme] = styles[len(scheme_linestyles) % len(styles)]
                
        except Exception as e:
            print(f"Error processing {run_dir}: {e}")
            continue
    
    if not all_data:
        print("No valid data found!")
        return
    
    print(f"Successfully loaded {len(all_data)} models")
    print(f"Available masses: {sorted(mass_colors.keys())}")
    print(f"Available schemes: {list(scheme_linestyles.keys())}")
    
    # Determine common photometric system
    systems = [run['phot_system']['name'] for run in all_data]
    from collections import Counter
    most_common_system = Counter(systems).most_common(1)[0][0]
    
    # Filter to models with the most common system
    filtered_data = [run for run in all_data if run['phot_system']['name'] == most_common_system]
    print(f"Using {most_common_system} photometric system for {len(filtered_data)} models")
    
    # Create comprehensive comparison plots
    create_magnitude_comparison(filtered_data, mass_colors, scheme_linestyles, most_common_system)
    create_color_evolution_comparison(filtered_data, mass_colors, scheme_linestyles, most_common_system)
    create_physics_photometry_correlation(filtered_data, mass_colors, scheme_linestyles, most_common_system)

def create_magnitude_comparison(all_data, mass_colors, scheme_linestyles, system_name):
    """Create magnitude lightcurve comparisons."""
    
    phot_system = all_data[0]['phot_system']
    n_filters = len(phot_system['filters'])
    
    fig, axes = plt.subplots(2, n_filters, figsize=(5*n_filters, 10))
    if n_filters == 1:
        axes = axes.reshape(2, 1)
    
    for i, filter_name in enumerate(phot_system['filters']):
        # Top panel: Absolute magnitudes
        ax1 = axes[0, i]
        
        for run in all_data:
            md = run['data']
            age_myr = md.star_age / 1e6
            
            try:
                mag_data = getattr(md, filter_name)
            except AttributeError:
                mag_data = md.data(filter_name)
            
            color = mass_colors[run['mass']]
            linestyle = scheme_linestyles[run['scheme']]
            
            label = f"M={run['mass']:.1f}, {run['scheme']}"
            ax1.plot(age_myr, mag_data, color=color, linestyle=linestyle, 
                    linewidth=2, label=label, alpha=0.8)
        
        ax1.set_xlabel("Age (Myr)")
        ax1.set_ylabel(f"{filter_name} magnitude")
        ax1.set_title(f"{filter_name} Band Evolution")
        ax1.invert_yaxis()
        ax1.grid(alpha=0.3)
        
        if i == 0:  # Only show legend on first plot
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Bottom panel: Magnitude differences from initial
        ax2 = axes[1, i]
        
        for run in all_data:
            md = run['data']
            age_myr = md.star_age / 1e6
            
            try:
                mag_data = getattr(md, filter_name)
            except AttributeError:
                mag_data = md.data(filter_name)
            
            # Calculate change from initial magnitude
            mag_change = mag_data - mag_data[0]
            
            color = mass_colors[run['mass']]
            linestyle = scheme_linestyles[run['scheme']]
            
            ax2.plot(age_myr, mag_change, color=color, linestyle=linestyle, 
                    linewidth=2, alpha=0.8)
        
        ax2.set_xlabel("Age (Myr)")
        ax2.set_ylabel(f"Δ{filter_name} (mag)")
        ax2.set_title(f"{filter_name} Change from ZAMS")
        ax2.grid(alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    
    plt.suptitle(f"{system_name} Photometric Evolution Comparison", fontsize=16)
    plt.tight_layout()
    
    os.makedirs("plots", exist_ok=True)
    plt.savefig(f"plots/batch_lightcurves_{system_name.lower()}.png", 
                dpi=300, bbox_inches='tight')
    print(f"Saved: plots/batch_lightcurves_{system_name.lower()}.png")
    plt.show()

def create_color_evolution_comparison(all_data, mass_colors, scheme_linestyles, system_name):
    """Create color evolution comparisons."""
    
    phot_system = all_data[0]['phot_system']
    colors = phot_system['colors']
    
    if not colors:
        print("No colors available for comparison")
        return
    
    n_colors = len(colors)
    fig, axes = plt.subplots(2, n_colors, figsize=(6*n_colors, 10))
    if n_colors == 1:
        axes = axes.reshape(2, 1)
    
    for i, color_name in enumerate(colors):
        f1, f2 = color_name.split('-')
        
        # Top panel: Color evolution
        ax1 = axes[0, i]
        
        for run in all_data:
            md = run['data']
            age_myr = md.star_age / 1e6
            
            try:
                mag1 = getattr(md, f1)
                mag2 = getattr(md, f2)
            except AttributeError:
                mag1 = md.data(f1)
                mag2 = md.data(f2)
            
            color_data = mag1 - mag2
            
            color = mass_colors[run['mass']]
            linestyle = scheme_linestyles[run['scheme']]
            
            label = f"M={run['mass']:.1f}, {run['scheme']}"
            ax1.plot(age_myr, color_data, color=color, linestyle=linestyle, 
                    linewidth=2, label=label, alpha=0.8)
        
        ax1.set_xlabel("Age (Myr)")
        ax1.set_ylabel(f"{color_name}")
        ax1.set_title(f"{color_name} Color Evolution")
        ax1.grid(alpha=0.3)
        
        if i == 0:
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Bottom panel: Color change rate
        ax2 = axes[1, i]
        
        for run in all_data:
            md = run['data']
            age_myr = md.star_age / 1e6
            
            try:
                mag1 = getattr(md, f1)
                mag2 = getattr(md, f2)
            except AttributeError:
                mag1 = md.data(f1)
                mag2 = md.data(f2)
            
            color_data = mag1 - mag2
            
            # Calculate color change rate
            if len(age_myr) > 1:
                dt = np.diff(age_myr)
                dc = np.diff(color_data)
                color_rate = dc / dt
                
                color = mass_colors[run['mass']]
                linestyle = scheme_linestyles[run['scheme']]
                
                ax2.plot(age_myr[1:], color_rate, color=color, linestyle=linestyle, 
                        linewidth=2, alpha=0.8)
        
        ax2.set_xlabel("Age (Myr)")
        ax2.set_ylabel(f"d({color_name})/dt (mag/Myr)")
        ax2.set_title(f"{color_name} Change Rate")
        ax2.grid(alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    
    plt.suptitle(f"{system_name} Color Evolution Comparison", fontsize=16)
    plt.tight_layout()
    
    plt.savefig(f"plots/batch_color_evolution_{system_name.lower()}.png", 
                dpi=300, bbox_inches='tight')
    print(f"Saved: plots/batch_color_evolution_{system_name.lower()}.png")
    plt.show()

def create_physics_photometry_correlation(all_data, mass_colors, scheme_linestyles, system_name):
    """Create plots showing correlations between internal physics and photometric properties."""
    
    phot_system = all_data[0]['phot_system']
    primary_color = phot_system['primary_color']
    primary_mag = phot_system['primary_mag']
    
    f1, f2 = primary_color.split('-')
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Color vs Central Temperature
    for run in all_data:
        md = run['data']
        
        if hasattr(md, 'log_center_T'):
            try:
                mag1 = getattr(md, f1)
                mag2 = getattr(md, f2)
            except AttributeError:
                mag1 = md.data(f1)
                mag2 = md.data(f2)
            
            color_data = mag1 - mag2
            
            color = mass_colors[run['mass']]
            linestyle = scheme_linestyles[run['scheme']]
            
            label = f"M={run['mass']:.1f}, {run['scheme']}"
            ax1.plot(md.log_center_T, color_data, color=color, linestyle=linestyle, 
                    linewidth=2, label=label, alpha=0.8)
    
    ax1.set_xlabel("log Central Temperature")
    ax1.set_ylabel(f"{primary_color}")
    ax1.set_title("Color vs Central Temperature")
    ax1.grid(alpha=0.3)
    ax1.legend()
    
    # Plot 2: Magnitude vs Central Density
    for run in all_data:
        md = run['data']
        
        if hasattr(md, 'log_center_Rho'):
            try:
                mag_data = getattr(md, primary_mag)
            except AttributeError:
                mag_data = md.data(primary_mag)
            
            color = mass_colors[run['mass']]
            linestyle = scheme_linestyles[run['scheme']]
            
            ax2.plot(md.log_center_Rho, mag_data, color=color, linestyle=linestyle, 
                    linewidth=2, alpha=0.8)
    
    ax2.set_xlabel("log Central Density")
    ax2.set_ylabel(f"{primary_mag} magnitude")
    ax2.set_title("Magnitude vs Central Density")
    ax2.invert_yaxis()
    ax2.grid(alpha=0.3)
    
    # Plot 3: Color vs Convective Core Mass (if available)
    for run in all_data:
        md = run['data']
        
        # Look for core mass data
        core_mass = None
        if hasattr(md, 'he_core_mass'):
            core_mass = md.he_core_mass
        elif hasattr(md, 'mass_conv_core'):
            core_mass = md.mass_conv_core
        elif hasattr(md, 'conv_mx1_top'):
            core_mass = md.conv_mx1_top * getattr(md, 'star_mass', 1.0)
        
        if core_mass is not None:
            try:
                mag1 = getattr(md, f1)
                mag2 = getattr(md, f2)
            except AttributeError:
                mag1 = md.data(f1)
                mag2 = md.data(f2)
            
            color_data = mag1 - mag2
            
            color = mass_colors[run['mass']]
            linestyle = scheme_linestyles[run['scheme']]
            
            ax3.plot(core_mass, color_data, color=color, linestyle=linestyle, 
                    linewidth=2, alpha=0.8)
    
    ax3.set_xlabel("Convective Core Mass (M☉)")
    ax3.set_ylabel(f"{primary_color}")
    ax3.set_title("Color vs Convective Core Mass")
    ax3.grid(alpha=0.3)
    
    # Plot 4: Luminosity vs Surface Temperature (HR-like but with photometry)
    for run in all_data:
        md = run['data']
        
        if hasattr(md, 'log_Teff') and hasattr(md, 'log_L'):
            # Color by photometric color
            try:
                mag1 = getattr(md, f1)
                mag2 = getattr(md, f2)
            except AttributeError:
                mag1 = md.data(f1)
                mag2 = md2.data(f2)
            
            color_data = mag1 - mag2
            
            scatter = ax4.scatter(md.log_Teff, md.log_L, c=color_data, 
                                cmap='viridis', s=20, alpha=0.7)
    
    ax4.set_xlabel("log Teff")
    ax4.set_ylabel("log L/L☉")
    ax4.set_title(f"HR Diagram Colored by {primary_color}")
    ax4.invert_xaxis()
    ax4.grid(alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label(f"{primary_color}")
    
    plt.suptitle(f"{system_name} Physics-Photometry Correlations", fontsize=16)
    plt.tight_layout()
    
    plt.savefig(f"plots/batch_physics_photometry_{system_name.lower()}.png", 
                dpi=300, bbox_inches='tight')
    print(f"Saved: plots/batch_physics_photometry_{system_name.lower()}.png")
    plt.show()

if __name__ == "__main__":
    print("MESA Batch Custom Colors Lightcurve Analysis")
    print("============================================")
    
    # Check for runs directory
    if os.path.exists("../runs"):
        plot_batch_lightcurves("../runs")
    elif os.path.exists("runs"):
        plot_batch_lightcurves("runs")
    else:
        print("No runs directory found. Please ensure you have completed batch runs.")
        print("Expected directory structure: ../runs/ or runs/")