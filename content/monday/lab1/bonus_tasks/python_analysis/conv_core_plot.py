#!/usr/bin/env python3
"""
conv_core_plot.py - Enhanced Convective Core Evolution Analysis with Custom Colors
Shows relationship between core evolution and photometric properties
"""

import os
import numpy as np
import matplotlib.pyplot as plt
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
    
    # Split the header line on whitespace
    all_cols = header_line.split()
    
    # Find the index of Flux_bol
    try:
        flux_index = all_cols.index("Flux_bol")
        filter_columns = all_cols[flux_index + 1:]
    except ValueError:
        print("Warning: Could not find 'Flux_bol' column in header")
        filter_columns = []
    
    return all_cols, filter_columns

def setup_color_params(md, filter_columns):
    """Set up color parameters based on available filters."""
    
    # Priority 1: GAIA colors (Gbp - Grp)
    if "Gbp" in filter_columns and "Grp" in filter_columns and "G" in filter_columns:
        color_index = md.Gbp - md.Grp
        magnitude = md.G
        color_label = "Gbp - Grp"
        mag_label = "G"
        system = "GAIA"
        
    # Priority 2: Johnson-Cousins (B-V)
    elif "B" in filter_columns and "V" in filter_columns:
        color_index = md.B - md.V
        magnitude = md.V
        color_label = "B - V"
        mag_label = "V"
        system = "Johnson"
        
    # Priority 3: 2MASS (J-K)
    elif "J" in filter_columns and "K" in filter_columns:
        color_index = md.J - md.K
        magnitude = md.K
        color_label = "J - K"
        mag_label = "K"
        system = "2MASS"
        
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
        
    else:
        # No colors available
        color_index = None
        magnitude = None
        color_label = None
        mag_label = None
        system = None
    
    return color_index, magnitude, color_label, mag_label, system

