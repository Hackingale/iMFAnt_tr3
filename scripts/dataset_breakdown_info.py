#!/usr/bin/env python3
"""
Analyze regex datasets and their corresponding ANML automata to extract statistics.
"""

import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET


def count_states_transitions_from_anml(anml_file: str) -> Tuple[int, int]:
    """
    Count the number of states and transitions in an ANML file.
    Includes XML fixes for malformed ANML files (similar to SPARX parser).
    
    Returns:
        (num_states, num_transitions)
    """
    try:
        # Read the file content
        with open(anml_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Apply XML fixes for malformed ANML (from SPARX)
        content = re.sub(r'\s+/>', '/>', content)
        content = re.sub(r'=(\w+)([>\s])', r'="\1"\2', content)
        content = re.sub(r'<available-re=(\S+)', r'<available-re>\1</available-re>', content)
        content = re.sub(r'<activate-on-match element=(\d+)/>', r'<activate-on-match element="\1"/>', content)
        content = re.sub(r'"\s*/>\s*<', '"/>\n<', content)
        content = re.sub(r'<available-re="([^"]+)"/>', r'<available-re re="\1"/>', content)
        content = re.sub(r'<report-on-match reportcode="([^"]+)"/>', r'<report-on-match reportcode="\1"/>', content)
        
        # Parse the fixed XML
        root = ET.fromstring(content)
        
        # Count transitions (both regular and range elements)
        regular_transitions = root.findall('.//{*}state-transition-element')
        range_transitions = root.findall('.//{*}state-transition-range-element')
        num_transitions = len(regular_transitions) + len(range_transitions)
        
        # Collect all unique state IDs (both as source states and target states)
        unique_state_ids = set()
        
        # Process regular state-transition-elements
        for elem in regular_transitions:
            # Add the state ID from the element itself
            state_id = int(elem.get('id'))
            unique_state_ids.add(state_id)
            
            # Also check for states referenced in activate-on-match elements
            for activate in elem.findall('.//{*}activate-on-match'):
                target_element = activate.get('element')
                if target_element:
                    unique_state_ids.add(int(target_element))
        
        # Process state-transition-range-elements
        for elem in range_transitions:
            # Add the state ID from the element itself
            state_id = int(elem.get('id'))
            unique_state_ids.add(state_id)
            
            # Also check for states referenced in activate-on-match elements
            for activate in elem.findall('.//{*}activate-on-match'):
                target_element = activate.get('element')
                if target_element:
                    unique_state_ids.add(int(target_element))
        
        # Number of states is the count of unique state IDs
        num_states = len(unique_state_ids)
        
        return num_states, num_transitions
    except Exception as e:
        print(f"Error parsing {anml_file}: {e}", file=sys.stderr)
        return 0, 0


def analyze_anml_directory(dataset_dir: str) -> Tuple[int, int, int, float, float]:
    """
    Analyze all ANML files in a dataset directory.
    
    Returns:
        (total_states, total_transitions, num_automata, avg_states, avg_transitions)
    """
    dataset_path = Path(dataset_dir)
    
    if not dataset_path.exists():
        print(f"Directory not found: {dataset_dir}", file=sys.stderr)
        return 0, 0, 0, 0.0, 0.0
    
    total_states = 0
    total_transitions = 0
    num_automata = 0
    
    # Find all automaton*.anml files
    anml_files = sorted(dataset_path.glob("automaton*.anml"))
    
    for anml_file in anml_files:
        states, transitions = count_states_transitions_from_anml(str(anml_file))
        total_states += states
        total_transitions += transitions
        num_automata += 1
    
    # Calculate averages
    avg_states = total_states / num_automata if num_automata > 0 else 0.0
    avg_transitions = total_transitions / num_automata if num_automata > 0 else 0.0
    
    return total_states, total_transitions, num_automata, avg_states, avg_transitions


def count_character_classes(regex: str) -> int:
    """
    Count the number of character classes in a regex pattern.
    Character classes are patterns like [a-z], [efg], [^adf], etc.
    """
    # Match character classes: [...] including negated ones [^...]
    # We need to be careful with escaped brackets
    pattern = r'\[(?:[^\]\\]|\\.)*\]'
    matches = re.findall(pattern, regex)
    return len(matches)


def count_bounded_repetitions(regex: str) -> int:
    """
    Count bounded repetitions like {n}, {n,m}, {n,}
    """
    pattern = r'\{[0-9]+(?:,[0-9]*)?\}'
    matches = re.findall(pattern, regex)
    return len(matches)


def count_repetitions(regex: str) -> int:
    """
    Count *, +, and ? repetition operators
    """
    # Count non-escaped *, +, ?
    count = 0
    i = 0
    while i < len(regex):
        if regex[i] in ['*', '+', '?']:
            # Check if it's escaped
            num_backslashes = 0
            j = i - 1
            while j >= 0 and regex[j] == '\\':
                num_backslashes += 1
                j -= 1
            # If even number of backslashes (including 0), it's not escaped
            if num_backslashes % 2 == 0:
                count += 1
        i += 1
    return count


def count_wildcards(regex: str) -> int:
    """
    Count wildcard dots (.)
    """
    count = 0
    i = 0
    while i < len(regex):
        if regex[i] == '.':
            # Check if it's escaped
            num_backslashes = 0
            j = i - 1
            while j >= 0 and regex[j] == '\\':
                num_backslashes += 1
                j -= 1
            # If even number of backslashes (including 0), it's not escaped
            if num_backslashes % 2 == 0:
                count += 1
        i += 1
    return count


def count_anchors(regex: str) -> int:
    """
    Count anchoring symbols ^ and $
    """
    count = 0
    i = 0
    while i < len(regex):
        if regex[i] in ['^', '$']:
            # Check if it's escaped
            num_backslashes = 0
            j = i - 1
            while j >= 0 and regex[j] == '\\':
                num_backslashes += 1
                j -= 1
            # If even number of backslashes, it's not escaped
            if num_backslashes % 2 == 0:
                count += 1
        i += 1
    return count


def analyze_regex_file(regex_file: str) -> Dict[str, any]:
    """
    Analyze a file containing regex patterns.
    
    Returns dictionary with statistics.
    """
    try:
        with open(regex_file, 'r', encoding='utf-8', errors='ignore') as f:
            regexes = [line.strip() for line in f if line.strip()]
        
        num_regexes = len(regexes)
        total_cc = sum(count_character_classes(r) for r in regexes)
        total_bounded_rep = sum(count_bounded_repetitions(r) for r in regexes)
        total_rep = sum(count_repetitions(r) for r in regexes)
        total_wildcards = sum(count_wildcards(r) for r in regexes)
        total_anchors = sum(count_anchors(r) for r in regexes)
        
        return {
            'num_regexes': num_regexes,
            'total_cc': total_cc,
            'avg_cc': total_cc / num_regexes if num_regexes > 0 else 0.0,
            'total_bounded_rep': total_bounded_rep,
            'total_rep': total_rep,
            'total_wildcards': total_wildcards,
            'total_anchors': total_anchors
        }
    except Exception as e:
        print(f"Error reading regex file {regex_file}: {e}", file=sys.stderr)
        return {
            'num_regexes': 0,
            'total_cc': 0,
            'avg_cc': 0.0,
            'total_bounded_rep': 0,
            'total_rep': 0,
            'total_wildcards': 0,
            'total_anchors': 0
        }


def analyze_dataset(dataset_name: str, regex_file: str, anml_dir: str) -> Dict[str, any]:
    """
    Perform complete analysis of a dataset.
    """
    print(f"\nAnalyzing dataset: {dataset_name}")
    print(f"  Regex file: {regex_file}")
    print(f"  ANML directory: {anml_dir}")
    
    # Analyze regex patterns
    regex_stats = analyze_regex_file(regex_file)
    
    # Analyze ANML automata
    total_states, total_trans, num_auto, avg_states, avg_trans = analyze_anml_directory(anml_dir)
    
    results = {
        'dataset': dataset_name,
        'num_regexes': regex_stats['num_regexes'],
        'total_states': total_states,
        'total_transitions': total_trans,
        'total_cc': regex_stats['total_cc'],
        'avg_states': avg_states,
        'avg_transitions': avg_trans,
        'avg_cc': regex_stats['avg_cc'],
        'total_bounded_rep': regex_stats['total_bounded_rep'],
        'total_rep': regex_stats['total_rep'],
        'total_wildcards': regex_stats['total_wildcards'],
        'total_anchors': regex_stats['total_anchors']
    }
    
    return results


def print_latex_table(datasets_results: List[Dict[str, any]]):
    """
    Print results in LaTeX table format.
    """
    print("\n" + "="*80)
    print("LaTeX Table Output:")
    print("="*80)
    print()
    
    print(r"\begin{table}[htbp]")
    print(r"\centering")
    print(r"\caption{Dataset Statistics}")
    print(r"\label{tab:dataset_stats}")
    print(r"\begin{tabular}{lrrrrrrrr}")
    print(r"\toprule")
    print(r"Dataset & Num. REs & Tot. NS$^\dagger$ & Tot. NTS$^\ddagger$ & Tot. N CC$^\star$ & " + 
          r"Avg. NS$^\dagger$ & Avg. NTS$^\ddagger$ & Avg. LCC$^\S$ \\")
    print(r"\midrule")
    
    for res in datasets_results:
        print(f"{res['dataset']:15s} & "
              f"{res['num_regexes']:4d} & "
              f"{res['total_states']:6d} & "
              f"{res['total_transitions']:6d} & "
              f"{res['total_cc']:6d} & "
              f"{res['avg_states']:6.2f} & "
              f"{res['avg_transitions']:6.2f} & "
              f"{res['avg_cc']:5.2f} \\\\")
    
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table}")
    print()
    print(r"% Legend:")
    print(r"% $^\dagger$ NS: Number of States (without merging)")
    print(r"% $^\ddagger$ NTS: Number of Transitions (without merging)")
    print(r"% $^\star$ N CC: Number of Character Classes")
    print(r"% $^\S$ LCC: Length of Character Classes (average per automaton)")


