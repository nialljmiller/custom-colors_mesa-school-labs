#!/usr/bin/env python3
"""
colorcolor_plot.py - Consolidated Color-Color Diagram Generator for MESA
Creates color-color diagrams with physics parameter color coding and 3D analysis
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

def setup_colorcolor_params(md, filter_columns):
    """Set up color-color parameters based on available filters with priority system."""
    
    # Priority 1: GAIA colors (Gbp-Grp vs Grp-Grvs)
    if all(f in filter_columns and hasattr(md, f) for f in ['Gbp', 'Grp', 'Grvs']):
        color1 = md.Gbp - md.Grp
        color2 = md.Grp - md.Grvs
        color1_label = "Gbp - Grp"
        color2_label = "Grp - Grvs"
        system = "GAIA"
        print("Using GAIA color-color: (Gbp-Grp) vs (Grp-Grvs)")
        
    # Priority 2: Johnson-Cousins (B-V vs V-I)
    elif all(f in filter_columns and hasattr(md, f) for f in ['B', 'V', 'I']):
        color1 = md.B - md.V
        color2 = md.V - md.I
        color1_label = "B - V"
        color2_label = "V - I"
        system = "Johnson"
        print("Using Johnson color-color: (B-V) vs (V-I)")
        
    # Priority 3: SDSS (g-r vs r-i)
    elif all(f in filter_columns and hasattr(md, f) for f in ['g', 'r', 'i']):
        color1 = getattr(md, 'g') - getattr(md, 'r')
        color2 = getattr(md, 'r') - getattr(md, 'i')
        color1_label = "g - r"
        color2_label = "r - i"
        system = "SDSS"
        print("Using SDSS color-color: (g-r) vs (r-i)")
        
    # Priority 4: 2MASS (J-H vs H-K)
    elif all(f in filter_columns and hasattr(md, f) for f in ['J', 'H', 'K']):
        color1 = md.J - md.H
        color2 = md.H - md.K
        color1_label = "J - H"
        color2_label = "H - K"
        system = "2MASS"
        print("Using 2MASS color-color: (J-H) vs (H-K)")
        
    # Fallback: Use available filters to construct colors
    elif len(filter_columns) >= 3:
        f1, f2, f3 = filter_columns[0], filter_columns[1], filter_columns[2]
        try:
            col1 = getattr(md, f1)
            col2 = getattr(md, f2)
            col3 = getattr(md, f3)
        except AttributeError:
            col1 = md.data(f1)
            col2 = md.data(f2)
            col3 = md.data(f3)
            
        color1 = col1 - col2
        color2 = col2 - col3
        color1_label = f"{f1} - {f2}"
        color2_label = f"{f2} - {f3}"
        system = "Custom"
        print(f"Using custom color-color: ({color1_label}) vs ({color2_label})")
        
    else:
        print("Error: Need at least 3 filters for color-color diagram")
        return None, None, None, None, None
    
    return color1, color2, color1_label, color2_label, system

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

def plot_single_colorcolor(logs_path="LOGS", physics_param='center_h1'):
    """Create color-color plots for a single MESA run with physics parameter color coding."""
    
    history_path = os.path.join(logs_path, "history.data")
    if not os.path.exists(history_path):
        print(f"Error: Could not find history file at {history_path}")
        return False
        
    try:
        data = mr.MesaData(history_path)
        all_cols, filter_columns = read_header_columns(history_path)
        color1, color2, color1_label, color2_label, system = setup_colorcolor_params(data, filter_columns)
        
        if color1 is None:
            print("Error: Could not set up color-color parameters")
            return False
            
        # Get physics parameter for color coding
        physics_data, physics_label = get_physics_param(data, physics_param)
        if physics_data is None:
            print(f"Warning: {physics_label}. Using model number instead.")
            physics_data = data.model_number
            physics_label = 'model_number'
            
        # Create plots directory
        os.makedirs("plots", exist_ok=True)
        
        # 2D Color-Color with physics parameter color coding
        plt.figure(figsize=(10, 10))
        scatter = plt.scatter(color1, color2, c=physics_data, 
                            cmap='viridis', s=20, alpha=0.7)
        
        # Mark start and end points
        plt.scatter(color1[0], color2[0], color='red', marker='o', 
                   s=100, label='Start', edgecolors='black')
        plt.scatter(color1[-1], color2[-1], color='blue', marker='s', 
                   s=100, label='End', edgecolors='black')
        
        plt.xlabel(color1_label, fontsize=14)
        plt.ylabel(color2_label, fontsize=14)
        
        plt.grid(alpha=0.3)
        plt.legend()
        plt.title(f'{system} Color-Color Diagram colored by {physics_label}', fontsize=16)
        
        # Add colorbar
        cbar = plt.colorbar(scatter)
        cbar.set_label(physics_label, fontsize=12)
        
        plt.tight_layout()
        plt.savefig(f"plots/colorcolor_{system.lower()}_{physics_param}.png", dpi=300, bbox_inches='tight')
        print(f"Saved 2D color-color to plots/colorcolor_{system.lower()}_{physics_param}.png")
        plt.show()
        
        # 3D Color-Color with age as z-axis
        if hasattr(data, 'star_age'):
            fig = plt.figure(figsize=(14, 10))
            ax = fig.add_subplot(111, projection='3d')
            
            age_myr = data.star_age / 1e6  # Convert to Myr
            
            scatter_3d = ax.scatter(color1, color2, age_myr, 
                                  c=physics_data, cmap='viridis', s=20, alpha=0.7)
            
            # Mark evolution points
            ax.scatter(color1[0], color2[0], age_myr[0], 
                      color='green', marker='o', s=100, label='Start')
            ax.scatter(color1[-1], color2[-1], age_myr[-1], 
                      color='red', marker='s', s=100, label='End')
            
            ax.set_xlabel(color1_label, fontsize=12)
            ax.set_ylabel(color2_label, fontsize=12)
            ax.set_zlabel('Age (Myr)', fontsize=12)
            ax.legend()
            
            plt.title(f"3D {system} Color-Color Evolution", fontsize=16)
            
            # Add colorbar
            cbar = plt.colorbar(scatter_3d, ax=ax, shrink=0.5, aspect=30)
            cbar.set_label(physics_label, fontsize=12)
            
            plt.savefig(f"plots/colorcolor_3d_{system.lower()}_{physics_param}.png", dpi=300, bbox_inches='tight')
            print(f"Saved 3D color-color to plots/colorcolor_3d_{system.lower()}_{physics_param}.png")
            plt.show()
            
        return True
        
    except Exception as e:
        print(f"Error creating color-color plots: {e}")
        return False

def plot_batch_colorcolor(runs_dir="../batch_runs/runs", physics_param='mass'):
    """Create batch color-color plots with physics parameter color coding."""
    
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
            color1, color2, color1_label, color2_label, system = setup_colorcolor_params(data, filter_columns)
            
            if color1 is None:
                continue
            
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
            
            # Store data
            run_info = {
                'data': data,
                'color1': color1,
                'color2': color2,
                'color1_label': color1_label,
                'color2_label': color2_label,
                'system': system,
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
        
    # Determine the photometric system to use
    systems = [d['system'] for d in all_data]
    primary_system = max(set(systems), key=systems.count)
    primary_data = [d for d in all_data if d['system'] == primary_system]
    
    print(f"Creating batch color-color plots using {primary_system} system")
    print(f"Found {len(primary_data)} models with {primary_system} photometry")
    
    # Normalize physics values for color mapping
    norm = Normalize(vmin=min(physics_values), vmax=max(physics_values))
    cmap = cm.viridis
    
    # Create batch color-color plot
    plt.figure(figsize=(12, 12))
    
    for run_info in primary_data:
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
            
        plt.plot(run_info['color1'], run_info['color2'], 
                color=color, linestyle=linestyle, linewidth=2, 
                label=label, alpha=0.8)
        
        # Mark start and end points
        plt.scatter(run_info['color1'][0], run_info['color2'][0], 
                   color=color, marker='o', s=30, alpha=0.7)
        plt.scatter(run_info['color1'][-1], run_info['color2'][-1], 
                   color=color, marker='s', s=30, alpha=0.7)
    
    plt.xlabel(f"{primary_data[0]['color1_label']}", fontsize=14)
    plt.ylabel(f"{primary_data[0]['color2_label']}", fontsize=14)
        
    plt.grid(alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.title(f"Batch {primary_system} Color-Color Diagrams colored by {physics_param}", fontsize=16)
    
    # Add colorbar for physics parameter
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=plt.gca())
    cbar.set_label(physics_param, fontsize=12)
    
    os.makedirs("plots", exist_ok=True)
    plt.tight_layout()
    plt.savefig(f"plots/batch_colorcolor_{primary_system.lower()}_{physics_param}.png", dpi=300, bbox_inches='tight')
    print(f"Saved batch color-color to plots/batch_colorcolor_{primary_system.lower()}_{physics_param}.png")
    plt.show()
    
    # Create 3D batch plot with Teff as z-axis
    if all(hasattr(d['data'], 'log_Teff') for d in primary_data):
        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_subplot(111, projection='3d')
        
        for run_info in primary_data:
            color = cmap(norm(run_info['physics_value']))
            
            if run_info['scheme'] == 'none':
                linestyle = '-'
            elif run_info['scheme'] == 'exponential':
                linestyle = '--'
            else:
                linestyle = '-.'
            
            # Use log_Teff evolution as z-coordinate
            teff_data = run_info['data'].log_Teff
            
            ax.plot(run_info['color1'], run_info['color2'], teff_data,
                   color=color, linestyle=linestyle, linewidth=2, alpha=0.8)
            
            # Mark endpoints
            ax.scatter(run_info['color1'][0], run_info['color2'][0], teff_data[0],
                      color=color, marker='o', s=50)
            ax.scatter(run_info['color1'][-1], run_info['color2'][-1], teff_data[-1],
                      color=color, marker='s', s=50)
        
        ax.set_xlabel(f"{primary_data[0]['color1_label']}", fontsize=12)
        ax.set_ylabel(f"{primary_data[0]['color2_label']}", fontsize=12)
        ax.set_zlabel('log Teff', fontsize=12)
        
        plt.title(f"3D Batch {primary_system} Color-Color Evolution (Teff tracks)", fontsize=16)
        
        # Add colorbar
        cbar = plt.colorbar(sm, ax=ax, shrink=0.5, aspect=30)
        cbar.set_label(physics_param, fontsize=12)
        
        plt.savefig(f"plots/batch_colorcolor_3d_{primary_system.lower()}_{physics_param}.png", dpi=300, bbox_inches='tight')
        print(f"Saved 3D batch color-color to plots/batch_colorcolor_3d_{primary_system.lower()}_{physics_param}.png")
        plt.show()
    
    return True

def main():
    """Main function to determine whether to plot single or batch color-color analysis."""
    
    # Check for single run
    single_run_found = False
    for logs_path in ["../../LOGS", "../LOGS", "LOGS"]:
        if os.path.isdir(logs_path):
            print(f"Found LOGS directory at {logs_path}. Creating color-color plots for single run.")
            
            # Create only the most informative color-color plot
            print(f"\nCreating color-color plot colored by center_h1 (evolutionary phase)...")
            plot_single_colorcolor(logs_path, 'center_h1')
            
            single_run_found = True
            break
    
    # Check for batch runs
    batch_run_found = False
    for runs_path in ["../batch_runs/runs", "runs"]:
        if os.path.isdir(runs_path):
            print(f"\nFound batch runs directory at {runs_path}. Creating batch color-color analysis.")
            
            # Create only the most informative batch color-color plot
            print(f"\nCreating batch color-color plot colored by mass...")
            plot_batch_colorcolor(runs_path, 'mass')
            
            batch_run_found = True
            break
    
    if not single_run_found and not batch_run_found:
        print("Error: Could not find LOGS directory or batch runs directory.")
        print("Make sure you're running this script from the right location.")

if __name__ == "__main__":
    main()