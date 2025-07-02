#!/usr/bin/env python3
"""
color_color_plots.py - Multi-System Color-Color Diagrams for MESA Custom Colors
Creates comprehensive color-color diagrams showcasing different photometric systems
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import mesa_reader as mr
import matplotlib.gridspec as gridspec
import glob
from matplotlib.patches import Rectangle
from matplotlib.collections import LineCollection

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

def setup_all_photometric_systems(filter_columns):
    """Set up all available photometric systems for comprehensive analysis."""
    systems = {}
    
    # GAIA system
    gaia_filters = ['Gbp', 'G', 'Grp']
    if all(f in filter_columns for f in gaia_filters):
        systems['GAIA'] = {
            'filters': gaia_filters,
            'color_combinations': [
                ('Gbp-Grp', 'Gbp-G'),  # Standard GAIA color-color
                ('Gbp-G', 'G-Grp'),    # Alternative GAIA colors
            ],
            'description': 'European Space Agency Gaia mission'
        }
    
    # Johnson-Cousins system
    johnson_filters = [f for f in ['U', 'B', 'V', 'R', 'I'] if f in filter_columns]
    if len(johnson_filters) >= 3:
        systems['Johnson'] = {
            'filters': johnson_filters,
            'color_combinations': [],
            'description': 'Johnson-Cousins photometric system'
        }
        
        # Add all possible color combinations
        if 'U' in johnson_filters and 'B' in johnson_filters and 'V' in johnson_filters:
            systems['Johnson']['color_combinations'].append(('U-B', 'B-V'))
        if 'B' in johnson_filters and 'V' in johnson_filters and 'R' in johnson_filters:
            systems['Johnson']['color_combinations'].append(('B-V', 'V-R'))
        if 'V' in johnson_filters and 'R' in johnson_filters and 'I' in johnson_filters:
            systems['Johnson']['color_combinations'].append(('V-R', 'R-I'))
        if 'B' in johnson_filters and 'V' in johnson_filters and 'I' in johnson_filters:
            systems['Johnson']['color_combinations'].append(('B-V', 'V-I'))
    
    # 2MASS system  
    twomass_filters = [f for f in ['J', 'H', 'K'] if f in filter_columns]
    if len(twomass_filters) >= 3:
        systems['2MASS'] = {
            'filters': twomass_filters,
            'color_combinations': [
                ('J-H', 'H-K'),  # Standard 2MASS color-color
                ('J-K', 'H-K'),  # Alternative combination
            ],
            'description': 'Two Micron All Sky Survey'
        }
    
    # SDSS system
    sdss_filters = [f for f in ['u', 'g', 'r', 'i', 'z'] if f in filter_columns]
    if len(sdss_filters) >= 3:
        systems['SDSS'] = {
            'filters': sdss_filters,
            'color_combinations': [],
            'description': 'Sloan Digital Sky Survey'
        }
        
        # Add SDSS color combinations
        if 'u' in sdss_filters and 'g' in sdss_filters and 'r' in sdss_filters:
            systems['SDSS']['color_combinations'].append(('u-g', 'g-r'))
        if 'g' in sdss_filters and 'r' in sdss_filters and 'i' in sdss_filters:
            systems['SDSS']['color_combinations'].append(('g-r', 'r-i'))
        if 'r' in sdss_filters and 'i' in sdss_filters and 'z' in sdss_filters:
            systems['SDSS']['color_combinations'].append(('r-i', 'i-z'))
    
    return systems

def get_color_data(md, color_name):
    """Extract color data from MESA data object."""
    if '-' not in color_name:
        return None
    
    f1, f2 = color_name.split('-')
    
    try:
        mag1 = getattr(md, f1)
        mag2 = getattr(md, f2)
    except AttributeError:
        try:
            mag1 = md.data(f1)
            mag2 = md.data(f2)
        except:
            return None
    
    return mag1 - mag2

def plot_single_color_color(logs_path="LOGS"):
    """Create color-color plots for a single MESA model."""
    
    if not os.path.isdir(logs_path):
        print(f"Error: Could not find {logs_path} directory")
        return
    
    history_path = os.path.join(logs_path, "history.data")
    if not os.path.exists(history_path):
        print(f"Error: Could not find history.data in {logs_path}")
        return
    
    print(f"Loading MESA data from {history_path}")
    md = mr.MesaData(history_path)
    
    # Get filter information
    all_cols, filter_columns = read_header_columns(history_path)
    print(f"Available photometric filters: {filter_columns}")
    
    # Set up all photometric systems
    systems = setup_all_photometric_systems(filter_columns)
    
    if not systems:
        print("No suitable photometric systems found!")
        return
    
    print(f"Available systems: {list(systems.keys())}")
    
    # Create figure with subplots for each system
    n_systems = len(systems)
    fig = plt.figure(figsize=(15, 5 * n_systems))
    
    plot_idx = 1
    
    for system_name, system_data in systems.items():
        print(f"Creating color-color plots for {system_name}...")
        
        n_combinations = len(system_data['color_combinations'])
        if n_combinations == 0:
            continue
        
        # Create subplot grid for this system
        for i, (color1, color2) in enumerate(system_data['color_combinations']):
            ax = plt.subplot(n_systems, max(2, n_combinations), plot_idx)
            plot_idx += 1
            
            # Get color data
            color1_data = get_color_data(md, color1)
            color2_data = get_color_data(md, color2)
            
            if color1_data is None or color2_data is None:
                print(f"Warning: Could not compute colors {color1} or {color2}")
                continue
            
            # Create evolutionary track with time coloring
            if hasattr(md, 'center_h1'):
                # Color by hydrogen abundance (evolutionary phase)
                scatter = ax.scatter(color1_data, color2_data, c=md.center_h1, 
                                   cmap='plasma_r', s=30, alpha=0.8, edgecolor='none')
                
                # Add colorbar
                cbar = plt.colorbar(scatter, ax=ax)
                cbar.set_label('Central H1 Fraction')
                
                # Mark evolutionary phases
                if np.max(md.center_h1) - np.min(md.center_h1) > 0.6:
                    # ZAMS (high H1)
                    zams_h1 = 0.7
                    zams_idx = np.abs(md.center_h1 - zams_h1).argmin()
                    ax.scatter(color1_data[zams_idx], color2_data[zams_idx], 
                             marker='*', s=300, edgecolor='black', facecolor='navy',
                             label='ZAMS', zorder=10)
                    
                    # TAMS (low H1) 
                    tams_h1 = 1e-6
                    tams_idx = np.abs(md.center_h1 - tams_h1).argmin()
                    ax.scatter(color1_data[tams_idx], color2_data[tams_idx], 
                             marker='s', s=200, edgecolor='black', facecolor='gold',
                             label='TAMS', zorder=10)
                    
                    ax.legend()
            else:
                # Simple line plot if no evolutionary data
                ax.plot(color1_data, color2_data, '-', color='blue', linewidth=2, alpha=0.8)
                ax.scatter(color1_data[0], color2_data[0], color='green', s=100, 
                          marker='o', label='Start', zorder=5)
                ax.scatter(color1_data[-1], color2_data[-1], color='red', s=100, 
                          marker='s', label='End', zorder=5)
                ax.legend()
            
            ax.set_xlabel(color1)
            ax.set_ylabel(color2)
            ax.set_title(f"{system_name}: {color1} vs {color2}")
            ax.grid(alpha=0.3)
    
    plt.suptitle("Multi-System Color-Color Diagrams - Custom Colors Showcase", fontsize=16)
    plt.tight_layout()
    
    # Save the plot
    os.makedirs("plots", exist_ok=True)
    plt.savefig("plots/color_color_diagrams_single.png", dpi=300, bbox_inches='tight')
    print("Saved: plots/color_color_diagrams_single.png")
    
    plt.show()

def plot_batch_color_color(runs_dir="../runs"):
    """Create comparative color-color plots for batch MESA runs."""
    
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
            continue
        
        try:
            # Parse parameters
            parts = run_dir.replace('inlist_M', '').split('_')
            mass = float(parts[0])
            
            if 'noovs' in run_dir:
                scheme = 'none'
            else:
                scheme = parts[2] if len(parts) > 2 else 'unknown'
            
            # Load data
            md = mr.MesaData(history_path)
            
            # Get filter information
            all_cols, filter_columns = read_header_columns(history_path)
            
            if not filter_columns:
                continue
            
            # Store data
            run_info = {
                'data': md,
                'mass': mass,
                'scheme': scheme,
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
    
    # Find common photometric systems
    all_filter_sets = [set(run['filter_columns']) for run in all_data]
    common_filters = list(set.intersection(*all_filter_sets))
    
    print(f"Common filters across all models: {common_filters}")
    
    # Set up systems based on common filters
    systems = setup_all_photometric_systems(common_filters)
    
    if not systems:
        print("No common photometric systems found!")
        return
    
    # Create comparison plots for each system
    for system_name, system_data in systems.items():
        create_batch_color_color_system(all_data, system_name, system_data, 
                                       mass_colors, scheme_linestyles)

def create_batch_color_color_system(all_data, system_name, system_data, 
                                   mass_colors, scheme_linestyles):
    """Create batch color-color plots for a specific photometric system."""
    
    color_combinations = system_data['color_combinations']
    n_combinations = len(color_combinations)
    
    if n_combinations == 0:
        return
    
    fig, axes = plt.subplots(1, n_combinations, figsize=(7*n_combinations, 6))
    if n_combinations == 1:
        axes = [axes]
    
    for i, (color1, color2) in enumerate(color_combinations):
        ax = axes[i]
        
        # Plot each model
        for run in all_data:
            md = run['data']
            
            color1_data = get_color_data(md, color1)
            color2_data = get_color_data(md, color2)
            
            if color1_data is None or color2_data is None:
                continue
            
            color = mass_colors[run['mass']]
            linestyle = scheme_linestyles[run['scheme']]
            
            # Plot evolutionary track
            ax.plot(color1_data, color2_data, color=color, linestyle=linestyle,
                   linewidth=2, alpha=0.8)
            
            # Mark start and end points
            ax.scatter(color1_data[0], color2_data[0], color=color, 
                      marker='o', s=60, alpha=0.9, edgecolor='black', linewidth=0.5)
            ax.scatter(color1_data[-1], color2_data[-1], color=color, 
                      marker='s', s=60, alpha=0.9, edgecolor='black', linewidth=0.5)
        
        ax.set_xlabel(color1)
        ax.set_ylabel(color2)
        ax.set_title(f"{system_name}: {color1} vs {color2}")
        ax.grid(alpha=0.3)
    
    # Create custom legend
    legend_elements = []
    
    # Mass legend
    for mass in sorted(mass_colors.keys()):
        legend_elements.append(plt.Line2D([0], [0], color=mass_colors[mass], 
                                        linewidth=3, label=f'M = {mass:.1f} M☉'))
    
    # Scheme legend
    for scheme in sorted(scheme_linestyles.keys()):
        legend_elements.append(plt.Line2D([0], [0], color='gray', 
                                        linestyle=scheme_linestyles[scheme],
                                        linewidth=2, label=f'{scheme} overshooting'))
    
    # Add markers legend
    legend_elements.extend([
        plt.Line2D([0], [0], marker='o', color='gray', linewidth=0, 
                  markersize=8, label='ZAMS'),
        plt.Line2D([0], [0], marker='s', color='gray', linewidth=0, 
                  markersize=8, label='TAMS')
    ])
    
    # Place legend
    if n_combinations > 1:
        axes[-1].legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        axes[0].legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.suptitle(f"{system_name} Color-Color Diagrams - Parameter Study\n"
                f"{system_data['description']}", fontsize=14)
    plt.tight_layout()
    
    # Save the plot
    os.makedirs("plots", exist_ok=True)
    filename = f"plots/batch_color_color_{system_name.lower()}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()

def create_multi_system_comparison(logs_path="LOGS"):
    """Create a comprehensive comparison showing all systems side by side."""
    
    if not os.path.isdir(logs_path):
        print(f"Error: Could not find {logs_path} directory")
        return
    
    history_path = os.path.join(logs_path, "history.data")
    if not os.path.exists(history_path):
        print(f"Error: Could not find history.data in {logs_path}")
        return
    
    md = mr.MesaData(history_path)
    all_cols, filter_columns = read_header_columns(history_path)
    systems = setup_all_photometric_systems(filter_columns)
    
    if len(systems) < 2:
        print("Need at least 2 photometric systems for comparison")
        return
    
    # Create a grid showing one color-color diagram per system
    n_systems = len(systems)
    fig, axes = plt.subplots(1, n_systems, figsize=(5*n_systems, 5))
    if n_systems == 1:
        axes = [axes]
    
    for i, (system_name, system_data) in enumerate(systems.items()):
        ax = axes[i]
        
        if not system_data['color_combinations']:
            continue
        
        # Use the first color combination for each system
        color1, color2 = system_data['color_combinations'][0]
        
        color1_data = get_color_data(md, color1)
        color2_data = get_color_data(md, color2)
        
        if color1_data is None or color2_data is None:
            continue
        
        # Plot with evolutionary phases
        if hasattr(md, 'center_h1'):
            scatter = ax.scatter(color1_data, color2_data, c=md.center_h1, 
                               cmap='plasma_r', s=40, alpha=0.8)
            
            # Add arrows to show direction
            n_points = len(color1_data)
            step = max(1, n_points // 20)  # Show ~20 arrows
            
            for j in range(0, n_points-step, step):
                ax.annotate('', xy=(color1_data[j+step], color2_data[j+step]),
                           xytext=(color1_data[j], color2_data[j]),
                           arrowprops=dict(arrowstyle='->', color='black', 
                                         alpha=0.5, lw=1))
        else:
            ax.plot(color1_data, color2_data, '-', linewidth=2)
        
        ax.set_xlabel(color1)
        ax.set_ylabel(color2)
        ax.set_title(f"{system_name}\n{system_data['description']}")
        ax.grid(alpha=0.3)
    
    plt.suptitle("Multi-System Color-Color Comparison", fontsize=16)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig("plots/multi_system_color_color.png", dpi=300, bbox_inches='tight')
    print("Saved: plots/multi_system_color_color.png")
    
    plt.show()

if __name__ == "__main__":
    print("MESA Custom Colors - Color-Color Diagram Analysis")
    print("=================================================")
    
    # Check for single model first
    if os.path.exists("LOGS/history.data"):
        print("Creating single model color-color plots...")
        plot_single_color_color()
        create_multi_system_comparison()
    
    # Check for custom log directories
    log_dirs = glob.glob("LOGS_M*")
    if log_dirs:
        log_dir = log_dirs[0]
        print(f"Found custom log directory: {log_dir}")
        plot_single_color_color(log_dir)
        create_multi_system_comparison(log_dir)
    
    # Check for batch runs
    if os.path.exists("../runs"):
        print("Creating batch color-color plots...")
        plot_batch_color_color("../runs")
    elif os.path.exists("runs"):
        print("Creating batch color-color plots...")
        plot_batch_color_color("runs")