def print_summary_table(datasets_results: List[Dict[str, any]]):
    """
    Print a human-readable summary table.
    """
    print("\n" + "="*80)
    print("Dataset Analysis Summary")
    print("="*80)
    
    header = f"{'Dataset':<15} {'REs':>6} {'States':>8} {'Trans':>8} {'CC':>6} " + \
             f"{'Avg St':>8} {'Avg Tr':>8} {'Avg CC':>8}"
    print(header)
    print("-" * len(header))
    
    for res in datasets_results:
        print(f"{res['dataset']:<15} "
              f"{res['num_regexes']:6d} "
              f"{res['total_states']:8d} "
              f"{res['total_transitions']:8d} "
              f"{res['total_cc']:6d} "
              f"{res['avg_states']:8.2f} "
              f"{res['avg_transitions']:8.2f} "
              f"{res['avg_cc']:8.2f}")
    
    print("\nAdditional Pattern Statistics:")
    print("-" * 80)
    for res in datasets_results:
        print(f"\n{res['dataset']}:")
        print(f"  Bounded repetitions {{n,m}}: {res['total_bounded_rep']}")
        print(f"  Repetitions (*, +, ?): {res['total_rep']}")
        print(f"  Wildcards (.): {res['total_wildcards']}")
        print(f"  Anchors (^, $): {res['total_anchors']}")


