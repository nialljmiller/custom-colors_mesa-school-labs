#!/usr/bin/env python3
"""
composition_plot.py - Enhanced Composition Analysis with Custom Colors
Shows relationship between stellar composition and photometric properties
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

def plot_single_composition_analysis(logs_path="LOGS"):
    """Create enhanced composition analysis plots for a single MESA run"""
    
    # Check if the LOGS directory exists
    if not os.path.isdir(logs_path):
        print(f"Error: Could not find {logs_path} directory")
        return
        
    # Try to find the latest profile file
    profile_files = sorted(glob.glob(os.path.join(logs_path, "profile*.data")))
    
    if not profile_files:
        print(f"Error: Could not find any profile files in {logs_path}")
        return
        
    # Also try to load history file for color evolution
    history_path = os.path.join(logs_path, "history.data")
    history_data = None
    if os.path.exists(history_path):
        try:
            history_data = mr.MesaData(history_path)
            all_cols, filter_columns = read_header_columns(history_path)
            color_index, magnitude, color_label, mag_label, system = setup_color_params(history_data, filter_columns)
        except Exception as e:
            print(f"Warning: Could not load history data: {e}")
            history_data = None
        
    try:
        # Load the last profile
        latest_profile = mr.MesaData(profile_files[-1])
        
        # Create enhanced composition analysis
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle("Enhanced Composition Analysis", fontsize=16)
        
        # Plot 1: Traditional composition profile
        if hasattr(latest_profile, 'mass') and hasattr(latest_profile, 'x_mass_fraction_H'):
            mass_coord = latest_profile.mass / latest_profile.star_mass
            
            axes[0, 0].plot(mass_coord, latest_profile.x_mass_fraction_H, '-', 
                           color='blue', linewidth=2, label='Hydrogen')
            
            # Add helium if available
            if hasattr(latest_profile, 'y_mass_fraction_He'):
                axes[0, 0].plot(mass_coord, latest_profile.y_mass_fraction_He, '-', 
                               color='red', linewidth=2, label='Helium')
            
            # Add metals if available
            if hasattr(latest_profile, 'z_mass_fraction_metals'):
                axes[0, 0].plot(mass_coord, latest_profile.z_mass_fraction_metals, '-', 
                               color='green', linewidth=2, label='Metals')
            
            axes[0, 0].set_xlabel("Mass Coordinate (m/M$_{\\rm star}$)", fontsize=12)
            axes[0, 0].set_ylabel("Mass Fraction", fontsize=12)
            axes[0, 0].set_title("Composition Profile (Final Model)", fontsize=14)
            axes[0, 0].legend()
            axes[0, 0].grid(alpha=0.3)
            axes[0, 0].set_xlim(0, 1)
            axes[0, 0].set_ylim(0, 1)
        else:
            axes[0, 0].text(0.5, 0.5, "Composition data\nnot available", 
                           ha='center', va='center', transform=axes[0, 0].transAxes)
        
        # Plot 2: Surface composition evolution vs time (if history available)
        if history_data is not None:
            if hasattr(history_data, 'star_age') and hasattr(history_data, 'surface_h1'):
                age_myr = history_data.star_age / 1e6
                
                axes[0, 1].plot(age_myr, history_data.surface_h1, '-', 
                               color='blue', linewidth=2, label='Surface H')
                
                if hasattr(history_data, 'surface_he4'):
                    axes[0, 1].plot(age_myr, history_data.surface_he4, '-', 
                                   color='red', linewidth=2, label='Surface He')
                
                if hasattr(history_data, 'surface_z'):
                    axes[0, 1].plot(age_myr, history_data.surface_z, '-', 
                                   color='green', linewidth=2, label='Surface Z')
                
                axes[0, 1].set_xlabel("Age (Myr)", fontsize=12)
                axes[0, 1].set_ylabel("Surface Mass Fraction", fontsize=12)
                axes[0, 1].set_title("Surface Composition Evolution", fontsize=14)
                axes[0, 1].legend()
                axes[0, 1].grid(alpha=0.3)
            else:
                axes[0, 1].text(0.5, 0.5, "Surface composition\nevolution not available", 
                               ha='center', va='center', transform=axes[0, 1].transAxes)
        else:
            axes[0, 1].text(0.5, 0.5, "History data\nnot available", 
                           ha='center', va='center', transform=axes[0, 1].transAxes)
        
        # Plot 3: Color evolution vs composition (if color data available)
        if history_data is not None and color_index is not None:
            if hasattr(history_data, 'surface_h1'):
                # Color by evolutionary phase if available
                if hasattr(history_data, 'center_h1'):
                    scatter = axes[1, 0].scatter(history_data.surface_h1, color_index,
                                               c=history_data.center_h1, cmap='viridis',
                                               s=30, alpha=0.7)
                    plt.colorbar(scatter, ax=axes[1, 0], label='Central H fraction')
                else:
                    axes[1, 0].scatter(history_data.surface_h1, color_index, 
                                     color='purple', s=30, alpha=0.7)
                    axes[1, 0].plot(history_data.surface_h1, color_index, '-', 
                                   color='purple', alpha=0.5, linewidth=1)
                
                axes[1, 0].set_xlabel("Surface H Mass Fraction", fontsize=12)
                axes[1, 0].set_ylabel(f"{color_label}", fontsize=12)
                axes[1, 0].set_title(f"Surface H vs {system} Color", fontsize=14)
                axes[1, 0].grid(alpha=0.3)
            else:
                axes[1, 0].text(0.5, 0.5, "Surface composition\ndata not available", 
                               ha='center', va='center', transform=axes[1, 0].transAxes)
        else:
            axes[1, 0].text(0.5, 0.5, "Color or composition\ndata not available", 
                           ha='center', va='center', transform=axes[1, 0].transAxes)
        
        # Plot 4: Metallicity evolution vs magnitude (if available)
        if history_data is not None and magnitude is not None:
            if hasattr(history_data, 'surface_z'):
                # Color by evolutionary phase if available
                if hasattr(history_data, 'center_h1'):
                    scatter = axes[1, 1].scatter(history_data.surface_z, magnitude,
                                               c=history_data.center_h1, cmap='viridis',
                                               s=30, alpha=0.7)
                    plt.colorbar(scatter, ax=axes[1, 1], label='Central H fraction')
                else:
                    axes[1, 1].scatter(history_data.surface_z, magnitude, 
                                     color='orange', s=30, alpha=0.7)
                    axes[1, 1].plot(history_data.surface_z, magnitude, '-', 
                                   color='orange', alpha=0.5, linewidth=1)
                
                axes[1, 1].set_xlabel("Surface Metallicity (Z)", fontsize=12)
                axes[1, 1].set_ylabel(f"{mag_label}", fontsize=12)
                axes[1, 1].invert_yaxis()  # Brighter magnitudes at top
                axes[1, 1].set_title(f"Surface Z vs {system} Magnitude", fontsize=14)
                axes[1, 1].grid(alpha=0.3)
            else:
                axes[1, 1].text(0.5, 0.5, "Surface metallicity\ndata not available", 
                               ha='center', va='center', transform=axes[1, 1].transAxes)
        else:
            axes[1, 1].text(0.5, 0.5, "Magnitude or metallicity\ndata not available", 
                           ha='center', va='center', transform=axes[1, 1].transAxes)
        
        # Save and show
        os.makedirs("plots", exist_ok=True)
        plt.tight_layout()
        plt.savefig("plots/composition_analysis_enhanced.png", dpi=300, bbox_inches='tight')
        print(f"Saved enhanced composition analysis to plots/composition_analysis_enhanced.png")
        plt.show()
        
        # Create traditional composition profile plot for compatibility
        if hasattr(latest_profile, 'mass') and hasattr(latest_profile, 'x_mass_fraction_H'):
            plt.figure(figsize=(10, 8))
            mass_coord = latest_profile.mass / latest_profile.star_mass
            
            plt.plot(mass_coord, latest_profile.x_mass_fraction_H, '-', 
                    color='blue', linewidth=2, label='Hydrogen')
            
            if hasattr(latest_profile, 'y_mass_fraction_He'):
                plt.plot(mass_coord, latest_profile.y_mass_fraction_He, '-', 
                        color='red', linewidth=2, label='Helium')
            
            if hasattr(latest_profile, 'z_mass_fraction_metals'):
                plt.plot(mass_coord, latest_profile.z_mass_fraction_metals, '-', 
                        color='green', linewidth=2, label='Metals')
            
            plt.xlabel("Mass Coordinate (m/M$_{\\rm star}$)", fontsize=14)
            plt.ylabel("Mass Fraction", fontsize=14)
            plt.title("Composition Profile at Final Model", fontsize=16)
            plt.legend(loc='best')
            plt.grid(alpha=0.3)
            plt.xlim(0, 1)
            plt.ylim(0, 1)
            
            plt.tight_layout()
            plt.savefig("plots/composition_profile.png", dpi=300)
            print(f"Saved composition profile to plots/composition_profile.png")
            plt.show()
        
        return True
        
    except Exception as e:
        print(f"Error creating composition analysis plots: {e}")
        return False

def plot_batch_composition_analysis():
    """Create composition analysis plots for batch runs"""
    
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
        profile_files = sorted(glob.glob(os.path.join(runs_dir, run_dir, "LOGS", "profile*.data")))
        
        if not os.path.exists(history_path) or not profile_files:
            print(f"Warning: Missing files in {run_dir}")
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
            history_data = mr.MesaData(history_path)
            profile_data = mr.MesaData(profile_files[-1])
            
            # Get filter information
            all_cols, filter_columns = read_header_columns(history_path)
            color_index, magnitude, color_label, mag_label, system = setup_color_params(history_data, filter_columns)
            
            # Store data
            run_info = {
                'history_data': history_data,
                'profile_data': profile_data,
                'mass': mass,
                'metallicity': metallicity,
                'scheme': scheme,
                'fov': fov,
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
        
    print(f"Creating batch composition analysis for {len(all_data)} models")
    
    # Create batch composition comparison
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle("Batch Composition Analysis", fontsize=16)
    
    # Plot 1: Final hydrogen profiles
    for run_info in all_data:
        color = colors_mass[run_info['mass']]
        linestyle = linestyles_scheme[run_info['scheme']]
        
        label = f"M={run_info['mass']}M☉"
        if run_info['scheme'] != 'none':
            label += f", {run_info['scheme']}"
        else:
            label += ", no ovs"
        
        profile = run_info['profile_data']
        if hasattr(profile, 'mass') and hasattr(profile, 'x_mass_fraction_H'):
            mass_coord = profile.mass / profile.star_mass
            axes[0, 0].plot(mass_coord, profile.x_mass_fraction_H,
                           color=color, linestyle=linestyle, linewidth=2,
                           label=label, alpha=0.8)
    
    axes[0, 0].set_xlabel("Mass Coordinate (m/M$_{\\rm star}$)", fontsize=12)
    axes[0, 0].set_ylabel("Hydrogen Mass Fraction", fontsize=12)
    axes[0, 0].set_title("Final Hydrogen Profiles", fontsize=14)
    axes[0, 0].grid(alpha=0.3)
    axes[0, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    axes[0, 0].set_xlim(0, 1)
    axes[0, 0].set_ylim(0, 1)
    
    # Plot 2: Surface composition evolution
    for run_info in all_data:
        color = colors_mass[run_info['mass']]
        linestyle = linestyles_scheme[run_info['scheme']]
        
        history = run_info['history_data']
        if hasattr(history, 'star_age') and hasattr(history, 'surface_h1'):
            age_myr = history.star_age / 1e6
            axes[0, 1].plot(age_myr, history.surface_h1,
                           color=color, linestyle=linestyle, linewidth=2, alpha=0.8)
    
    axes[0, 1].set_xlabel("Age (Myr)", fontsize=12)
    axes[0, 1].set_ylabel("Surface H Mass Fraction", fontsize=12)
    axes[0, 1].set_title("Surface Hydrogen Evolution", fontsize=14)
    axes[0, 1].grid(alpha=0.3)
    
    # Plot 3 & 4: Color-composition relationships for models with photometry
    models_with_colors = [r for r in all_data if r['color_index'] is not None]
    
    if models_with_colors:
        # Determine primary photometric system
        systems = [r['system'] for r in models_with_colors]
        primary_system = max(set(systems), key=systems.count)
        primary_models = [r for r in models_with_colors if r['system'] == primary_system]
        
        # Plot 3: Surface H vs Color
        for run_info in primary_models:
            color = colors_mass[run_info['mass']]
            linestyle = linestyles_scheme[run_info['scheme']]
            
            history = run_info['history_data']
            if hasattr(history, 'surface_h1'):
                axes[1, 0].plot(history.surface_h1, run_info['color_index'],
                               color=color, linestyle=linestyle, linewidth=2, alpha=0.8)
        
        axes[1, 0].set_xlabel("Surface H Mass Fraction", fontsize=12)
        axes[1, 0].set_ylabel(f"{primary_models[0]['color_label']}", fontsize=12)
        axes[1, 0].set_title(f"Surface H vs {primary_system} Color", fontsize=14)
        axes[1, 0].grid(alpha=0.3)
        
        # Plot 4: Surface Z vs Magnitude
        for run_info in primary_models:
            color = colors_mass[run_info['mass']]
            linestyle = linestyles_scheme[run_info['scheme']]
            
            history = run_info['history_data']
            if hasattr(history, 'surface_z') and run_info['magnitude'] is not None:
                axes[1, 1].plot(history.surface_z, run_info['magnitude'],
                               color=color, linestyle=linestyle, linewidth=2, alpha=0.8)
        
        axes[1, 1].set_xlabel("Surface Metallicity (Z)", fontsize=12)
        axes[1, 1].set_ylabel(f"{primary_models[0]['mag_label']}", fontsize=12)
        axes[1, 1].invert_yaxis()
        axes[1, 1].set_title(f"Surface Z vs {primary_system} Magnitude", fontsize=14)
        axes[1, 1].grid(alpha=0.3)
    else:
        axes[1, 0].text(0.5, 0.5, "No photometric\ncolors available", 
                       ha='center', va='center', transform=axes[1, 0].transAxes)
        axes[1, 1].text(0.5, 0.5, "No photometric\nmagnitudes available", 
                       ha='center', va='center', transform=axes[1, 1].transAxes)
    
    os.makedirs("plots", exist_ok=True)
    plt.tight_layout()
    plt.savefig("plots/composition_analysis_batch.png", dpi=300, bbox_inches='tight')
    print(f"Saved batch composition analysis to plots/composition_analysis_batch.png")
    plt.show()
    
    # Create separate hydrogen profiles plot
    plt.figure(figsize=(12, 8))
    for run_info in all_data:
        color = colors_mass[run_info['mass']]
        linestyle = linestyles_scheme[run_info['scheme']]
        
        label = f"M={run_info['mass']}M☉, {run_info['scheme']}"
        if run_info['fov'] > 0:
            label += f" (f_ov={run_info['fov']})"
        
        profile = run_info['profile_data']
        if hasattr(profile, 'mass') and hasattr(profile, 'x_mass_fraction_H'):
            mass_coord = profile.mass / profile.star_mass
            plt.plot(mass_coord, profile.x_mass_fraction_H,
                    color=color, linestyle=linestyle, linewidth=2,
                    label=label, alpha=0.8)
    
    plt.xlabel("Mass Coordinate (m/M$_{\\rm star}$)", fontsize=14)
    plt.ylabel("Hydrogen Mass Fraction", fontsize=14)
    plt.title("Final Hydrogen Profiles (All Models)", fontsize=16)
    plt.grid(alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig("plots/hydrogen_profiles_all_models.png", dpi=300, bbox_inches='tight')
    print(f"Saved hydrogen profiles to plots/hydrogen_profiles_all_models.png")
    plt.show()
    
    return True

def main():
    """Main function to determine whether to plot single or batch composition analysis"""
    
    # First, check if we're in a directory with a single MESA run
    if os.path.isdir("../../LOGS"):
        print("Found LOGS directory. Creating composition analysis for single run.")
        plot_single_composition_analysis("../../LOGS")
    elif os.path.isdir("../LOGS"):
        print("Found LOGS directory. Creating composition analysis for single run.")
        plot_single_composition_analysis("../LOGS")
    elif os.path.isdir("LOGS"):
        print("Found LOGS directory. Creating composition analysis for single run.")
        plot_single_composition_analysis("LOGS")

    # Check for batch runs
    if os.path.isdir("../runs"):
        print("Found batch runs directory. Creating batch composition analysis.")
        plot_batch_composition_analysis()
    else:
        print("No batch runs directory found.")
        
    if not (os.path.isdir("../../LOGS") or os.path.isdir("../LOGS") or 
            os.path.isdir("LOGS") or os.path.isdir("../runs")):
        print("Error: Could not find LOGS directory or batch runs directory.")
        print("Make sure you're running this script from the right location.")

if __name__ == "__main__":
    main()