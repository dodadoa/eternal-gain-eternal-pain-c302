# Motor Neuron Activity Analysis

This guide explains how to extract and analyze motor neuron activity data to see if the nematode moves aggressively before and after pain injection.

## Overview

The enhanced pain model (`c302_EternalPainWithMotors.py`) includes motor neurons that drive forward and backward movement. By injecting pain after a delay, we can compare baseline motor activity (before pain) with pain-induced activity (after pain).

## Step-by-Step Instructions

### 1. Generate the Simulation Model

```bash
cd /home/dodadoa/giang/eternal-gain-eternal-pain/c302
python3 eternalpain/c302_EternalPainWithMotors.py A 2000
```

This creates:
- `examples/c302_A_EternalPainWithMotors.net.nml` (network file)
- `examples/LEMS_c302_A_EternalPainWithMotors.xml` (simulation file)

**Parameters:**
- `A`: Parameter set (can use `B`, `C`, etc.)
- `2000`: Pain injection delay in milliseconds (2 seconds baseline)

### 2. Run the Simulation

```bash
cd examples
pynml LEMS_c302_A_EternalPainWithMotors.xml
```

This will generate:
- `examples/c302_A_EternalPainWithMotors.dat` (raw neuron voltage data)

**Note:** This may take a few minutes depending on simulation duration.

### 3. Analyze Motor Neuron Activity

```bash
cd ..
python3 eternalpain/analyze_motor_activity.py examples/c302_A_EternalPainWithMotors.dat 2000
```

**Parameters:**
- First argument: Path to the .dat file
- Second argument: Pain injection time in milliseconds (should match delay from step 1)

The script will:
1. Extract column names from the LEMS XML file automatically
2. Identify forward motor neurons (VB, DB) and backward/reversal motor neurons (VD, DD)
3. Calculate mean activity before and after pain injection
4. Generate statistics and a visualization plot

### 4. Interpret the Results

The analysis will output:

**Forward Motor Neurons (VB, DB):**
- Before pain: Baseline forward locomotion activity
- After pain: Activity changes when pain is injected

**Backward/Reversal Motor Neurons (VD, DD):**
- Before pain: Minimal reversal activity
- After pain: **Should increase significantly** - this indicates aggressive avoidance behavior

**Key Metrics:**
- If backward motor activity increases significantly after pain → **Aggressive movement detected**
- The nematode is showing avoidance behavior (reversals) in response to pain

## Motor Neurons Included

- **Forward locomotion:** VB1-VB5, DB1-DB5
- **Backward/reversal:** VD1-VD5, DD1-DD5 (GABAergic)

## Output Files

- `motor_activity_analysis.png`: Plot showing motor activity over time with before/after comparison

## Troubleshooting

**If you see "Warning: No motor neurons found in data!":**
1. Make sure the simulation has been run (step 2)
2. Check that the .dat file exists in the examples directory
3. The script automatically looks for the LEMS XML file - make sure it's in the same location

**The script automatically:**
- Extracts column names from the LEMS XML file (dat files have no headers)
- Handles column naming with `_v` suffix (e.g., `VB1_v`, `VD1_v`)
- Finds both forward (VB, DB) and backward (VD, DD) motor neurons

