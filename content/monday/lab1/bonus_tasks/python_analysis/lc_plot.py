#!/usr/bin/env python3
"""
lightcurve_plot.py - Consolidated Lightcurve Generator for MESA
Time series photometry with physics parameter color coding and 3D filter analysis
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import mesa_reader as mr
import glob
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

def get_available_filters(md, filter_columns):
    """Get available photometric filters with priority system."""
    available_filters = []
    
    # Priority order for lightcurves
    priority_filters = ['G', 'Gbp', 'Grp', 'V', 'B', 'R', 'I', 'J', 'H', 'K', 'g', 'r', 'i']
    
    # Add priority filters if available
    for filt in priority_filters:
        if filt in filter_columns and hasattr(md, filt):
            available_filters.append(filt)
    
    # Add any other available filters
    for filt in filter_columns:
        if filt not in available_filters and hasattr(md, filt):
            available_filters.append(filt)
    
    return available_filters

def get_physics_param(md, param_name):
    """Get physics parameter for color coding - focused on most informative recorded columns."""
    physics_params = {
        # Most informative recorded parameters
        'center_h1': 'center_h1',           # Hydrogen depletion - evolutionary phase
        'he_core_mass': 'he_core_mass',     # Core evolution
        'log_LH': 'log_LH',                 # Hydrogen burning power
        'mass_conv_core': 'mass_conv_core', # Convective core size
        'center_he4': 'center_he4',         # Helium abundance evolution
        
        # Basic stellar properties
        'mass': 'star_mass',
        'age': 'star_age',
        'teff': 'log_Teff',
        'luminosity': 'log_L',
        'radius': 'log_R'
    }
    
    if param_name not in physics_params:
        return None, f"Unknown parameter: {param_name}"
    
    param_col = physics_params[param_name]
    if hasattr(md, param_col):
        return getattr(md, param_col), param_col
    else:
        return None, f"{param_col} not found"

def plot_single_lightcurve(logs_path="LOGS", physics_param='center_h1'):
    """Create lightcurve plots for a single MESA run with physics parameter color coding."""
    
    history_path = os.path.join(logs_path, "history.data")
    if not os.path.exists(history_path):
        print(f"Error: Could not find history file at {history_path}")
        return False
        
    try:
        data = mr.MesaData(history_path)
        all_cols, filter_columns = read_header_columns(history_path)
        available_filters = get_available_filters(data, filter_columns)
        
        if not available_filters:
            print("Error: No photometric filters found for lightcurve")
            return False
            
        # Get time data
        if hasattr(data, 'star_age'):
            time_data = data.star_age / 1e6  # Convert to Myr
            time_label = 'Age (Myr)'
        else:
            time_data = data.model_number
            time_label = 'Model Number'
            
        # Get physics parameter for color coding
        physics_data, physics_label = get_physics_param(data, physics_param)
        if physics_data is None:
            print(f"Warning: {physics_label}. Using model number instead.")
            physics_data = data.model_number
            physics_label = 'model_number'
            
        # Create plots directory
        os.makedirs("plots", exist_ok=True)
        
        # Select primary filter for 2D plot (prefer G, then V, then first available)
        primary_filter = None
        for filt in ['G', 'V']:
            if filt in available_filters:
                primary_filter = filt
                break
        if primary_filter is None:
            primary_filter = available_filters[0]
            
        primary_mag = getattr(data, primary_filter)
        
        # 2D Lightcurve with physics parameter color coding
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(time_data, primary_mag, c=physics_data, 
                            cmap='viridis', s=20, alpha=0.7)
        
        # Mark start and end points
        plt.scatter(time_data[0], primary_mag[0], color='red', marker='o', 
                   s=100, label='Start', edgecolors='black')
        plt.scatter(time_data[-1], primary_mag[-1], color='blue', marker='s', 
                   s=100, label='End', edgecolors='black')
        
        plt.xlabel(time_label, fontsize=14)
        plt.ylabel(f'{primary_filter} magnitude', fontsize=14)
        plt.gca().invert_yaxis()  # Magnitudes decrease upward
        
        plt.grid(alpha=0.3)
        plt.legend()
        plt.title(f'{primary_filter} Lightcurve colored by {physics_label}', fontsize=16)
        
        # Add colorbar
        cbar = plt.colorbar(scatter)
        cbar.set_label(physics_label, fontsize=12)
        
        plt.tight_layout()
        plt.savefig(f"plots/lightcurve_{primary_filter.lower()}_{physics_param}.png", dpi=300, bbox_inches='tight')
        print(f"Saved 2D lightcurve to plots/lightcurve_{primary_filter.lower()}_{physics_param}.png")
        plt.show()
        
        # 3D Lightcurve with multiple filters
        if len(available_filters) > 1:
            fig = plt.figure(figsize=(14, 10))
            ax = fig.add_subplot(111, projection='3d')
            
            # Create filter wavelength mapping for z-axis
            filter_wavelengths = {
                'Gbp': 0.51, 'G': 0.62, 'Grp': 0.78,  # GAIA
                'B': 0.44, 'V': 0.55, 'R': 0.64, 'I': 0.79,  # Johnson-Cousins
                'J': 1.22, 'H': 1.63, 'K': 2.19,  # 2MASS
                'g': 0.48, 'r': 0.62, 'i': 0.75, 'z': 0.91  # SDSS
            }
            
            # Plot up to 5 filters to avoid clutter
            plot_filters = available_filters[:5]
            
            for i, filt in enumerate(plot_filters):
                mag_data = getattr(data, filt)
                wavelength = filter_wavelengths.get(filt, 0.5 + i*0.1)  # Default spacing
                z_coord = np.full_like(time_data, wavelength)
                
                scatter_3d = ax.scatter(time_data, mag_data, z_coord,
                                      c=physics_data, cmap='viridis', s=15, alpha=0.6,
                                      label=f'{filt} ({wavelength:.2f}μm)')
            
            ax.set_xlabel(time_label, fontsize=12)
            ax.set_ylabel('Magnitude', fontsize=12)
            ax.set_zlabel('Wavelength (μm)', fontsize=12)
            ax.invert_yaxis()
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.title(f"3D Multi-Filter Lightcurve Evolution", fontsize=16)
            
            # Add colorbar
            cbar = plt.colorbar(scatter_3d, ax=ax, shrink=0.5, aspect=30)
            cbar.set_label(physics_label, fontsize=12)
            
            plt.savefig(f"plots/lightcurve_3d_multifilter_{physics_param}.png", dpi=300, bbox_inches='tight')
            print(f"Saved 3D lightcurve to plots/lightcurve_3d_multifilter_{physics_param}.png")
            plt.show()
            
        return True
        
    except Exception as e:
        print(f"Error creating lightcurve plots: {e}")
        return False

def plot_batch_lightcurves(runs_dir="../runs", physics_param='mass'):
    """Create batch lightcurve plots with physics parameter color coding."""
    
    if not os.path.isdir(runs_dir):
        print(f"Error: Could not find {runs_dir} directory")
        return False
        
    # Find all run directories
    run_dirs = [d for d in os.listdir(runs_dir) 
                if os.path.isdir(os.path.join(runs_dir, d)) and d.startswith("inlist_")]
    
    if not run_dirs:
        print("No batch run directories found")
        return False
        
    # Parse run parameters and collect data
    all_data = []
    physics_values = []
    
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
            available_filters = get_available_filters(data, filter_columns)
            
            if not available_filters:
                continue
            
            # Get time data
            if hasattr(data, 'star_age'):
                time_data = data.star_age / 1e6  # Convert to Myr
                time_label = 'Age (Myr)'
            else:
                time_data = data.model_number
                time_label = 'Model Number'
            
            # Get physics parameter value
            if physics_param == 'mass':
                phys_value = mass
            elif physics_param == 'metallicity':
                phys_value = metallicity  
            elif physics_param == 'fov':
                phys_value = fov
            elif physics_param == 'center_h1':
                # Use initial hydrogen abundance for comparison
                phys_data, _ = get_physics_param(data, physics_param)
                phys_value = phys_data[0] if phys_data is not None else 0
            else:
                # Use final value for most other parameters
                phys_data, _ = get_physics_param(data, physics_param)
                phys_value = phys_data[-1] if phys_data is not None else 0
            
            # Select primary filter
            primary_filter = None
            for filt in ['G', 'V']:
                if filt in available_filters:
                    primary_filter = filt
                    break
            if primary_filter is None:
                primary_filter = available_filters[0]
                
            primary_mag = getattr(data, primary_filter)
            
            # Store data
            run_info = {
                'data': data,
                'time_data': time_data,
                'time_label': time_label,
                'primary_filter': primary_filter,
                'primary_mag': primary_mag,
                'available_filters': available_filters,
                'mass': mass,
                'metallicity': metallicity,
                'scheme': scheme,
                'fov': fov,
                'run_dir': run_dir,
                'physics_value': phys_value
            }
            all_data.append(run_info)
            physics_values.append(phys_value)
            
        except Exception as e:
            print(f"Error processing {run_dir}: {e}")
            continue
    
    if not all_data:
        print("No valid data found in batch runs")
        return False
        
    print(f"Creating batch lightcurve plots for {len(all_data)} models")
    
    # Normalize physics values for color mapping
    norm = Normalize(vmin=min(physics_values), vmax=max(physics_values))
    cmap = cm.viridis
    
    # Use the most common filter and time label
    primary_filters = [d['primary_filter'] for d in all_data]
    common_filter = max(set(primary_filters), key=primary_filters.count)
    common_time_label = all_data[0]['time_label']
    
    # Create batch lightcurve plot
    plt.figure(figsize=(14, 10))
    
    for run_info in all_data:
        if run_info['primary_filter'] != common_filter:
            continue  # Skip models without the common filter
            
        color = cmap(norm(run_info['physics_value']))
        
        # Different line styles for different schemes
        if run_info['scheme'] == 'none':
            linestyle = '-'
        elif run_info['scheme'] == 'exponential':
            linestyle = '--'
        elif run_info['scheme'] == 'step':
            linestyle = '-.'
        else:
            linestyle = ':'
            
        label = f"M={run_info['mass']}M☉"
        if run_info['scheme'] != 'none':
            label += f", {run_info['scheme']}"
        if run_info['fov'] > 0:
            label += f" (f_ov={run_info['fov']})"
            
        plt.plot(run_info['time_data'], run_info['primary_mag'], 
                color=color, linestyle=linestyle, linewidth=2, 
                label=label, alpha=0.8)
        
        # Mark start and end points
        plt.scatter(run_info['time_data'][0], run_info['primary_mag'][0], 
                   color=color, marker='o', s=30, alpha=0.7)
        plt.scatter(run_info['time_data'][-1], run_info['primary_mag'][-1], 
                   color=color, marker='s', s=30, alpha=0.7)
    
    plt.xlabel(common_time_label, fontsize=14)
    plt.ylabel(f'{common_filter} magnitude', fontsize=14)
    plt.gca().invert_yaxis()
        
    plt.grid(alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.title(f"Batch {common_filter} Lightcurves colored by {physics_param}", fontsize=16)
    
    # Add colorbar for physics parameter
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=plt.gca())
    cbar.set_label(physics_param, fontsize=12)
    
    os.makedirs("plots", exist_ok=True)
    plt.tight_layout()
    plt.savefig(f"plots/batch_lightcurve_{common_filter.lower()}_{physics_param}.png", dpi=300, bbox_inches='tight')
    print(f"Saved batch lightcurve to plots/batch_lightcurve_{common_filter.lower()}_{physics_param}.png")
    plt.show()
    
    # Create 3D batch plot with age as z-axis
    if all(hasattr(d['data'], 'star_age') for d in all_data):
        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_subplot(111, projection='3d')
        
        for run_info in all_data:
            if run_info['primary_filter'] != common_filter:
                continue
                
            color = cmap(norm(run_info['physics_value']))
            
            if run_info['scheme'] == 'none':
                linestyle = '-'
            elif run_info['scheme'] == 'exponential':
                linestyle = '--'
            else:
                linestyle = '-.'
            
            # Use mass as z-coordinate to separate models visually
            z_coord = run_info['data'].log_Teff            

            ax.plot(run_info['time_data'], run_info['primary_mag'], z_coord,
                   color=color, linestyle=linestyle, linewidth=2, alpha=0.8)
            
            # Mark endpoints
            ax.scatter(run_info['time_data'][0], run_info['primary_mag'][0], z_coord[0],
                      color=color, marker='o', s=50)
            ax.scatter(run_info['time_data'][-1], run_info['primary_mag'][-1], z_coord[-1],
                      color=color, marker='s', s=50)
        
        ax.set_xlabel(common_time_label, fontsize=12)
        ax.set_ylabel(f'{common_filter} magnitude', fontsize=12)
        ax.set_zlabel('Teff', fontsize=12)
        ax.invert_yaxis()
        
        plt.title(f"3D Batch {common_filter} Lightcurve Evolution (log_Teff tracks)", fontsize=16)
        
        # Add colorbar
        cbar = plt.colorbar(sm, ax=ax, shrink=0.5, aspect=30)
        cbar.set_label(physics_param, fontsize=12)
        
        plt.savefig(f"plots/batch_lightcurve_3d_{common_filter.lower()}_{physics_param}.png", dpi=300, bbox_inches='tight')
        print(f"Saved 3D batch lightcurve to plots/batch_lightcurve_3d_{common_filter.lower()}_{physics_param}.png")
        plt.show()
    
    return True

def main():
    """Main function to determine whether to plot single or batch lightcurve analysis."""
    
    # Check for single run
    single_run_found = False
    for logs_path in ["../../LOGS", "../LOGS", "LOGS"]:
        if os.path.isdir(logs_path):
            print(f"Found LOGS directory at {logs_path}. Creating lightcurve plots for single run.")
            
            # Create only the most informative lightcurve plot
            print(f"\nCreating lightcurve plot colored by center_h1 (evolutionary phase)...")
            plot_single_lightcurve(logs_path, 'center_h1')
            
            single_run_found = True
            break
    
    # Check for batch runs
    batch_run_found = False
    for runs_path in ["../runs", "runs"]:
        if os.path.isdir(runs_path):
            print(f"\nFound batch runs directory at {runs_path}. Creating batch lightcurve analysis.")
            
            # Create only the most informative batch lightcurve plot
            print(f"\nCreating batch lightcurve plot colored by mass...")
            plot_batch_lightcurves(runs_path, 'mass')
            
            batch_run_found = True
            break
    
    if not single_run_found and not batch_run_found:
        print("Error: Could not find LOGS directory or batch runs directory.")
        print("Make sure you're running this script from the right location.")

if __name__ == "__main__":
    main()