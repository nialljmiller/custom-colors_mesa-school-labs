#!/usr/bin/env python3
"""
physics_photometry_correlations.py - Internal Physics vs Photometric Properties
Demonstrates how stellar internal structure changes manifest in observable colors
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import mesa_reader as mr
import matplotlib.gridspec as gridspec
import glob
from scipy import stats
from matplotlib.colors import LogNorm

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

def setup_primary_photometric_system(md, filter_columns):
    """Choose the best available photometric system for analysis."""
    
    # Priority order for analysis
    systems = [
        ('GAIA', ['Gbp', 'G', 'Grp'], 'Gbp-Grp', 'G'),
        ('Johnson', ['B', 'V'], 'B-V', 'V'),
        ('2MASS', ['J', 'K'], 'J-K', 'K'),
        ('SDSS', ['g', 'r'], 'g-r', 'r')
    ]
    
    for name, required_filters, primary_color, primary_mag in systems:
        if all(f in filter_columns for f in required_filters):
            return {
                'name': name,
                'filters': required_filters,
                'primary_color': primary_color,
                'primary_mag': primary_mag
            }
    
    return None

def get_color_magnitude_data(md, system):
    """Extract color and magnitude data from MESA model."""
    f1, f2 = system['primary_color'].split('-')
    
    try:
        mag1 = getattr(md, f1)
        mag2 = getattr(md, f2)
        primary_mag = getattr(md, system['primary_mag'])
    except AttributeError:
        mag1 = md.data(f1)
        mag2 = md.data(f2)
        primary_mag = md.data(system['primary_mag'])
    
    color = mag1 - mag2
    return color, primary_mag

def plot_physics_photometry_single(logs_path="LOGS"):
    """Create comprehensive physics-photometry correlation plots for a single model."""
    
    if not os.path.isdir(logs_path):
        print(f"Error: Could not find {logs_path} directory")
        return
    
    history_path = os.path.join(logs_path, "history.data")
    if not os.path.exists(history_path):
        print(f"Error: Could not find history.data in {logs_path}")
        return
    
    print(f"Loading MESA data from {history_path}")
    md = mr.MesaData(history_path)
    
    # Get photometric system
    all_cols, filter_columns = read_header_columns(history_path)
    system = setup_primary_photometric_system(md, filter_columns)
    
    if system is None:
        print("No suitable photometric system found!")
        return
    
    print(f"Using {system['name']} photometric system")
    
    # Get color and magnitude data
    color, magnitude = get_color_magnitude_data(md, system)
    
    # Create comprehensive figure
    fig = plt.figure(figsize=(20, 15))
    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.3, wspace=0.3)
    
    # Plot 1: Color vs Central Temperature
    ax1 = fig.add_subplot(gs[0, 0])
    if hasattr(md, 'log_center_T'):
        if hasattr(md, 'center_h1'):
            scatter = ax1.scatter(md.log_center_T, color, c=md.center_h1, 
                                cmap='plasma_r', s=30, alpha=0.8)
            plt.colorbar(scatter, ax=ax1, label='Central H1')
        else:
            ax1.plot(md.log_center_T, color, '-', color='blue', linewidth=2)
        
        ax1.set_xlabel('log Central Temperature')
        ax1.set_ylabel(f'{system["primary_color"]}')
        ax1.set_title('Color vs Central Temperature')
        ax1.grid(alpha=0.3)
    
    # Plot 2: Magnitude vs Central Density
    ax2 = fig.add_subplot(gs[0, 1])
    if hasattr(md, 'log_center_Rho'):
        if hasattr(md, 'center_h1'):
            scatter = ax2.scatter(md.log_center_Rho, magnitude, c=md.center_h1, 
                                cmap='plasma_r', s=30, alpha=0.8)
            plt.colorbar(scatter, ax=ax2, label='Central H1')
        else:
            ax2.plot(md.log_center_Rho, magnitude, '-', color='red', linewidth=2)
        
        ax2.set_xlabel('log Central Density')
        ax2.set_ylabel(f'{system["primary_mag"]} magnitude')
        ax2.set_title('Magnitude vs Central Density')
        ax2.invert_yaxis()
        ax2.grid(alpha=0.3)
    
    # Plot 3: Color vs Convective Core Mass
    ax3 = fig.add_subplot(gs[0, 2])
    core_mass = None
    if hasattr(md, 'he_core_mass'):
        core_mass = md.he_core_mass
        core_label = 'He Core Mass (M☉)'
    elif hasattr(md, 'mass_conv_core'):
        core_mass = md.mass_conv_core
        core_label = 'Convective Core Mass (M☉)'
    elif hasattr(md, 'conv_mx1_top'):
        if hasattr(md, 'star_mass'):
            core_mass = md.conv_mx1_top * md.star_mass
        else:
            core_mass = md.conv_mx1_top
        core_label = 'Convective Core Mass (M☉)'
    
    if core_mass is not None:
        if hasattr(md, 'star_age'):
            scatter = ax3.scatter(core_mass, color, c=md.star_age/1e6, 
                                cmap='viridis', s=30, alpha=0.8)
            plt.colorbar(scatter, ax=ax3, label='Age (Myr)')
        else:
            ax3.plot(core_mass, color, '-', color='green', linewidth=2)
        
        ax3.set_xlabel(core_label)
        ax3.set_ylabel(f'{system["primary_color"]}')
        ax3.set_title('Color vs Core Mass')
        ax3.grid(alpha=0.3)
    
    # Plot 4: Surface vs Central Properties
    ax4 = fig.add_subplot(gs[0, 3])
    if hasattr(md, 'log_Teff') and hasattr(md, 'log_center_T'):
        if hasattr(md, 'center_h1'):
            scatter = ax4.scatter(md.log_Teff, md.log_center_T, c=color, 
                                cmap='coolwarm', s=30, alpha=0.8)
            plt.colorbar(scatter, ax=ax4, label=system['primary_color'])
        else:
            ax4.plot(md.log_Teff, md.log_center_T, '-', color='purple', linewidth=2)
        
        ax4.set_xlabel('log Surface Temperature')
        ax4.set_ylabel('log Central Temperature')
        ax4.set_title('Surface vs Central Temperature\n(colored by color index)')
        ax4.grid(alpha=0.3)
    
    # Plot 5: Luminosity vs Color Evolution
    ax5 = fig.add_subplot(gs[1, 0])
    if hasattr(md, 'log_L'):
        if hasattr(md, 'star_age'):
            scatter = ax5.scatter(color, md.log_L, c=md.star_age/1e6, 
                                cmap='plasma', s=30, alpha=0.8)
            plt.colorbar(scatter, ax=ax5, label='Age (Myr)')
        else:
            ax5.plot(color, md.log_L, '-', color='orange', linewidth=2)
        
        ax5.set_xlabel(f'{system["primary_color"]}')
        ax5.set_ylabel('log L/L☉')
        ax5.set_title('Luminosity vs Color')
        ax5.grid(alpha=0.3)
    
    # Plot 6: Nuclear Energy Generation vs Color
    ax6 = fig.add_subplot(gs[1, 1])
    if hasattr(md, 'log_LH') or hasattr(md, 'log_center_eps_nuc'):
        nuclear_var = None
        nuclear_label = None
        
        if hasattr(md, 'log_LH'):
            nuclear_var = md.log_LH
            nuclear_label = 'log H Burning Luminosity'
        elif hasattr(md, 'log_center_eps_nuc'):
            nuclear_var = md.log_center_eps_nuc
            nuclear_label = 'log Central Nuclear Energy Rate'
        
        if nuclear_var is not None:
            if hasattr(md, 'center_h1'):
                scatter = ax6.scatter(color, nuclear_var, c=md.center_h1, 
                                    cmap='plasma_r', s=30, alpha=0.8)
                plt.colorbar(scatter, ax=ax6, label='Central H1')
            else:
                ax6.plot(color, nuclear_var, '-', color='red', linewidth=2)
            
            ax6.set_xlabel(f'{system["primary_color"]}')
            ax6.set_ylabel(nuclear_label)
            ax6.set_title('Nuclear Energy vs Color')
            ax6.grid(alpha=0.3)
    
    # Plot 7: Stellar Radius vs Magnitude
    ax7 = fig.add_subplot(gs[1, 2])
    if hasattr(md, 'log_R'):
        if hasattr(md, 'star_age'):
            scatter = ax7.scatter(md.log_R, magnitude, c=md.star_age/1e6, 
                                cmap='viridis', s=30, alpha=0.8)
            plt.colorbar(scatter, ax=ax7, label='Age (Myr)')
        else:
            ax7.plot(md.log_R, magnitude, '-', color='blue', linewidth=2)
        
        ax7.set_xlabel('log R/R☉')
        ax7.set_ylabel(f'{system["primary_mag"]} magnitude')
        ax7.set_title('Stellar Radius vs Magnitude')
        ax7.invert_yaxis()
        ax7.grid(alpha=0.3)
    
    # Plot 8: Mass Loss vs Photometry (if available)
    ax8 = fig.add_subplot(gs[1, 3])
    if hasattr(md, 'log_abs_mdot'):
        if hasattr(md, 'star_age'):
            # Only plot points where mass loss is significant
            significant_mdot = md.log_abs_mdot > -10
            if np.any(significant_mdot):
                scatter = ax8.scatter(color[significant_mdot], md.log_abs_mdot[significant_mdot], 
                                    c=md.star_age[significant_mdot]/1e6, 
                                    cmap='plasma', s=30, alpha=0.8)
                plt.colorbar(scatter, ax=ax8, label='Age (Myr)')
                ax8.set_xlabel(f'{system["primary_color"]}')
                ax8.set_ylabel('log |Mdot| (M☉/yr)')
                ax8.set_title('Mass Loss vs Color')
                ax8.grid(alpha=0.3)
    
    # Plot 9: Time Evolution of Key Quantities
    ax9 = fig.add_subplot(gs[2, :2])
    if hasattr(md, 'star_age'):
        age_myr = md.star_age / 1e6
        
        # Create multiple y-axes for different quantities
        ax9_color = ax9
        ax9_mag = ax9.twinx()
        ax9_lum = ax9_mag.twinx()
        
        # Offset the third y-axis
        ax9_lum.spines['right'].set_position(('outward', 60))
        
        # Plot color evolution
        line1 = ax9_color.plot(age_myr, color, 'b-', linewidth=2, 
                              label=f'{system["primary_color"]}')
        ax9_color.set_xlabel('Age (Myr)')
        ax9_color.set_ylabel(f'{system["primary_color"]}', color='b')
        ax9_color.tick_params(axis='y', labelcolor='b')
        
        # Plot magnitude evolution
        line2 = ax9_mag.plot(age_myr, magnitude, 'r-', linewidth=2, 
                            label=f'{system["primary_mag"]}')
        ax9_mag.set_ylabel(f'{system["primary_mag"]} magnitude', color='r')
        ax9_mag.tick_params(axis='y', labelcolor='r')
        ax9_mag.invert_yaxis()
        
        # Plot luminosity if available
        if hasattr(md, 'log_L'):
            line3 = ax9_lum.plot(age_myr, md.log_L, 'g-', linewidth=2, 
                                label='log L/L☉')
            ax9_lum.set_ylabel('log L/L☉', color='g')
            ax9_lum.tick_params(axis='y', labelcolor='g')
        
        ax9_color.set_title('Evolution of Photometric Properties')
        ax9_color.grid(alpha=0.3)
    
    # Plot 10: Phase Space Analysis
    ax10 = fig.add_subplot(gs[2, 2:])
    if hasattr(md, 'log_center_T') and hasattr(md, 'log_center_Rho'):
        # Create a phase space plot colored by photometric color
        scatter = ax10.scatter(md.log_center_T, md.log_center_Rho, c=color, 
                              cmap='coolwarm', s=40, alpha=0.8)
        
        # Add evolutionary arrows
        n_points = len(md.log_center_T)
        step = max(1, n_points // 15)
        
        for i in range(0, n_points-step, step):
            ax10.annotate('', 
                         xy=(md.log_center_T[i+step], md.log_center_Rho[i+step]),
                         xytext=(md.log_center_T[i], md.log_center_Rho[i]),
                         arrowprops=dict(arrowstyle='->', color='black', 
                                       alpha=0.6, lw=1))
        
        plt.colorbar(scatter, ax=ax10, label=f'{system["primary_color"]}')
        ax10.set_xlabel('log Central Temperature')
        ax10.set_ylabel('log Central Density')
        ax10.set_title('Central Conditions Phase Space\n(colored by color index)')
        ax10.grid(alpha=0.3)
    
    # Overall title
    model_mass = getattr(md, 'star_mass', [1.0])[-1] if hasattr(md, 'star_mass') else 1.0
    fig.suptitle(f'Physics-Photometry Correlations: {system["name"]} System\n'
                f'Model Mass: {model_mass:.2f} M☉', fontsize=16)
    
    # Save the plot
    os.makedirs("plots", exist_ok=True)
    filename = f"plots/physics_photometry_{system['name'].lower()}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()

def plot_batch_physics_photometry(runs_dir="../runs"):
    """Create physics-photometry correlation plots for batch runs."""
    
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
    
    # Collect data from all runs
    all_data = []
    
    for run_dir in run_dirs:
        history_path = os.path.join(runs_dir, run_dir, "LOGS", "history.data")
        
        if not os.path.exists(history_path):
            continue
        
        try:
            # Parse parameters
            parts = run_dir.replace('inlist_M', '').split('_')
            mass = float(parts[0])
            
            # Load data
            md = mr.MesaData(history_path)
            
            # Get photometric system
            all_cols, filter_columns = read_header_columns(history_path)
            system = setup_primary_photometric_system(md, filter_columns)
            
            if system is None:
                continue
            
            # Get final values for comparison
            color, magnitude = get_color_magnitude_data(md, system)
            
            final_data = {
                'mass': mass,
                'color': color[-1],
                'magnitude': magnitude[-1],
                'system': system,
                'md': md,
                'run_dir': run_dir
            }
            
            # Add physics parameters if available
            if hasattr(md, 'log_center_T'):
                final_data['final_center_T'] = md.log_center_T[-1]
            if hasattr(md, 'log_center_Rho'):
                final_data['final_center_Rho'] = md.log_center_Rho[-1]
            if hasattr(md, 'log_L'):
                final_data['final_log_L'] = md.log_L[-1]
            if hasattr(md, 'log_Teff'):
                final_data['final_log_Teff'] = md.log_Teff[-1]
            
            all_data.append(final_data)
            
        except Exception as e:
            print(f"Error processing {run_dir}: {e}")
            continue
    
    if not all_data:
        print("No valid data found!")
        return
    
    # Create comparison plots
    create_mass_scaling_plots(all_data)

def create_mass_scaling_plots(all_data):
    """Create plots showing how photometric properties scale with stellar mass."""
    
    masses = np.array([d['mass'] for d in all_data])
    colors = np.array([d['color'] for d in all_data])
    magnitudes = np.array([d['magnitude'] for d in all_data])
    
    system_name = all_data[0]['system']['name']
    color_name = all_data[0]['system']['primary_color']
    mag_name = all_data[0]['system']['primary_mag']
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Color vs Mass
    ax1.scatter(masses, colors, s=100, alpha=0.7, color='blue')
    
    # Fit trend line
    if len(masses) > 2:
        z = np.polyfit(masses, colors, 1)
        p = np.poly1d(z)
        ax1.plot(masses, p(masses), 'r--', alpha=0.8, 
                label=f'Slope: {z[0]:.3f} mag/M☉')
        ax1.legend()
    
    ax1.set_xlabel('Stellar Mass (M☉)')
    ax1.set_ylabel(f'{color_name}')
    ax1.set_title(f'Final {color_name} vs Stellar Mass')
    ax1.grid(alpha=0.3)
    
    # Plot 2: Magnitude vs Mass
    ax2.scatter(masses, magnitudes, s=100, alpha=0.7, color='red')
    
    if len(masses) > 2:
        z = np.polyfit(masses, magnitudes, 1)
        p = np.poly1d(z)
        ax2.plot(masses, p(masses), 'b--', alpha=0.8, 
                label=f'Slope: {z[0]:.3f} mag/M☉')
        ax2.legend()
    
    ax2.set_xlabel('Stellar Mass (M☉)')
    ax2.set_ylabel(f'{mag_name} magnitude')
    ax2.set_title(f'Final {mag_name} vs Stellar Mass')
    ax2.invert_yaxis()
    ax2.grid(alpha=0.3)
    
    # Plot 3: Color-Magnitude diagram colored by mass
    scatter = ax3.scatter(colors, magnitudes, c=masses, s=100, 
                         cmap='viridis', alpha=0.8)
    plt.colorbar(scatter, ax=ax3, label='Mass (M☉)')
    
    ax3.set_xlabel(f'{color_name}')
    ax3.set_ylabel(f'{mag_name} magnitude')
    ax3.set_title('Color-Magnitude Diagram\n(colored by mass)')
    ax3.invert_yaxis()
    ax3.grid(alpha=0.3)
    
    # Plot 4: Physics correlations (if available)
    physics_available = any('final_log_L' in d for d in all_data)
    
    if physics_available:
        log_L_vals = np.array([d.get('final_log_L', np.nan) for d in all_data])
        valid_mask = ~np.isnan(log_L_vals)
        
        if np.sum(valid_mask) > 1:
            scatter = ax4.scatter(colors[valid_mask], log_L_vals[valid_mask], 
                                c=masses[valid_mask], s=100, cmap='plasma', alpha=0.8)
            plt.colorbar(scatter, ax=ax4, label='Mass (M☉)')
            
            ax4.set_xlabel(f'{color_name}')
            ax4.set_ylabel('log L/L☉')
            ax4.set_title('Color vs Luminosity\n(colored by mass)')
            ax4.grid(alpha=0.3)
    
    plt.suptitle(f'{system_name} Photometry: Mass Scaling Relations\n'
                f'Based on {len(all_data)} stellar models', fontsize=14)
    plt.tight_layout()
    
    # Save the plot
    os.makedirs("plots", exist_ok=True)
    filename = f"plots/mass_scaling_{system_name.lower()}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()

if __name__ == "__main__":
    print("MESA Custom Colors - Physics-Photometry Correlation Analysis")
    print("============================================================")
    
    # Check for single model first
    if os.path.exists("LOGS/history.data"):
        print("Creating single model physics-photometry plots...")
        plot_physics_photometry_single()
    
    # Check for custom log directories
    log_dirs = glob.glob("LOGS_M*")
    if log_dirs:
        log_dir = log_dirs[0]
        print(f"Found custom log directory: {log_dir}")
        plot_physics_photometry_single(log_dir)
    
    # Check for batch runs
    if os.path.exists("../runs"):
        print("Creating batch physics-photometry plots...")
        plot_batch_physics_photometry("../runs")
    elif os.path.exists("runs"):
        print("Creating batch physics-photometry plots...")
        plot_batch_physics_photometry("runs")