def plot_single_core_evolution(logs_path="LOGS"):
    """Create enhanced core mass evolution plots for a single MESA run"""
    
    # Check if the LOGS directory exists
    if not os.path.isdir(logs_path):
        print(f"Error: Could not find {logs_path} directory")
        return
        
    # Try to load the history file
    history_path = os.path.join(logs_path, "history.data")
    if not os.path.exists(history_path):
        print(f"Error: Could not find history.data in {logs_path}")
        return
        
    try:
        # Load the data
        data = mr.MesaData(history_path)
        
        # Get filter information
        all_cols, filter_columns = read_header_columns(history_path)
        color_index, magnitude, color_label, mag_label, system = setup_color_params(data, filter_columns)
        
        # Check if we have core mass information
        has_core_mass = False
        core_mass_data = None
        core_mass_attr_name = None
        
        for core_mass_attr in ['he_core_mass', 'mass_conv_core', 'conv_mx1_top']:
            if hasattr(data, core_mass_attr):
                core_mass_attr_name = core_mass_attr
                core_mass_data = getattr(data, core_mass_attr)
                has_core_mass = True
                break
                
        if not has_core_mass:
            print("Could not find core mass information in history data")
            return False
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle("Enhanced Core Evolution Analysis", fontsize=16)
        
        # Get age in Myr
        if hasattr(data, 'star_age'):
            age = data.star_age / 1e6  # Convert to Myr
            age_label = "Age (Myr)"
            age_data = age
        else:
            # Fall back to model number
            age_data = data.model_number
            age_label = "Model Number"
        
        # Plot 1: Core Mass vs Age/Model
        axes[0, 0].plot(age_data, core_mass_data, '-', color='blue', linewidth=2)
        axes[0, 0].set_xlabel(age_label, fontsize=12)
        axes[0, 0].set_ylabel(f"{core_mass_attr_name.replace('_', ' ').title()} ($M_\\odot$)", fontsize=12)
        axes[0, 0].set_title("Core Mass Evolution", fontsize=14)
        axes[0, 0].grid(alpha=0.3)
        
        # Plot 2: Core Mass Fraction vs Age/Model
        if hasattr(data, 'star_mass'):
            core_mass_fraction = core_mass_data / data.star_mass
            axes[0, 1].plot(age_data, core_mass_fraction, '-', color='red', linewidth=2)
            axes[0, 1].set_xlabel(age_label, fontsize=12)
            axes[0, 1].set_ylabel("Core Mass Fraction", fontsize=12)
            axes[0, 1].set_title("Core Mass Fraction Evolution", fontsize=14)
            axes[0, 1].grid(alpha=0.3)
        else:
            axes[0, 1].text(0.5, 0.5, "Star mass data\nnot available", 
                           ha='center', va='center', transform=axes[0, 1].transAxes)
            axes[0, 1].set_title("Core Mass Fraction (N/A)", fontsize=14)
        
        # Plot 3: Core Mass vs Color Index (if available)
        if color_index is not None:
            # Color by evolutionary phase if available
            if hasattr(data, 'center_h1'):
                scatter = axes[1, 0].scatter(core_mass_data, color_index, 
                                           c=data.center_h1, cmap='viridis', 
                                           s=30, alpha=0.7)
                plt.colorbar(scatter, ax=axes[1, 0], label='Central H fraction')
            else:
                axes[1, 0].scatter(core_mass_data, color_index, color='green', 
                                 s=30, alpha=0.7)
                axes[1, 0].plot(core_mass_data, color_index, '-', color='green', 
                               alpha=0.5, linewidth=1)
            
            axes[1, 0].set_xlabel(f"{core_mass_attr_name.replace('_', ' ').title()} ($M_\\odot$)", fontsize=12)
            axes[1, 0].set_ylabel(f"{color_label}", fontsize=12)
            axes[1, 0].set_title(f"Core Mass vs {system} Color", fontsize=14)
            axes[1, 0].grid(alpha=0.3)
        else:
            axes[1, 0].text(0.5, 0.5, f"No photometric\ncolors available", 
                           ha='center', va='center', transform=axes[1, 0].transAxes)
            axes[1, 0].set_title("Core Mass vs Color (N/A)", fontsize=14)
        
        # Plot 4: Core Mass vs Magnitude (if available)
        if magnitude is not None:
            # Color by evolutionary phase if available
            if hasattr(data, 'center_h1'):
                scatter = axes[1, 1].scatter(core_mass_data, magnitude, 
                                           c=data.center_h1, cmap='viridis', 
                                           s=30, alpha=0.7)
                plt.colorbar(scatter, ax=axes[1, 1], label='Central H fraction')
            else:
                axes[1, 1].scatter(core_mass_data, magnitude, color='purple', 
                                 s=30, alpha=0.7)
                axes[1, 1].plot(core_mass_data, magnitude, '-', color='purple', 
                               alpha=0.5, linewidth=1)
            
            axes[1, 1].set_xlabel(f"{core_mass_attr_name.replace('_', ' ').title()} ($M_\\odot$)", fontsize=12)
            axes[1, 1].set_ylabel(f"{mag_label}", fontsize=12)
            axes[1, 1].invert_yaxis()  # Brighter magnitudes at top
            axes[1, 1].set_title(f"Core Mass vs {system} Magnitude", fontsize=14)
            axes[1, 1].grid(alpha=0.3)
        else:
            axes[1, 1].text(0.5, 0.5, f"No photometric\nmagnitudes available", 
                           ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 1].set_title("Core Mass vs Magnitude (N/A)", fontsize=14)
        
        # Save and show
        os.makedirs("plots", exist_ok=True)
        plt.tight_layout()
        plt.savefig("plots/core_evolution_enhanced.png", dpi=300, bbox_inches='tight')
        print(f"Saved enhanced core evolution plot to plots/core_evolution_enhanced.png")
        plt.show()
        
        # Create separate traditional plots for compatibility
        # Core mass evolution
        plt.figure(figsize=(10, 6))
        plt.plot(age_data, core_mass_data, '-', color='blue', linewidth=2)
        plt.xlabel(age_label, fontsize=14)
        plt.ylabel(f"{core_mass_attr_name.replace('_', ' ').title()} ($M_\\odot$)", fontsize=14)
        plt.title("Core Mass Evolution", fontsize=16)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig("plots/core_mass_evolution.png", dpi=300)
        print(f"Saved core mass evolution to plots/core_mass_evolution.png")
        plt.show()
        
        # Core mass fraction evolution (if available)
        if hasattr(data, 'star_mass'):
            plt.figure(figsize=(10, 6))
            plt.plot(age_data, core_mass_fraction, '-', color='red', linewidth=2)
            plt.xlabel(age_label, fontsize=14)
            plt.ylabel("Core Mass Fraction", fontsize=14)
            plt.title("Core Mass Fraction Evolution", fontsize=16)
            plt.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig("plots/core_mass_fraction.png", dpi=300)
            print(f"Saved core mass fraction to plots/core_mass_fraction.png")
            plt.show()
            
        return True
        
    except Exception as e:
        print(f"Error creating core evolution plots: {e}")
        return False

