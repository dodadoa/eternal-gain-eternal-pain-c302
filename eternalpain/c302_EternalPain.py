# Model of pain induction in C. elegans worm with crucial motor neuron monitoring
# This simulation induces persistent pain by stimulating nociceptive neurons (ASH)
# after a delay to capture motor neuron activity before and after pain injection
# Crucial motor neurons included for observation and plotting: VB2/VB3, VD2/VD3, DD2/DD3, DB2/DB3

# To run:
#          python c302_EternalPainWithMotors.py A   (uses parameters_A, requires jNeuroML to run)
# or
#          python c302_EternalPainWithMotors.py B   (uses parameters_B, requires jNeuroML built from the
#                                         experimental branches to run: 'python getNeuroML experimental'
#                                         see https://github.com/NeuroML/jNeuroML)

import c302

import neuroml.writers as writers

import sys
import importlib


def setup(
    parameter_set,
    generate=False,
    duration=10000,  # Long simulation duration (10 seconds)
    dt=0.05,
    target_directory="examples",
    data_reader=c302.DEFAULT_DATA_READER,
    param_overrides={},
    config_param_overrides={},
    verbose=True,
    pain_start_delay=500,  # Delay before pain injection (ms) - early pain injection
):
    ParameterisedModel = getattr(
        importlib.import_module("c302.parameters_%s" % parameter_set),
        "ParameterisedModel",
    )
    params = ParameterisedModel()

    # Include the neural circuit for motivational trade-offs as described in Key et al. (2023)
    # - ASH: Primary nociceptive neurons that detect harmful stimuli
    # - AWC: Modulatory chemosensory neurons (tonically active, prolong reversals)
    # - AIB: Layer 1 interneurons that integrate ASH and AWC inputs
    # - RIM: Layer 2 interneurons (modulatory, secrete tyramine)
    # - AVA: Command interneurons (output to motor neurons for reversals)
    
    # Add crucial motor neurons to monitor behavioral output:
    # - VB: Forward locomotion motor neurons (crucial: VB2, VB3)
    # - VD: Backward/reversal motor neurons (crucial: VD2, VD3)
    # - DD: Backward/reversal motor neurons (GABAergic) (crucial: DD2, DD3)
    # - DB: Additional forward motor neurons (crucial: DB2, DB3)
    pain_circuit_cells = ["ASHL", "ASHR", "AWCL", "AWCR", "AIBL", "AIBR", "RIML", "RIMR", "AVAL", "AVAR"]
    # Only include crucial motor cells for observation and plotting
    motor_cells = ["VB2", "VB3",  # Forward locomotion (crucial representatives)
                   "VD2", "VD3",  # Backward/reversal (crucial representatives)
                   "DD2", "DD3",  # Backward/reversal GABAergic (crucial representatives)
                   "DB2", "DB3"]  # Additional forward (crucial representatives)
    
    cells = pain_circuit_cells + motor_cells
    cells_to_stimulate = []

    reference = "c302_%s_EternalPain" % parameter_set

    nml_doc = None

    if generate:
        nml_doc = c302.generate(
            reference,
            params,
            cells=cells,
            cells_to_stimulate=cells_to_stimulate,
            duration=duration,
            dt=dt,
            target_directory=target_directory,
            param_overrides=param_overrides,
            verbose=verbose,
            data_reader=data_reader,
        )

    # Induce pain by stimulating ASH nociceptive neurons
    # Start pain stimulation AFTER a delay to capture baseline motor activity
    pain_start = "%sms" % pain_start_delay  # Start pain stimulation after delay
    pain_duration = "%sms" % (duration - pain_start_delay)  # Continue pain for remainder of simulation
    pain_amplitude = "15pA"  # Strong pain stimulus (increased amplitude for more intense pain)

    # Only add pain inputs if network has been generated
    if nml_doc is not None:
        # Stimulate ASH neurons - primary nociceptive neurons (necessary for aversive responses)
        # ASH detects harmful stimuli like octanol and initiates avoidance behavior
        c302.add_new_input(nml_doc, "ASHL", pain_start, pain_duration, pain_amplitude, params)
        c302.add_new_input(nml_doc, "ASHR", pain_start, pain_duration, pain_amplitude, params)

        # Stimulate AWC neurons - modulatory chemosensory neurons
        # AWC is tonically active and prolongs reversals; food odorants dampen AWC activity
        # For pain simulation, we stimulate AWC to enhance aversive responses
        c302.add_new_input(nml_doc, "AWCL", pain_start, pain_duration, "10pA", params)
        c302.add_new_input(nml_doc, "AWCR", pain_start, pain_duration, "10pA", params)

        # Stimulate AIB interneurons - Layer 1 interneurons that integrate ASH and AWC
        # AIB is both necessary and sufficient for modulating aversive responses
        # Ablation of AIB causes hungry worms to rapidly stop (like feeding worms)
        c302.add_new_input(nml_doc, "AIBL", pain_start, pain_duration, "12pA", params)
        c302.add_new_input(nml_doc, "AIBR", pain_start, pain_duration, "12pA", params)

        # Stimulate RIM interneurons - Layer 2 modulatory interneurons
        # RIM secretes tyramine and modulates the AIB-RIM-AVA network activity
        # RIM weakens correlated states and facilitates context-specific responses
        c302.add_new_input(nml_doc, "RIML", pain_start, pain_duration, "10pA", params)
        c302.add_new_input(nml_doc, "RIMR", pain_start, pain_duration, "10pA", params)

        # Stimulate AVA command interneurons - Layer 3 command interneurons
        # AVA directly outputs to motor neurons to drive reversals
        # Ablation or silencing of AVA prevents reversals
        c302.add_new_input(nml_doc, "AVAL", pain_start, pain_duration, "8pA", params)
        c302.add_new_input(nml_doc, "AVAR", pain_start, pain_duration, "8pA", params)

    # Write network file with pain inputs if network has been generated
    if nml_doc is not None:
        nml_file = target_directory + "/" + reference + ".net.nml"
        writers.NeuroMLWriter.write(
            nml_doc, nml_file
        )  # Write over network file written above...

        c302.print_("(Re)written network file to: " + nml_file)
        c302.print_("=" * 70)
        c302.print_("Pain stimulation applied to ASH/AWC-AIB-RIM-AVA circuit:")
        c302.print_("  - ASHL/ASHR (primary nociceptive): %s for %s starting at %s" 
                    % (pain_amplitude, pain_duration, pain_start))
        c302.print_("  - AWCL/AWCR (modulatory chemosensory): 10pA for %s starting at %s" 
                    % (pain_duration, pain_start))
        c302.print_("  - AIBL/AIBR (integrating interneurons): 12pA for %s starting at %s" 
                    % (pain_duration, pain_start))
        c302.print_("  - RIML/RIMR (modulatory interneurons): 10pA for %s starting at %s" 
                    % (pain_duration, pain_start))
        c302.print_("  - AVAL/AVAR (command interneurons): 8pA for %s starting at %s" 
                    % (pain_duration, pain_start))
        c302.print_("=" * 70)
        c302.print_("Crucial motor neurons included for monitoring and plotting:")
        c302.print_("  - Forward locomotion: VB2, VB3, DB2, DB3")
        c302.print_("  - Backward/reversal: VD2, VD3, DD2, DD3")
        c302.print_("=" * 70)
        c302.print_("TIMELINE:")
        c302.print_("  - 0ms to %sms: BASELINE (no pain - observe normal motor activity)" % pain_start_delay)
        c302.print_("  - %sms: PAIN INJECTION BEGINS" % pain_start_delay)
        c302.print_("  - %sms to %sms: PAIN PERIOD (observe aggressive/reversal behavior)" 
                    % (pain_start_delay, duration))
        c302.print_("=" * 70)
        c302.print_("Motor neuron activity will be output in the generated LEMS file.")
        c302.print_("Look for activity data in: %s/%s.activity.dat" % (target_directory, reference))

    return cells, cells_to_stimulate, params, [], nml_doc


if __name__ == "__main__":
    parameter_set = sys.argv[1] if len(sys.argv) == 2 else "A"
    pain_delay = int(sys.argv[2]) if len(sys.argv) >= 3 else 500  # Default 500ms delay (early pain)

    setup(parameter_set, generate=True, pain_start_delay=pain_delay)

