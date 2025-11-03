# Model of happiness/pleasure induction in C. elegans worm
# This simulation induces positive states by stimulating dopamine-releasing neurons
# to simulate reward and happiness responses

# To run:
#          python c302_Happiness.py A   (uses parameters_A, requires jNeuroML to run)
# or
#          python c302_Happiness.py B   (uses parameters_B, requires jNeuroML built from the
#                                       experimental branches to run: 'python getNeuroML experimental'
#                                       see https://github.com/NeuroML/jNeuroML)

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
):
    ParameterisedModel = getattr(
        importlib.import_module("c302.parameters_%s" % parameter_set),
        "ParameterisedModel",
    )
    params = ParameterisedModel()

    # Include reward/reward pathway neurons as described in Key et al. (2023)
    # Based on the paper: When worms are on food, bacteria stimulate:
    # - NSM neurons: secrete serotonin (essential for flexible responses, acts on ASH)
    # - CEP neurons: dopaminergic mechanosensory neurons (dopamine acts on ASH)
    # These neuromodulators positively modulate the ASH/AWC-AIB-RIM-AVA circuit
    # Also include the core circuit neurons for complete simulation
    cells = ["NSML", "NSMR",  # Serotonin-releasing neurons (stimulated by bacteria)
             "CEPDL", "CEPDR", "CEPVL", "CEPVR",  # Dopamine-releasing neurons (stimulated by bacteria)
             "ASHL", "ASHR",  # ASH neurons have serotonin and dopamine receptors
             "AWCL", "AWCR",  # AWC neurons (food odorants dampen AWC activity)
             "AIBL", "AIBR",  # AIB interneurons integrate reward and aversive signals
             "RIML", "RIMR",  # RIM interneurons (modulatory)
             "AVAL", "AVAR"]  # AVA command interneurons
    cells_to_stimulate = []

    reference = "c302_%s_Happiness" % parameter_set

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

    # Induce happiness/reward by stimulating neurons activated when worms are on food
    # Based on Key et al. (2023): When on food, bacteria stimulate NSM (serotonin) 
    # and dopaminergic neurons (CEP), which positively modulate behavior
    happiness_start = "0ms"  # Start reward stimulation at the very beginning
    happiness_duration = "10000ms"  # Continue reward signals for the full simulation duration (10 seconds)
    reward_amplitude = "10pA"  # Moderate, pleasant stimulus

    # Only add reward inputs if network has been generated
    if nml_doc is not None:
        # Stimulate NSM neurons - secrete serotonin when stimulated by bacteria
        # Serotonin receptors on ASH are essential for flexible responses
        # When worms are on food, NSM secretes serotonin which hastens reversals
        c302.add_new_input(nml_doc, "NSML", happiness_start, happiness_duration, reward_amplitude, params)
        c302.add_new_input(nml_doc, "NSMR", happiness_start, happiness_duration, reward_amplitude, params)

        # Stimulate CEP neurons - dopaminergic mechanosensory neurons
        # Stimulated by bacteria, dopamine acts on ASH to quicken response when feeding
        # Dopamine-deficient worms have slowed responses
        c302.add_new_input(nml_doc, "CEPDL", happiness_start, happiness_duration, "8pA", params)
        c302.add_new_input(nml_doc, "CEPDR", happiness_start, happiness_duration, "8pA", params)
        c302.add_new_input(nml_doc, "CEPVL", happiness_start, happiness_duration, "8pA", params)
        c302.add_new_input(nml_doc, "CEPVR", happiness_start, happiness_duration, "8pA", params)

        # Modulate ASH neurons - have serotonin and dopamine receptors
        # When stimulated by serotonin/dopamine (on food), ASH response is quicker
        # This simulates the positive modulation when worms are rewarded
        c302.add_new_input(nml_doc, "ASHL", happiness_start, happiness_duration, "6pA", params)
        c302.add_new_input(nml_doc, "ASHR", happiness_start, happiness_duration, "6pA", params)

        # Modulate AWC neurons - food odorants dampen AWC tonic activity
        # When on food, reduced AWC activity hastens reversals and promotes forward locomotion
        # For reward simulation, we reduce stimulation to simulate dampened activity
        # (Note: In reality this would be inhibition, but we simulate it with lower amplitude)
        c302.add_new_input(nml_doc, "AWCL", happiness_start, happiness_duration, "3pA", params)
        c302.add_new_input(nml_doc, "AWCR", happiness_start, happiness_duration, "3pA", params)

        # Modulate AIB interneurons - integrate reward signals
        # When on food, serotonin inhibits AIB, causing quicker responses to aversive stimuli
        # For reward state, we simulate positive modulation
        c302.add_new_input(nml_doc, "AIBL", happiness_start, happiness_duration, "7pA", params)
        c302.add_new_input(nml_doc, "AIBR", happiness_start, happiness_duration, "7pA", params)

        # Modulate RIM and AVA - part of the reward-modulated circuit
        c302.add_new_input(nml_doc, "RIML", happiness_start, happiness_duration, "6pA", params)
        c302.add_new_input(nml_doc, "RIMR", happiness_start, happiness_duration, "6pA", params)
        c302.add_new_input(nml_doc, "AVAL", happiness_start, happiness_duration, "5pA", params)
        c302.add_new_input(nml_doc, "AVAR", happiness_start, happiness_duration, "5pA", params)

    # Write network file with dopamine inputs if network has been generated
    if nml_doc is not None:
        nml_file = target_directory + "/" + reference + ".net.nml"
        writers.NeuroMLWriter.write(
            nml_doc, nml_file
        )  # Write over network file written above...

        c302.print_("(Re)written network file to: " + nml_file)
        c302.print_("Reward/happiness stimulation applied to food-responsive neurons:")
        c302.print_("  - NSML/NSMR (serotonin-releasing): %s for %s starting at %s" 
                    % (reward_amplitude, happiness_duration, happiness_start))
        c302.print_("  - CEPDL/CEPDR/CEPVL/CEPVR (dopamine-releasing): 8pA for %s starting at %s" 
                    % (happiness_duration, happiness_start))
        c302.print_("  - ASHL/ASHR (modulated by serotonin/dopamine): 6pA for %s starting at %s" 
                    % (happiness_duration, happiness_start))
        c302.print_("  - AWCL/AWCR (dampened by food odorants): 3pA for %s starting at %s" 
                    % (happiness_duration, happiness_start))
        c302.print_("  - AIBL/AIBR (integrate reward signals): 7pA for %s starting at %s" 
                    % (happiness_duration, happiness_start))
        c302.print_("  - RIML/RIMR and AVAL/AVAR (reward-modulated circuit): 6pA/5pA for %s starting at %s" 
                    % (happiness_duration, happiness_start))
        c302.print_("This simulates the reward state when worms are on food (Key et al. 2023).")
        c302.print_("The worm will experience continuous reward signals and positive states throughout the simulation.")

    return cells, cells_to_stimulate, params, [], nml_doc


if __name__ == "__main__":
    parameter_set = sys.argv[1] if len(sys.argv) == 2 else "A"

    setup(parameter_set, generate=True)