def plot_batch_core_evolution():
    """Create core evolution plots for batch runs"""
    
    runs_dir = "../runs"
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
    colors_mass = {}
    linestyles_scheme = {}
    
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
            
            # Check for core mass data
            core_mass_data = None
            core_mass_attr_name = None
            for core_mass_attr in ['he_core_mass', 'mass_conv_core', 'conv_mx1_top']:
                if hasattr(data, core_mass_attr):
                    core_mass_attr_name = core_mass_attr
                    core_mass_data = getattr(data, core_mass_attr)
                    break
                    
            if core_mass_data is None:
                print(f"Warning: No core mass data in {run_dir}")
                continue
            
            # Get filter information
            all_cols, filter_columns = read_header_columns(history_path)
            color_index, magnitude, color_label, mag_label, system = setup_color_params(data, filter_columns)
            
            # Store data
            run_info = {
                'data': data,
                'mass': mass,
                'metallicity': metallicity,
                'scheme': scheme,
                'fov': fov,
                'core_mass_data': core_mass_data,
                'core_mass_attr_name': core_mass_attr_name,
                'color_index': color_index,
                'magnitude': magnitude,
                'color_label': color_label,
                'mag_label': mag_label,
                'system': system,
                'run_dir': run_dir
            }
            all_data.append(run_info)
            
            # Assign colors by mass
            if mass not in colors_mass:
                colors_mass[mass] = plt.cm.viridis(len(colors_mass) / 10.0)
                
            # Assign line styles by scheme
            if scheme not in linestyles_scheme:
                styles = ['-', '--', '-.', ':']
                linestyles_scheme[scheme] = styles[len(linestyles_scheme) % len(styles)]
                
        except Exception as e:
            print(f"Error processing {run_dir}: {e}")
            continue
    
    if not all_data:
        print("No valid data found in batch runs")
        return False
        
    print(f"Creating batch core evolution plots for {len(all_data)} models")
    
    # Create batch core mass evolution plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle("Batch Core Evolution Analysis", fontsize=16)
    
    for run_info in all_data:
        color = colors_mass[run_info['mass']]
        linestyle = linestyles_scheme[run_info['scheme']]
        
        label = f"M={run_info['mass']}M☉"
        if run_info['scheme'] != 'none':
            label += f", {run_info['scheme']}"
            if run_info['fov'] > 0:
                label += f" (f_ov={run_info['fov']})"
        else:
            label += ", no ovs"
        
        # Get age data
        if hasattr(run_info['data'], 'star_age'):
            age_data = run_info['data'].star_age / 1e6
            age_label = "Age (Myr)"
        else:
            age_data = run_info['data'].model_number
            age_label = "Model Number"
        
        # Plot 1: Core mass vs age
        axes[0, 0].plot(age_data, run_info['core_mass_data'], 
                       color=color, linestyle=linestyle, linewidth=2, 
                       label=label, alpha=0.8)
        
        # Plot 2: Core mass fraction vs age (if available)
        if hasattr(run_info['data'], 'star_mass'):
            core_mass_fraction = run_info['core_mass_data'] / run_info['data'].star_mass
            axes[0, 1].plot(age_data, core_mass_fraction, 
                           color=color, linestyle=linestyle, linewidth=2, 
                           alpha=0.8)
    
    # Format plots
    axes[0, 0].set_xlabel(age_label, fontsize=12)
    axes[0, 0].set_ylabel("Core Mass ($M_\\odot$)", fontsize=12)
    axes[0, 0].set_title("Core Mass Evolution", fontsize=14)
    axes[0, 0].grid(alpha=0.3)
    axes[0, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    axes[0, 1].set_xlabel(age_label, fontsize=12)
    axes[0, 1].set_ylabel("Core Mass Fraction", fontsize=12)
    axes[0, 1].set_title("Core Mass Fraction Evolution", fontsize=14)
    axes[0, 1].grid(alpha=0.3)
    
    # Plot 3 & 4: Color-core mass relationships for models with photometry
    models_with_colors = [r for r in all_data if r['color_index'] is not None]
    
    if models_with_colors:
        # Determine primary photometric system
        systems = [r['system'] for r in models_with_colors]
        primary_system = max(set(systems), key=systems.count)
        primary_models = [r for r in models_with_colors if r['system'] == primary_system]
        
        for run_info in primary_models:
            color = colors_mass[run_info['mass']]
            linestyle = linestyles_scheme[run_info['scheme']]
            
            # Plot 3: Core mass vs color index
            axes[1, 0].plot(run_info['core_mass_data'], run_info['color_index'], 
                           color=color, linestyle=linestyle, linewidth=2, alpha=0.8)
            
            # Plot 4: Core mass vs magnitude
            if run_info['magnitude'] is not None:
                axes[1, 1].plot(run_info['core_mass_data'], run_info['magnitude'], 
                               color=color, linestyle=linestyle, linewidth=2, alpha=0.8)
        
        axes[1, 0].set_xlabel("Core Mass ($M_\\odot$)", fontsize=12)
        axes[1, 0].set_ylabel(f"{primary_models[0]['color_label']}", fontsize=12)
        axes[1, 0].set_title(f"Core Mass vs {primary_system} Color", fontsize=14)
        axes[1, 0].grid(alpha=0.3)
        
        axes[1, 1].set_xlabel("Core Mass ($M_\\odot$)", fontsize=12)
        axes[1, 1].set_ylabel(f"{primary_models[0]['mag_label']}", fontsize=12)
        axes[1, 1].invert_yaxis()
        axes[1, 1].set_title(f"Core Mass vs {primary_system} Magnitude", fontsize=14)
        axes[1, 1].grid(alpha=0.3)
    else:
        axes[1, 0].text(0.5, 0.5, "No photometric\ncolors available", 
                       ha='center', va='center', transform=axes[1, 0].transAxes)
        axes[1, 1].text(0.5, 0.5, "No photometric\nmagnitudes available", 
                       ha='center', va='center', transform=axes[1, 1].transAxes)
    
    os.makedirs("plots", exist_ok=True)
    plt.tight_layout()
    plt.savefig("plots/core_evolution_batch.png", dpi=300, bbox_inches='tight')
    print(f"Saved batch core evolution to plots/core_evolution_batch.png")
    plt.show()
    
    # Create separate traditional plots
    plt.figure(figsize=(12, 8))
    for run_info in all_data:
        color = colors_mass[run_info['mass']]
        linestyle = linestyles_scheme[run_info['scheme']]
        
        label = f"M={run_info['mass']}M☉, {run_info['scheme']}"
        if run_info['fov'] > 0:
            label += f" (f_ov={run_info['fov']})"
        
        # Use log age for better visualization
        if hasattr(run_info['data'], 'star_age'):
            log_age = np.log10(run_info['data'].star_age / 1e6)  # log(age in Myr)
            plt.plot(log_age, run_info['core_mass_data'], 
                    color=color, linestyle=linestyle, linewidth=2, 
                    label=label, alpha=0.8)
    
    plt.xlabel("log Age (Myr)", fontsize=14)
    plt.ylabel("Core Mass ($M_\\odot$)", fontsize=14)
    plt.title("Core Mass vs Log Age (All Models)", fontsize=16)
    plt.grid(alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("plots/core_mass_vs_log_age.png", dpi=300, bbox_inches='tight')
    print(f"Saved core mass vs log age to plots/core_mass_vs_log_age.png")
    plt.show()
    
    return True

def main():
    """Main function to determine whether to plot single or batch core evolution"""
    
    # First, check if we're in a directory with a single MESA run
    if os.path.isdir("../../LOGS"):
        print("Found LOGS directory. Creating core evolution plots for single run.")
        plot_single_core_evolution("../../LOGS")
    elif os.path.isdir("../LOGS"):
        print("Found LOGS directory. Creating core evolution plots for single run.")
        plot_single_core_evolution("../LOGS")
    elif os.path.isdir("LOGS"):
        print("Found LOGS directory. Creating core evolution plots for single run.")
        plot_single_core_evolution("LOGS")

    # Check for batch runs
    if os.path.isdir("../runs"):
        print("Found batch runs directory. Creating batch core evolution plots.")
        plot_batch_core_evolution()
    else:
        print("No batch runs directory found.")
        
    if not (os.path.isdir("../../LOGS") or os.path.isdir("../LOGS") or 
            os.path.isdir("LOGS") or os.path.isdir("../runs")):
        print("Error: Could not find LOGS directory or batch runs directory.")
        print("Make sure you're running this script from the right location.")

if __name__ == "__main__":
    main()