if __name__ == "__main__":
    # Define your datasets here
    datasets = [
        {
            'name': 'Dictionary',
            'regex_file': '../datasets/custom/dataset_dictionary.txt',
            'anml_dir': '../mfsa/dataset_dictionary_1'
        },
        {
            'name': 'Synthetic',
            'regex_file': '../datasets/custom/dataset_regexes_synth.txt',
            'anml_dir': '../mfsa/dataset_regexes_synth_1'
        },
        {
            'name': 'PowerEN0',
            'regex_file': '../datasets/custom/dataset_0_410.txt',
            'anml_dir': '../mfsa/dataset_0_410_1'
        },
        {
            'name': 'PowerEN1',
            'regex_file': '../datasets/custom/dataset_1_410.txt',
            'anml_dir': '../mfsa/dataset_1_410_1'
        },
        {
            'name': 'PowerEN2',
            'regex_file': '../datasets/custom/dataset_2_410.txt',
            'anml_dir': '../mfsa/dataset_2_410_1'
        },
        {
            'name': 'PowerEN3',
            'regex_file': '../datasets/custom/dataset_3_410.txt',
            'anml_dir': '../mfsa/dataset_3_410_1'
        },
        {
            'name': 'PowerEN4',
            'regex_file': '../datasets/custom/dataset_4_410.txt',
            'anml_dir': '../mfsa/dataset_4_410_1'
        },
        {
            'name': 'PowerEN5',
            'regex_file': '../datasets/custom/dataset_5_410.txt',
            'anml_dir': '../mfsa/dataset_5_410_1'
        },
        {
            'name': 'PowerEN6',
            'regex_file': '../datasets/custom/dataset_6_398.txt',
            'anml_dir': '../mfsa/dataset_6_398_1'
        }
    ]
    
    print("Dataset Analyzer")
    print("=" * 80)
    
    all_results = []
    
    for dataset in datasets:
        results = analyze_dataset(
            dataset['name'],
            dataset['regex_file'],
            dataset['anml_dir']
        )
        all_results.append(results)
    
    # Print results
    print_summary_table(all_results)
    print_latex_table(all_results)