#!/usr/bin/env python3
"""
cmd_plot.py - Color-Magnitude Diagram Generator for MESA with Custom Colors
Replaces hr_plot.py to emphasize GAIA and custom photometric colors
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

def setup_cmd_params(md, filter_columns):
    """Set up parameters for CMD based on available filters."""
    
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

def plot_single_cmd(logs_path="LOGS"):
    """Create Color-Magnitude Diagram for a single MESA run with evolutionary phase information"""
    
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
        
        # Set up CMD parameters
        color_index, magnitude, color_label, mag_label, system = setup_cmd_params(data, filter_columns)
        
        # Create the plot
        plt.figure(figsize=(10, 8))
        
        # Define color mapping based on central hydrogen abundance if available
        if hasattr(data, 'center_h1'):
            # Create a color map based on central hydrogen abundance
            norm = plt.Normalize(0, max(data.center_h1))
            cmap = plt.cm.viridis
            
            # Plot with color representing evolutionary state
            sc = plt.scatter(color_index, magnitude, 
                        c=data.center_h1, cmap=cmap, norm=norm,
                        s=30, alpha=0.8)
            
            # Add a line connecting points
            plt.plot(color_index, magnitude, '-', color='gray', alpha=0.5, linewidth=1)
            
            # Add a colorbar
            cbar = plt.colorbar(sc)
            cbar.set_label('Central H mass fraction')
            
            # Mark evolutionary points
            # ZAMS (when H burning is well established)
            zams_h1 = 0.7  # Typical value, adjust if needed
            # TAMS (when central H is depleted to stopping criterion)
            tams_h1 = 0.001
            
            # Find indices closest to ZAMS and TAMS
            if min(data.center_h1) < 0.1 and max(data.center_h1) > 0.6:  # Make sure we have both phases
                zams_idx = np.abs(data.center_h1 - zams_h1).argmin()
                tams_idx = np.abs(data.center_h1 - tams_h1).argmin()
                
                # Mark ZAMS with a star
                plt.scatter(color_index[zams_idx], magnitude[zams_idx], 
                          marker='*', s=200, edgecolor='black', facecolor='navy',
                          label='ZAMS')
                
                # Mark TAMS with a square
                plt.scatter(color_index[tams_idx], magnitude[tams_idx], 
                          marker='s', s=100, edgecolor='black', facecolor='gold',
                          label='TAMS')
            else:
                # If we don't have the full evolution, just mark start and end
                plt.scatter(color_index[0], magnitude[0], color='green', s=100, 
                          marker='o', label='Start')
                plt.scatter(color_index[-1], magnitude[-1], color='red', s=100, 
                          marker='s', label='End')
        else:
            # Fallback to original coloring if no center_h1
            plt.plot(color_index, magnitude, '-', color='blue', linewidth=2)
            
            # Add points for start and end of evolution
            plt.scatter(color_index[0], magnitude[0], color='green', s=100, 
                      marker='o', label='Start')
            plt.scatter(color_index[-1], magnitude[-1], color='red', s=100, 
                      marker='s', label='End')
        
        # Set up the plot
        plt.xlabel(f"{color_label}", fontsize=14)
        plt.ylabel(f"{mag_label}", fontsize=14)
        
        # Invert magnitude axis (brighter stars at top)
        plt.gca().invert_yaxis()
        
        # For HR diagram, also invert x-axis
        if system == "HR":
            plt.gca().invert_xaxis()
            
        plt.grid(alpha=0.3)
        plt.legend(loc='best')
        
        # Add title with system information
        plt.title(f"{system} Color-Magnitude Diagram", fontsize=16)
        
        # Save and show
        os.makedirs("plots", exist_ok=True)
        plt.tight_layout()
        plt.savefig("plots/cmd_diagram.png", dpi=300)
        print(f"Saved CMD to plots/cmd_diagram.png")
        plt.show()
        
        # Make a 3D age plot if age info exists
        if hasattr(data, 'star_age'):
            fig = plt.figure(figsize=(12, 10))
            ax = fig.add_subplot(111, projection='3d')
            
            age_myr = data.star_age / 1e6  # Convert to Myr
            
            # Add color based on evolutionary phase if available
            if hasattr(data, 'center_h1'):
                points = ax.scatter(color_index, magnitude, age_myr,
                                   c=data.center_h1, cmap=cmap, norm=norm,
                                   s=30, alpha=0.8)
                
                # Connect points
                ax.plot(color_index, magnitude, age_myr, color='gray', alpha=0.5, linewidth=1)
                
                # Add colorbar
                cbar = fig.colorbar(points, ax=ax, pad=0.1)
                cbar.set_label('Central H mass fraction')
                
                # Mark key evolutionary points if we have the full evolution
                if min(data.center_h1) < 0.1 and max(data.center_h1) > 0.6:
                    ax.scatter(color_index[zams_idx], magnitude[zams_idx], age_myr[zams_idx],
                              marker='*', s=200, edgecolor='black', facecolor='navy',
                              label='ZAMS')
                    ax.scatter(color_index[tams_idx], magnitude[tams_idx], age_myr[tams_idx],
                              marker='s', s=150, edgecolor='black', facecolor='gold',
                              label='TAMS')
                else:
                    ax.scatter(color_index[0], magnitude[0], age_myr[0], 
                             color='green', marker='o', s=100, label='Start')
                    ax.scatter(color_index[-1], magnitude[-1], age_myr[-1], 
                             color='red', marker='s', s=100, label='End')
            else:
                ax.plot(color_index, magnitude, age_myr, color='blue', linewidth=2)
                ax.scatter(color_index[0], magnitude[0], age_myr[0], 
                          color='green', marker='o', s=100, label='Start')
                ax.scatter(color_index[-1], magnitude[-1], age_myr[-1], 
                          color='red', marker='s', s=100, label='End')
            
            ax.set_xlabel(f"{color_label}", fontsize=14)
            ax.set_ylabel(f"{mag_label}", fontsize=14)
            ax.set_zlabel("Age (Myr)", fontsize=14)
            ax.invert_yaxis()
            
            # For HR diagram, also invert x-axis
            if system == "HR":
                ax.invert_xaxis()
                
            ax.legend()
            ax.set_title(f"3D {system} CMD Evolution", fontsize=16)
            
            plt.savefig("plots/cmd_diagram_3d.png", dpi=300)
            print(f"Saved 3D CMD to plots/cmd_diagram_3d.png")
            plt.show()
            
            # Create rotating animation
            try:
                from matplotlib.animation import FuncAnimation
                
                def animate(frame):
                    ax.view_init(elev=20, azim=frame*4)
                    return []
                
                anim = FuncAnimation(fig, animate, frames=90, interval=100, blit=False)
                anim.save("plots/cmd_diagram_3d_rotation.gif", writer='pillow', fps=10)
                print(f"Saved rotating 3D CMD to plots/cmd_diagram_3d_rotation.gif")
            except ImportError:
                print("Could not create animation (pillow not available)")
            except Exception as e:
                print(f"Could not create animation: {e}")
            
        return True
        
    except Exception as e:
        print(f"Error creating CMD: {e}")
        return False

def plot_batch_cmds():
    """Create CMD plots for batch runs"""
    
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
            
            # Get filter information
            all_cols, filter_columns = read_header_columns(history_path)
            
            # Set up CMD parameters (use same logic for all)
            color_index, magnitude, color_label, mag_label, system = setup_cmd_params(data, filter_columns)
            
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
        
    # Determine the photometric system to use (use the most common one)
    systems = [d['system'] for d in all_data]
    primary_system = max(set(systems), key=systems.count)
    primary_data = [d for d in all_data if d['system'] == primary_system]
    
    print(f"Creating batch CMD plots using {primary_system} system")
    print(f"Found {len(primary_data)} models with {primary_system} photometry")
    
    # Create batch CMD plot
    plt.figure(figsize=(12, 10))
    
    for run_info in primary_data:
        color = colors_mass[run_info['mass']]
        linestyle = linestyles_scheme[run_info['scheme']]
        
        label = f"M={run_info['mass']}M☉, {run_info['scheme']}"
        if run_info['fov'] > 0:
            label += f" (f_ov={run_info['fov']})"
            
        plt.plot(run_info['color_index'], run_info['magnitude'], 
                color=color, linestyle=linestyle, linewidth=2, 
                label=label, alpha=0.8)
        
        # Mark start and end points
        plt.scatter(run_info['color_index'][0], run_info['magnitude'][0], 
                   color=color, marker='o', s=50, alpha=0.7)
        plt.scatter(run_info['color_index'][-1], run_info['magnitude'][-1], 
                   color=color, marker='s', s=50, alpha=0.7)
    
    plt.xlabel(f"{primary_data[0]['color_label']}", fontsize=14)
    plt.ylabel(f"{primary_data[0]['mag_label']}", fontsize=14)
    plt.gca().invert_yaxis()
    
    if primary_system == "HR":
        plt.gca().invert_xaxis()
        
    plt.grid(alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.title(f"Batch {primary_system} Color-Magnitude Diagrams", fontsize=16)
    
    os.makedirs("plots", exist_ok=True)
    plt.tight_layout()
    plt.savefig("plots/all_cmd_diagrams.png", dpi=300, bbox_inches='tight')
    print(f"Saved batch CMD to plots/all_cmd_diagrams.png")
    plt.show()
    
    # Create 3D batch plot
    if all(hasattr(d['data'], 'star_age') for d in primary_data):
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        for run_info in primary_data:
            color = colors_mass[run_info['mass']]
            age_myr = run_info['data'].star_age / 1e6
            
            ax.plot(run_info['color_index'], run_info['magnitude'], age_myr,
                   color=color, linewidth=2, alpha=0.8,
                   label=f"M={run_info['mass']}M☉")
        
        ax.set_xlabel(f"{primary_data[0]['color_label']}", fontsize=14)
        ax.set_ylabel(f"{primary_data[0]['mag_label']}", fontsize=14)
        ax.set_zlabel("Age (Myr)", fontsize=14)
        ax.invert_yaxis()
        
        if primary_system == "HR":
            ax.invert_xaxis()
            
        ax.legend()
        ax.set_title(f"3D Batch {primary_system} CMD Evolution", fontsize=16)
        
        plt.savefig("plots/all_cmd_diagrams_3d.png", dpi=300, bbox_inches='tight')
        print(f"Saved 3D batch CMD to plots/all_cmd_diagrams_3d.png")
        plt.show()
    
    return True

def main():
    """Main function to determine whether to plot single or batch CMDs"""
    
    # First, check if we're in a directory with a single MESA run
    if os.path.isdir("../../LOGS"):
        print("Found LOGS directory. Creating CMD for single run.")
        plot_single_cmd("../../LOGS")
    elif os.path.isdir("../LOGS"):
        print("Found LOGS directory. Creating CMD for single run.")
        plot_single_cmd("../LOGS")
    elif os.path.isdir("LOGS"):
        print("Found LOGS directory. Creating CMD for single run.")
        plot_single_cmd("LOGS")

    # Check for batch runs
    if os.path.isdir("../runs"):
        print("Found batch runs directory. Creating batch CMD plots.")
        plot_batch_cmds()
    else:
        print("No batch runs directory found.")
        
    if not (os.path.isdir("../../LOGS") or os.path.isdir("../LOGS") or 
            os.path.isdir("LOGS") or os.path.isdir("../runs")):
        print("Error: Could not find LOGS directory or batch runs directory.")
        print("Make sure you're running this script from the right location.")

if __name__ == "__main__":
    main()