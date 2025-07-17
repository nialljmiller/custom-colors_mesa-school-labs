#!/usr/bin/env python3
"""
cmd_3d_age.py - Simplified 3D Color-Magnitude Diagram Generator with Age Axis
Creates only 3D CMD plots where the third axis is stellar age
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import mesa_reader as mr
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
        color_label = r"$\log(T_{\mathrm{eff}}/\mathrm{K})$"
        mag_label = r"$\log(L/L_{\odot})$"
        system = "HR"
    
    return color_index, magnitude, color_label, mag_label, system

def plot_single_3d_cmd(logs_path="LOGS"):
    """Create 3D CMD plot for a single MESA run with age as third axis."""
    
    history_path = os.path.join(logs_path, "history.data")
    if not os.path.exists(history_path):
        print(f"Error: Could not find history file at {history_path}")
        return False
        
    try:
        data = mr.MesaData(history_path)
        all_cols, filter_columns = read_header_columns(history_path)
        color_index, magnitude, color_label, mag_label, system = setup_cmd_params(data, filter_columns)
        
        if color_index is None:
            print("Error: Could not set up CMD parameters")
            return False
            
        if not hasattr(data, 'star_age'):
            print("Error: No age data available for 3D plot")
            return False
            
        # Create plots directory
        os.makedirs("plots", exist_ok=True)
        
        # 3D CMD with age as z-axis
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        age_myr = data.star_age / 1e6  # Convert to Myr
        
        ax.plot(color_index, magnitude, age_myr, 
                color='blue', linewidth=2, alpha=0.8)
        
        # Mark start and end points
        ax.scatter(color_index[0], magnitude[0], age_myr[0], 
                  color='green', marker='o', s=100, label='Start')
        ax.scatter(color_index[-1], magnitude[-1], age_myr[-1], 
                  color='red', marker='s', s=100, label='End')
        
        ax.set_xlabel(color_label, fontsize=12)
        ax.set_ylabel(mag_label, fontsize=12)
        ax.set_zlabel('Age (Myr)', fontsize=12)
        ax.invert_yaxis()
        
        if system == "HR":
            ax.invert_xaxis()
            
        ax.legend()
        ax.set_title(f"3D {system} CMD Evolution", fontsize=16)
        ax.view_init(elev=30, azim=-60)
        
        plt.savefig(f"plots/cmd_3d_{system.lower()}_age.png", dpi=300, bbox_inches='tight')
        print(f"Saved 3D CMD to plots/cmd_3d_{system.lower()}_age.png")
        plt.show()
        
        return True
        
    except Exception as e:
        print(f"Error creating 3D CMD plot: {e}")
        return False

def plot_batch_3d_cmd(runs_dir="../runs"):
    """Create 3D CMD plots for batch runs with age as third axis."""
    
    if not os.path.isdir(runs_dir):
        print(f"Error: Could not find {runs_dir} directory")
        return False
        
    # Find all run directories
    run_dirs = [d for d in os.listdir(runs_dir) 
                if os.path.isdir(os.path.join(runs_dir, d)) and d.startswith("inlist_")]
    
    if not run_dirs:
        print("No batch run directories found")
        return False
        
    # Collect data from all runs
    runs_data = {}
    run_params = {}
    
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
            
            # Check if we have age data
            if not hasattr(data, 'star_age'):
                print(f"Warning: No age data in {run_dir}")
                continue
                
            runs_data[run_dir] = data
            run_params[run_dir] = {
                'mass': mass,
                'metallicity': metallicity,
                'scheme': scheme,
                'fov': fov
            }
            
        except Exception as e:
            print(f"Error processing {run_dir}: {e}")
            continue
    
    if not runs_data:
        print("No valid data found in batch runs")
        return False
        
    # Determine CMD parameters from first valid run
    first_run = list(runs_data.keys())[0]
    first_data = runs_data[first_run]
    all_cols, filter_columns = read_header_columns(
        os.path.join(runs_dir, first_run, "LOGS", "history.data"))
    color_index, magnitude, color_label, mag_label, system = setup_cmd_params(first_data, filter_columns)
    
    if color_index is None:
        print("Error: Could not set up CMD parameters")
        return False
        
    print(f"Creating 3D batch CMD plots using {system} system")
    print(f"Found {len(runs_data)} models")
    
    # Set up colors and styles like in the reference script
    masses = sorted(set(param["mass"] for param in run_params.values()))
    mass_colors = plt.cm.brg(np.linspace(0, 1, len(masses)))
    mass_color_map = {mass: mass_colors[i] for i, mass in enumerate(masses)}
    
    # Create 3D plot
    fig = plt.figure(figsize=(18, 14))
    ax = fig.add_subplot(111, projection='3d')
    
    for run, data in runs_data.items():
        params = run_params[run]
        
        # Get CMD parameters for this run
        all_cols, filter_columns = read_header_columns(
            os.path.join(runs_dir, run, "LOGS", "history.data"))
        run_color_index, run_magnitude, _, _, run_system = setup_cmd_params(data, filter_columns)
        
        # Only plot if same system as primary
        if run_system != system:
            continue
            
        base_color = mass_color_map[params["mass"]]
        age_myr = data.star_age / 1e6
        
        # Alpha based on fov like in reference script
        fov_alpha = 0.3 + 0.7 * params["fov"] if params["scheme"] != "none" else 1.0
        
        # Line style based on scheme
        if params["scheme"] == "none":
            linestyle = '--'
        elif params["scheme"] == "exponential":
            linestyle = '-'
        else:
            linestyle = ':'
        
        ax.plot(run_color_index, run_magnitude, age_myr,
                color=base_color,
                linestyle=linestyle,
                linewidth=2,
                alpha=fov_alpha)
        
        # Mark start and end points
        ax.scatter(run_color_index[0], run_magnitude[0], age_myr[0],
                  color=base_color, marker='o', s=50, alpha=fov_alpha)
        ax.scatter(run_color_index[-1], run_magnitude[-1], age_myr[-1],
                  color=base_color, marker='s', s=50, alpha=fov_alpha)
    
    ax.set_xlabel(color_label, fontsize=14)
    ax.set_ylabel(mag_label, fontsize=14)
    ax.set_zlabel("Age (Myr)", fontsize=14)
    ax.invert_yaxis()
    
    if system == "HR":
        ax.invert_xaxis()
        
    ax.set_title(f"3D {system} CMD Evolution for All Stellar Models", fontsize=16)
    ax.view_init(elev=30, azim=-60)
    
    # Create simplified legend like in reference script
    # Mass legend
    for mass in masses:
        ax.plot([], [], [], '-', color=mass_color_map[mass], linewidth=3, label=f"{mass}M☉")
    
    # Scheme legend
    scheme_styles = {'none': '--', 'exponential': '-', 'step': ':'}
    for scheme, style in scheme_styles.items():
        if any(params['scheme'] == scheme for params in run_params.values()):
            ax.plot([], [], [], linestyle=style, color='gray', label=f"{scheme} scheme")
    
    if len(runs_data) <= 10:
        ax.legend(fontsize=9, loc='best')
    
    os.makedirs("plots", exist_ok=True)
    plt.tight_layout()
    plt.savefig(f"plots/batch_cmd_3d_{system.lower()}_age.png", dpi=300, bbox_inches='tight')
    print(f"Saved 3D batch CMD to plots/batch_cmd_3d_{system.lower()}_age.png")
    plt.show()
    
    return True

def main():
    """Main function to create 3D CMD plots with age axis."""
    
    # Check for single run
    single_run_found = False
    for logs_path in ["../../LOGS", "../LOGS", "LOGS"]:
        if os.path.isdir(logs_path):
            print(f"Found LOGS directory at {logs_path}. Creating 3D CMD plot for single run.")
            plot_single_3d_cmd(logs_path)
            single_run_found = True
            break
    
    # Check for batch runs
    batch_run_found = False
    for runs_path in ["../runs", "runs"]:
        if os.path.isdir(runs_path):
            print(f"\nFound batch runs directory at {runs_path}. Creating 3D batch CMD plot.")
            plot_batch_3d_cmd(runs_path)
            batch_run_found = True
            break
    
    if not single_run_found and not batch_run_found:
        print("Error: Could not find LOGS directory or batch runs directory.")
        print("Make sure you're running this script from the right location.")

if __name__ == "__main__":
    main()