import csv
from typing import List, Tuple, Dict
from collections import defaultdict

# Transition class with rules of the Turing machine
class TMTransition:
    def __init__(self, current_state: str, read_symbol: str, next_state: str, write_symbol: str, move_direction: str):
        self.current_state = current_state
        self.read_symbol = read_symbol
        self.next_state = next_state
        self.write_symbol = write_symbol
        self.move_direction = move_direction

# Configuration class stores the configuration of the Turing machine at any point in time
class TMConfiguration:
    def __init__(self, left_tape: str, state: str, current_symbol: str, right_tape: str):
        self.left_tape = left_tape
        self.state = state
        self.current_symbol = current_symbol
        self.right_tape = right_tape

    # String representation of the Turing machine configuration
    def __str__(self):
        return f"[{self.left_tape}], ({self.state}), [{self.current_symbol}{self.right_tape}]"

# Simulator class for the Non-deterministic Turing Machine (NTM)
class TuringMachineSimulator:
    def __init__(self, machine_config_file: str):
        self.transition_rules = defaultdict(list)
        self.initial_state = ""
        self.accept_state = ""
        self.reject_state = "reject"
        self.load_machine_configuration(machine_config_file)

    # Loads the Turing machine's state and transition information from a CSV file
    def load_machine_configuration(self, filename: str):
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            self.machine_name = next(reader)[0]
            next(reader)
            next(reader)  
            next(reader) 
            self.initial_state = next(reader)[0]
            self.accept_state = next(reader)[0]
            self.reject_state = next(reader)[0]
            
            for row in reader:
                if len(row) != 5:
                    continue
                state_from, read_symbol, state_to, write_symbol, move_dir = row
                self.transition_rules[(state_from, read_symbol)].append(
                    TMTransition(state_from, read_symbol, state_to, write_symbol, move_dir)
                )

    # Simulates the NTM with a given input string and maximum number of steps
    def simulate_machine(self, input_string: str, max_steps: int = 1000) -> Tuple[bool, int, List[List[TMConfiguration]], int]:
        initial_config = TMConfiguration(
            "", self.initial_state, input_string[0] if input_string else "_", input_string[1:]
        )
        
        config_tree = [[initial_config]]
        total_steps = 0
        
        for step in range(max_steps):
            current_level = config_tree[-1]
            next_level = []
            
            for config in current_level:
                if config.state == self.accept_state:
                    return True, step, config_tree, total_steps
                if config.state == self.reject_state:
                    continue
                
                transitions = self.transition_rules.get((config.state, config.current_symbol), [])
                if not transitions:
                    next_level.append(TMConfiguration(
                        config.left_tape, self.reject_state, 
                        config.current_symbol, config.right_tape
                    ))
                    continue
                
                for transition in transitions:
                    new_config = self.apply_transition(config, transition)
                    next_level.append(new_config)
                    total_steps += 1
            
            if not next_level or all(c.state == self.reject_state for c in next_level):
                return False, step, config_tree, total_steps
                
            config_tree.append(next_level)
            
        return False, max_steps, config_tree, total_steps

    # Applies a transition to a configuration and returns the updated configuration
    def apply_transition(self, config: TMConfiguration, transition: TMTransition) -> TMConfiguration:
        new_left_tape = config.left_tape
        new_right_tape = config.right_tape
        new_current_symbol = transition.write_symbol

        if transition.move_direction == 'L':
            if new_left_tape:
                new_current_symbol = new_left_tape[-1]
                new_left_tape = new_left_tape[:-1]
            else:
                new_current_symbol = '_'
            new_right_tape = transition.write_symbol + config.right_tape
        else:
            new_left_tape = config.left_tape + transition.write_symbol
            if new_right_tape:
                new_current_symbol = new_right_tape[0]
                new_right_tape = new_right_tape[1:]
            else:
                new_current_symbol = '_'

        return TMConfiguration(new_left_tape, transition.next_state, new_current_symbol, new_right_tape)

    # Prints a summary of the configuration tree exploration
    def display_summary(self, tree: List[List[TMConfiguration]]):
        print("Configuration Tree Exploration Report")

        for level, configs in enumerate(tree):
            print(f"\nLevel {level}:")
            config_count = len(configs)
            unique_states = set(config.state for config in configs)
            print(f"  - Total configurations: {config_count}")
            print(f"  - Unique states reached: {', '.join(unique_states)}")

# Prints the detailed configuration tree for a specific input string
def display_detailed_configuration_tree(simulator, input_string, max_steps=1000):
    """
    Display a summary view of the configuration tree showing all explored alternatives
    """
    print(f"\nNTM: {simulator.machine_name}")
    print(f"Input String: '{input_string}'")

    # Run simulation
    accepted, steps, tree, total_steps = simulator.simulate_machine(input_string, max_steps)

    # Calculate nondeterminism
    def calculate_nondeterminism(tree):
        if not tree or len(tree) <= 1:
            return 1.0

        # Count configurations at each level that have multiple next configurations
        total_branches = 0
        total_configs = 0

        for level in range(len(tree) - 1):
            current_level = tree[level]
            next_level = tree[level + 1]

            total_configs += len(current_level)

            # Count branches by looking at how many configurations in current level 
            # generate different configurations in the next level
            unique_parent_states = set()
            for config in current_level:
                if config.state not in unique_parent_states and len(
                    [c for c in next_level if c.state != config.state]
                ) > 1:
                    total_branches += 1
                    unique_parent_states.add(config.state)

        # Avoid division by zero
        if total_configs == 0:
            return 1.0

        return max(1.0, total_branches / total_configs)

    nondeterminism = calculate_nondeterminism(tree)

    # Display configuration exploration summary
    simulator.display_summary(tree)

    # Result and summary
    print(f"\nSimulation Result: {'ACCEPTED' if accepted else 'REJECTED'}")
    print(f"Tree Depth: {len(tree)} levels")
    print(f"Total Transitions Explored: {total_steps}")
    print(f"Nondeterminism Metric: {nondeterminism:.2f}")

    # Provide context-specific comment
    if nondeterminism == 1.0:
        comment = "Computation was deterministic"
    elif nondeterminism < 1.5:
        comment = "Slight nondeterministic behavior observed"
    elif nondeterminism < 3.0:
        comment = "Moderate nondeterministic exploration"
    else:
        comment = "Highly nondeterministic computation with extensive alternative paths"

    print(f"Analysis Comment: {comment}")

# Run comprehensive tests for the Non-deterministic Turing Machine (NTM) with multiple input strings
def run_machine_tests(machine_file, test_inputs):
    """
    Run a series of tests on the NTM with a set of input strings
    """
    simulator = TuringMachineSimulator(machine_file)

    print(f"\nTesting NTM: {simulator.machine_name}")

    for input_str in test_inputs:
        display_detailed_configuration_tree(simulator, input_str)

# Test the a+ machine with various inputs
test_inputs_aplus = ["", "a", "aa", "aaa", "aaaa", "aaaaa", "b"]
run_machine_tests("a_plus.csv", test_inputs_aplus)
