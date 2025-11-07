#!/usr/bin/env python3
"""
Analyze motor neuron activity before and after pain injection.

This script extracts motor neuron activity data from the simulation output
and compares activity before and after pain injection to determine if
the nematode moves more aggressively (more reversals) after pain.

Usage:
    python analyze_motor_activity.py <activity_file> <pain_start_ms>

Example:
    python analyze_motor_activity.py examples/c302_A_EternalPainWithMotors.dat 2000
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def get_column_names_from_lems(lems_file):
    """Extract column names from LEMS XML file."""
    import xml.etree.ElementTree as ET
    import os
    try:
        if not os.path.exists(lems_file):
            return None
        
        tree = ET.parse(lems_file)
        root = tree.getroot()
        
        # Find the OutputFile that matches our dat file
        output_columns = []
        # Try without namespace first (simpler)
        for column in root.findall('.//OutputColumn'):
            col_id = column.get('id')
            if col_id:
                output_columns.append(col_id)
        
        # If that didn't work, try with namespace
        if not output_columns:
            ns = 'http://www.neuroml.org/lems/0.7.1'
            prefix = f'{{{ns}}}'
            for column in root.findall(f'.//{prefix}OutputColumn'):
                col_id = column.get('id')
                if col_id:
                    output_columns.append(col_id)
        
        if output_columns:
            # First column is always time
            return ['time'] + output_columns
        return None
    except Exception as e:
        print(f"Warning: Could not parse LEMS file {lems_file}: {e}")
        return None


def load_activity_data(filename, lems_file=None):
    """Load activity data from c302 output file."""
    try:
        # c302 output files are tab-separated with no headers
        # First try to get column names from LEMS file
        column_names = None
        if lems_file:
            column_names = get_column_names_from_lems(lems_file)
        
        # Load data - if no column names, pandas will number them
        data = pd.read_csv(filename, sep='\t', header=None, engine='python')
        
        # Assign column names if we have them
        if column_names and len(column_names) == len(data.columns):
            data.columns = column_names
        elif len(data.columns) > 0:
            # Use generic names: time, col1, col2, etc.
            data.columns = ['time'] + [f'col{i}' for i in range(1, len(data.columns))]
        
        return data
    except Exception as e:
        print(f"Error loading file {filename}: {e}")
        print("Make sure the simulation has been run first!")
        sys.exit(1)


def analyze_motor_activity(data, pain_start_ms, duration_ms=10000):
    """Analyze motor neuron activity before and after pain injection."""
    
    # Extract time column (usually first column)
    time_col = data.columns[0]
    times = data[time_col].values
    
    # Identify motor neurons (VB, VD, DD, DB)
    # Check for voltage columns first (format: VB1_v, etc.) - this is the standard c302 format
    forward_motors = [col for col in data.columns if any(m in col for m in ['VB', 'DB']) and '_v' in col]
    backward_motors = [col for col in data.columns if any(m in col for m in ['VD', 'DD']) and '_v' in col]
    
    # If not found with _v suffix, try without
    if not forward_motors and not backward_motors:
        forward_motors = [col for col in data.columns if col.startswith('VB') or col.startswith('DB')]
        backward_motors = [col for col in data.columns if col.startswith('VD') or col.startswith('DD')]
    
    # Filter to only crucial motor cells for plotting: VB2, VB3, VD2, VD3, DD2, DD3, DB2, DB3
    crucial_cells = ['VB2', 'VB3', 'VD2', 'VD3', 'DD2', 'DD3', 'DB2', 'DB3']
    forward_motors = [col for col in forward_motors if any(cell in col for cell in ['VB2', 'VB3', 'DB2', 'DB3'])]
    backward_motors = [col for col in backward_motors if any(cell in col for cell in ['VD2', 'VD3', 'DD2', 'DD3'])]
    
    # Also check for pattern like 'col5', 'col6' if columns are numbered
    if not forward_motors and not backward_motors:
        # Check if we have numbered columns - need to check LEMS file for actual names
        print("Note: Columns appear to be numbered. Checking LEMS file for neuron names...")
        # This will be handled by the LEMS file parsing above
    
    print(f"Found {len(forward_motors)} crucial forward motor neurons (filtered to VB2, VB3, DB2, DB3)")
    if forward_motors:
        print(f"  Forward motors: {forward_motors}")
    
    print(f"Found {len(backward_motors)} crucial backward motor neurons (filtered to VD2, VD3, DD2, DD3)")
    if backward_motors:
        print(f"  Backward motors: {backward_motors}")
    
    if not forward_motors and not backward_motors:
        print("\n⚠️  WARNING: No motor neurons found in data!")
        print(f"Available columns ({len(data.columns)} total):")
        print(f"  First 10: {list(data.columns[:10])}")
        print(f"  Looking for columns containing: VB, DB, VD, DD (with _v suffix or without)")
        print("\nTip: Make sure:")
        print("  1. The simulation has been run (pynml LEMS_c302_A_EternalPainWithMotors.xml)")
        print("  2. The LEMS file is accessible for column name extraction")
        return None
    
    # Calculate mean activity for forward and backward motors
    if forward_motors:
        forward_activity = data[forward_motors].mean(axis=1).values
    else:
        forward_activity = np.zeros(len(times))
    
    if backward_motors:
        backward_activity = data[backward_motors].mean(axis=1).values
    else:
        backward_activity = np.zeros(len(times))
    
    # Find indices for before and after pain
    pain_start_idx = np.argmin(np.abs(times - pain_start_ms))
    
    before_mask = times < pain_start_ms
    after_mask = times >= pain_start_ms
    
    # Calculate statistics
    forward_before = forward_activity[before_mask]
    forward_after = forward_activity[after_mask]
    backward_before = backward_activity[before_mask]
    backward_after = backward_activity[after_mask]
    
    results = {
        'times': times,
        'forward_activity': forward_activity,
        'backward_activity': backward_activity,
        'forward_before_mean': np.mean(forward_before) if len(forward_before) > 0 else 0,
        'forward_after_mean': np.mean(forward_after) if len(forward_after) > 0 else 0,
        'backward_before_mean': np.mean(backward_before) if len(backward_before) > 0 else 0,
        'backward_after_mean': np.mean(backward_after) if len(backward_after) > 0 else 0,
        'forward_before_std': np.std(forward_before) if len(forward_before) > 0 else 0,
        'forward_after_std': np.std(forward_after) if len(forward_after) > 0 else 0,
        'backward_before_std': np.std(backward_before) if len(backward_before) > 0 else 0,
        'backward_after_std': np.std(backward_after) if len(backward_after) > 0 else 0,
        'pain_start_idx': pain_start_idx,
        'pain_start_ms': pain_start_ms,
    }
    
    return results


def print_analysis(results):
    """Print analysis results."""
    print("\n" + "=" * 70)
    print("CRUCIAL MOTOR NEURON ACTIVITY ANALYSIS")
    print("=" * 70)
    print(f"\nPain injection time: {results['pain_start_ms']} ms")
    print("\n--- FORWARD MOTOR NEURONS (VB2, VB3, DB2, DB3) ---")
    print(f"Before pain:  Mean = {results['forward_before_mean']:.4f}, Std = {results['forward_before_std']:.4f}")
    print(f"After pain:   Mean = {results['forward_after_mean']:.4f}, Std = {results['forward_after_std']:.4f}")
    
    forward_change = results['forward_after_mean'] - results['forward_before_mean']
    forward_pct = (forward_change / results['forward_before_mean'] * 100) if results['forward_before_mean'] != 0 else 0
    print(f"Change:       {forward_change:+.4f} ({forward_pct:+.2f}%)")
    
    print("\n--- BACKWARD/REVERSAL MOTOR NEURONS (VD2, VD3, DD2, DD3) ---")
    print(f"Before pain:  Mean = {results['backward_before_mean']:.4f}, Std = {results['backward_before_std']:.4f}")
    print(f"After pain:   Mean = {results['backward_after_mean']:.4f}, Std = {results['backward_after_std']:.4f}")
    
    backward_change = results['backward_after_mean'] - results['backward_before_mean']
    backward_pct = (backward_change / results['backward_before_mean'] * 100) if results['backward_before_mean'] != 0 else 0
    print(f"Change:       {backward_change:+.4f} ({backward_pct:+.2f}%)")
    
    print("\n--- INTERPRETATION ---")
    if backward_change > forward_change and backward_change > 0:
        print("✓ AGGRESSIVE MOVEMENT DETECTED: Significant increase in reversal activity after pain")
        print("  The nematode is showing avoidance behavior (reversals) in response to pain")
    elif forward_change < 0:
        print("✓ MOVEMENT INHIBITION: Decrease in forward movement after pain")
        print("  The nematode is stopping forward locomotion in response to pain")
    else:
        print("? Movement pattern needs further analysis")
    
    print("=" * 70 + "\n")


def plot_activity(results, output_file=None):
    """Plot motor neuron activity over time."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    times = results['times']
    pain_start = results['pain_start_ms']
    
    # Plot forward motor activity (crucial cells only: VB2, VB3, DB2, DB3)
    ax1.plot(times, results['forward_activity'], 'g-', label='Forward motors (VB2, VB3, DB2, DB3)', linewidth=1.5)
    ax1.axvline(pain_start, color='r', linestyle='--', linewidth=2, label=f'Pain injection ({pain_start} ms)')
    ax1.axhline(results['forward_before_mean'], color='g', linestyle=':', alpha=0.5, label='Before mean')
    ax1.axhline(results['forward_after_mean'], color='g', linestyle='--', alpha=0.5, label='After mean')
    ax1.fill_between(times, 
                     results['forward_before_mean'] - results['forward_before_std'],
                     results['forward_before_mean'] + results['forward_before_std'],
                     where=times < pain_start, alpha=0.2, color='g')
    ax1.fill_between(times,
                     results['forward_after_mean'] - results['forward_after_std'],
                     results['forward_after_mean'] + results['forward_after_std'],
                     where=times >= pain_start, alpha=0.2, color='g')
    ax1.set_ylabel('Forward Motor Activity', fontsize=12)
    ax1.set_title('Crucial Motor Neuron Activity Before and After Pain Injection', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot backward motor activity (crucial cells only: VD2, VD3, DD2, DD3)
    ax2.plot(times, results['backward_activity'], 'r-', label='Backward/reversal motors (VD2, VD3, DD2, DD3)', linewidth=1.5)
    ax2.axvline(pain_start, color='r', linestyle='--', linewidth=2, label=f'Pain injection ({pain_start} ms)')
    ax2.axhline(results['backward_before_mean'], color='r', linestyle=':', alpha=0.5, label='Before mean')
    ax2.axhline(results['backward_after_mean'], color='r', linestyle='--', alpha=0.5, label='After mean')
    ax2.fill_between(times,
                     results['backward_before_mean'] - results['backward_before_std'],
                     results['backward_before_mean'] + results['backward_before_std'],
                     where=times < pain_start, alpha=0.2, color='r')
    ax2.fill_between(times,
                     results['backward_after_mean'] - results['backward_after_std'],
                     results['backward_after_mean'] + results['backward_after_std'],
                     where=times >= pain_start, alpha=0.2, color='r')
    ax2.set_xlabel('Time (ms)', fontsize=12)
    ax2.set_ylabel('Backward/Reversal Motor Activity', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_file}")
    else:
        plt.savefig('motor_activity_analysis.png', dpi=150, bbox_inches='tight')
        print("Plot saved to: motor_activity_analysis.png")
    
    plt.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: Missing required arguments")
        print("\nUsage: python analyze_motor_activity.py <activity_file> [pain_start_ms] [lems_file]")
        sys.exit(1)
    
    filename = sys.argv[1]
    pain_start_ms = int(sys.argv[2]) if len(sys.argv) >= 3 else 2000
    lems_file = sys.argv[3] if len(sys.argv) >= 4 else None
    
    # If no LEMS file provided, try to infer it from dat filename
    if not lems_file:
        base_name = filename.replace('.dat', '')
        if '/examples/' in base_name:
            lems_file = base_name.replace('.dat', '.xml').replace('/examples/', '/examples/LEMS_')
        else:
            lems_file = base_name.replace('.dat', '.xml')
            if not lems_file.startswith('LEMS_'):
                lems_file = lems_file.replace('c302_', 'LEMS_c302_')
    
    print(f"Loading activity data from: {filename}")
    if lems_file:
        print(f"Using LEMS file for column names: {lems_file}")
    data = load_activity_data(filename, lems_file)
    
    print(f"Analyzing motor activity with pain injection at {pain_start_ms} ms...")
    results = analyze_motor_activity(data, pain_start_ms)
    
    if results:
        print_analysis(results)
        plot_activity(results)
    else:
        print("Analysis failed - check input file format")


if __name__ == "__main__":
    main()

