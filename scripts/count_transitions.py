#!/usr/env python3
"""
ANML Transition Counter Script
Author: Alessandro Marina
Purpose: Count state transitions in ANML files for compressed vs uncompressed datasets
"""

import os
import re
from pathlib import Path

def fix_anml_xml(content):
    """Fix ANML XML structure to make it parseable."""
    # ANML files may have issues with XML declaration or namespace
    # Add XML declaration if missing
    if not content.strip().startswith('<?xml'):
        content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
    
    # Fix common ANML namespace issues
    # Replace anml namespace with a simpler structure for parsing
    content = re.sub(r'<automata-network[^>]*>', '<automata-network>', content)
    
    return content

def count_transitions_in_file(filepath):
    """Count transitions in a single ANML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix XML structure
        content = fix_anml_xml(content)
        
        # Count state-transition-element
        transition_element_count = len(re.findall(r'<state-transition-element\s+id', content))
        
        # Count state-transition-range-element
        transition_range_count = len(re.findall(r'<state-transition-range-element', content))
        
        total_transitions = transition_element_count + transition_range_count
        
        return total_transitions, transition_element_count, transition_range_count
        
    except Exception as e:
        print(f"  ⚠️ Error reading {filepath}: {e}")
        return 0, 0, 0

def count_transitions_in_directory(directory):
    """Count all transitions in all ANML files in a directory."""
    total_transitions = 0
    total_element = 0
    total_range = 0
    file_count = 0
    
    # Find all .anml files
    anml_files = list(Path(directory).glob('automaton*.anml'))
    
    if not anml_files:
        print(f"  ⚠️ No ANML files found in {directory}")
        return 0, 0, 0, 0
    
    for anml_file in sorted(anml_files):
        trans, elem, rang = count_transitions_in_file(anml_file)
        total_transitions += trans
        total_element += elem
        total_range += rang
        file_count += 1
        print(f"    • {anml_file.name}: {trans:,} transitions ({elem:,} element + {rang:,} range)")
    
    return total_transitions, total_element, total_range, file_count

def analyze_dataset(base_path, dataset_name, compressed_suffix, uncompressed_suffix):
    """Analyze both compressed and uncompressed versions of a dataset."""
    
    print(f"\n{'='*80}")
    print(f"Processing: {dataset_name}")
    print(f"{'='*80}")
    
    # Compressed version
    compressed_dir = Path(base_path) / f"{dataset_name}_{compressed_suffix}"
    print(f"\n  Compressed ({compressed_dir.name}):")
    
    if compressed_dir.exists():
        comp_trans, comp_elem, comp_range, comp_files = count_transitions_in_directory(compressed_dir)
        print(f"  ✓ Total: {comp_trans:,} transitions in {comp_files} files")
    else:
        print(f"  ⚠️ Directory not found: {compressed_dir}")
        comp_trans, comp_elem, comp_range, comp_files = 0, 0, 0, 0
    
    # Uncompressed version
    uncompressed_dir = Path(base_path) / f"{dataset_name}_{uncompressed_suffix}"
    print(f"\n  Uncompressed ({uncompressed_dir.name}):")
    
    if uncompressed_dir.exists():
        uncomp_trans, uncomp_elem, uncomp_range, uncomp_files = count_transitions_in_directory(uncompressed_dir)
        print(f"  ✓ Total: {uncomp_trans:,} transitions in {uncomp_files} files")
    else:
        print(f"  ⚠️ Directory not found: {uncompressed_dir}")
        uncomp_trans, uncomp_elem, uncomp_range, uncomp_files = 0, 0, 0, 0
    
    # Calculate reduction
    if uncomp_trans > 0:
        reduction_pct = ((uncomp_trans - comp_trans) / uncomp_trans) * 100
        print(f"\n  📊 Transition Reduction: {reduction_pct:.1f}% ({uncomp_trans - comp_trans:,} transitions saved)")
    else:
        reduction_pct = 0
    
    return {
        'dataset': dataset_name,
        'compressed_transitions': comp_trans,
        'compressed_element': comp_elem,
        'compressed_range': comp_range,
        'compressed_files': comp_files,
        'uncompressed_transitions': uncomp_trans,
        'uncompressed_element': uncomp_elem,
        'uncompressed_range': uncomp_range,
        'uncompressed_files': uncomp_files,
        'reduction_abs': uncomp_trans - comp_trans,
        'reduction_pct': reduction_pct
    }

def generate_text_table(results, output_file='transition_count_summary.txt'):
    """Generate text-based summary table."""
    
    with open(output_file, 'w') as f:
        # Write header
        line = "="*150
        f.write(line + "\n")
        f.write("TRANSITION COUNT SUMMARY: COMPRESSED VS UNCOMPRESSED\n")
        f.write(line + "\n\n")
        
        # Column headers
        header = f"{'Dataset':<20} {'Comp Trans':>12} {'Comp Elem':>12} {'Comp Range':>12} " \
                 f"{'Uncomp Trans':>14} {'Uncomp Elem':>12} {'Uncomp Range':>13} " \
                 f"{'Reduction':>12} {'Reduction %':>12}\n"
        f.write(header)
        f.write("-"*150 + "\n")
        
        # Data rows
        for result in results:
            row = f"{result['dataset']:<20} " \
                  f"{result['compressed_transitions']:>12,} " \
                  f"{result['compressed_element']:>12,} " \
                  f"{result['compressed_range']:>12,} " \
                  f"{result['uncompressed_transitions']:>14,} " \
                  f"{result['uncompressed_element']:>12,} " \
                  f"{result['uncompressed_range']:>13,} " \
                  f"{result['reduction_abs']:>12,} " \
                  f"{result['reduction_pct']:>11.2f}%\n"
            f.write(row)
        
        f.write("-"*150 + "\n")
        
        # Summary statistics
        total_comp = sum(r['compressed_transitions'] for r in results)
        total_uncomp = sum(r['uncompressed_transitions'] for r in results)
        total_reduction = sum(r['reduction_abs'] for r in results)
        valid_results = [r for r in results if r['uncompressed_transitions'] > 0]
        avg_reduction_pct = sum(r['reduction_pct'] for r in valid_results) / len(valid_results) if valid_results else 0
        
        summary = f"{'TOTAL/AVERAGE':<20} " \
                  f"{total_comp:>12,} " \
                  f"{'':>12} {'':>12} " \
                  f"{total_uncomp:>14,} " \
                  f"{'':>12} {'':>13} " \
                  f"{total_reduction:>12,} " \
                  f"{avg_reduction_pct:>11.2f}%\n"
        f.write(summary)
        f.write(line + "\n\n")
        
        # Additional statistics
        f.write("SUMMARY STATISTICS:\n")
        f.write(f"  Total Compressed Transitions:   {total_comp:,}\n")
        f.write(f"  Total Uncompressed Transitions: {total_uncomp:,}\n")
        f.write(f"  Total Reduction:                {total_reduction:,} transitions\n")
        f.write(f"  Average Reduction:              {avg_reduction_pct:.2f}%\n")
        f.write(line + "\n")
    
    # Also print to console
    print("\n" + "="*150)
    print("TRANSITION COUNT SUMMARY: COMPRESSED VS UNCOMPRESSED")
    print("="*150 + "\n")
    
    print(f"{'Dataset':<20} {'Comp Trans':>12} {'Comp Elem':>12} {'Comp Range':>12} "
          f"{'Uncomp Trans':>14} {'Uncomp Elem':>12} {'Uncomp Range':>13} "
          f"{'Reduction':>12} {'Reduction %':>12}")
    print("-"*150)
    
    for result in results:
        print(f"{result['dataset']:<20} "
              f"{result['compressed_transitions']:>12,} "
              f"{result['compressed_element']:>12,} "
              f"{result['compressed_range']:>12,} "
              f"{result['uncompressed_transitions']:>14,} "
              f"{result['uncompressed_element']:>12,} "
              f"{result['uncompressed_range']:>13,} "
              f"{result['reduction_abs']:>12,} "
              f"{result['reduction_pct']:>11.2f}%")
    
    print("-"*150)
    print(f"{'TOTAL/AVERAGE':<20} "
          f"{total_comp:>12,} "
          f"{'':>12} {'':>12} "
          f"{total_uncomp:>14,} "
          f"{'':>12} {'':>13} "
          f"{total_reduction:>12,} "
          f"{avg_reduction_pct:>11.2f}%")
    print("="*150 + "\n")
    
    print("SUMMARY STATISTICS:")
    print(f"  Total Compressed Transitions:   {total_comp:,}")
    print(f"  Total Uncompressed Transitions: {total_uncomp:,}")
    print(f"  Total Reduction:                {total_reduction:,} transitions")
    print(f"  Average Reduction:              {avg_reduction_pct:.2f}%")
    print("="*150 + "\n")
    
    print(f"✓ Text table saved: {output_file}")

def generate_csv_table(results, output_file='transition_count_summary.csv'):
    """Generate CSV summary table."""
    
    with open(output_file, 'w') as f:
        # Header
        f.write("Dataset,Compressed Transitions,Compressed Element,Compressed Range,Compressed Files,"
                "Uncompressed Transitions,Uncompressed Element,Uncompressed Range,Uncompressed Files,"
                "Reduction Absolute,Reduction Percentage\n")
        
        # Data rows
        for result in results:
            f.write(f"{result['dataset']},"
                   f"{result['compressed_transitions']},"
                   f"{result['compressed_element']},"
                   f"{result['compressed_range']},"
                   f"{result['compressed_files']},"
                   f"{result['uncompressed_transitions']},"
                   f"{result['uncompressed_element']},"
                   f"{result['uncompressed_range']},"
                   f"{result['uncompressed_files']},"
                   f"{result['reduction_abs']},"
                   f"{result['reduction_pct']:.2f}\n")
    
    print(f"✓ CSV table saved: {output_file}")

def generate_latex_table(results, output_file='transition_count_table.tex'):
    """Generate LaTeX table for thesis."""
    
    latex_content = r"""
\begin{table}[htbp]
\centering
\caption{State Transition Count: Compressed vs Uncompressed MFSA}
\label{tab:transition_count}
\resizebox{\textwidth}{!}{
\begin{tabular}{l|rrr|rrr|rr}
\hline
\textbf{Dataset} & \multicolumn{3}{c|}{\textbf{Compressed}} & \multicolumn{3}{c|}{\textbf{Uncompressed}} & \multicolumn{2}{c}{\textbf{Reduction}} \\
 & Total & Element & Range & Total & Element & Range & Absolute & \% \\
\hline
"""
    
    for result in results:
        latex_content += f"{result['dataset'].replace('_', '\\_')} & "
        latex_content += f"{result['compressed_transitions']:,} & "
        latex_content += f"{result['compressed_element']:,} & "
        latex_content += f"{result['compressed_range']:,} & "
        latex_content += f"{result['uncompressed_transitions']:,} & "
        latex_content += f"{result['uncompressed_element']:,} & "
        latex_content += f"{result['uncompressed_range']:,} & "
        latex_content += f"{result['reduction_abs']:,} & "
        latex_content += f"{result['reduction_pct']:.1f}\\% \\\\\n"
    
    # Add summary row
    total_comp = sum(r['compressed_transitions'] for r in results)
    total_uncomp = sum(r['uncompressed_transitions'] for r in results)
    total_reduction = sum(r['reduction_abs'] for r in results)
    valid_results = [r for r in results if r['uncompressed_transitions'] > 0]
    avg_reduction_pct = sum(r['reduction_pct'] for r in valid_results) / len(valid_results) if valid_results else 0
    
    latex_content += r"\hline" + "\n"
    latex_content += f"\\textbf{{Total/Average}} & "
    latex_content += f"{total_comp:,} & - & - & "
    latex_content += f"{total_uncomp:,} & - & - & "
    latex_content += f"{total_reduction:,} & "
    latex_content += f"{avg_reduction_pct:.1f}\\% \\\\\n"
    
    latex_content += r"""\hline
\end{tabular}
}
\end{table}
"""
    
    with open(output_file, 'w') as f:
        f.write(latex_content)
    
    print(f"✓ LaTeX table saved: {output_file}")

def main():
    """Main execution function."""
    
    print("\n" + "="*120)
    print("ANML TRANSITION COUNTER - COMPRESSED VS UNCOMPRESSED")
    print("="*120)
    
    # Base path for MFSA files
    base_path = Path('../mfsa')
    
    if not base_path.exists():
        print(f"\n⚠️ ERROR: Base path {base_path} does not exist!")
        print("Please run this script from a directory where '../mfsa' is accessible.")
        return
    
    results = []
    
    # PowerEN datasets (0-6, all use 410 except dataset_6 which uses 398)
    for i in range(7):
        if i == 6:
            dataset_name = f"dataset_6_398"
        else:
            dataset_name = f"dataset_{i}_410"
        
        result = analyze_dataset(base_path, dataset_name, '0', '1')
        results.append(result)
    
    # Synth dataset
    result = analyze_dataset(base_path, 'dataset_regexes_synth', '0', '1')
    results.append(result)
    
    # Dictionary dataset
    result = analyze_dataset(base_path, 'dataset_dictionary', '0', '1')
    results.append(result)
    
    # Generate summary tables
    print("\n" + "="*120)
    print("GENERATING SUMMARY TABLES")
    print("="*120 + "\n")
    
    generate_text_table(results)
    generate_csv_table(results)
    generate_latex_table(results)
    
    print("\n" + "="*120)
    print("✓ Analysis complete!")
    print("="*120 + "\n")

if __name__ == '__main__':
    main()

def fix_anml_xml(content):
    """Fix ANML XML structure to make it parseable."""
    # ANML files may have issues with XML declaration or namespace
    # Add XML declaration if missing
    if not content.strip().startswith('<?xml'):
        content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
    
    # Fix common ANML namespace issues
    # Replace anml namespace with a simpler structure for parsing
    content = re.sub(r'<automata-network[^>]*>', '<automata-network>', content)
    
    return content

def count_transitions_in_file(filepath):
    """Count transitions in a single ANML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix XML structure
        content = fix_anml_xml(content)
        
        # Count state-transition-element
        transition_element_count = len(re.findall(r'<state-transition-element\s+id', content))
        
        # Count state-transition-range-element
        transition_range_count = len(re.findall(r'<state-transition-range-element', content))
        
        total_transitions = transition_element_count + transition_range_count
        
        return total_transitions, transition_element_count, transition_range_count
        
    except Exception as e:
        print(f"  ⚠️ Error reading {filepath}: {e}")
        return 0, 0, 0

def count_transitions_in_directory(directory):
    """Count all transitions in all ANML files in a directory."""
    total_transitions = 0
    total_element = 0
    total_range = 0
    file_count = 0
    
    # Find all .anml files
    anml_files = list(Path(directory).glob('automaton*.anml'))
    
    if not anml_files:
        print(f"  ⚠️ No ANML files found in {directory}")
        return 0, 0, 0, 0
    
    for anml_file in sorted(anml_files):
        trans, elem, rang = count_transitions_in_file(anml_file)
        total_transitions += trans
        total_element += elem
        total_range += rang
        file_count += 1
        print(f"    • {anml_file.name}: {trans:,} transitions ({elem:,} element + {rang:,} range)")
    
    return total_transitions, total_element, total_range, file_count

def analyze_dataset(base_path, dataset_name, compressed_suffix, uncompressed_suffix):
    """Analyze both compressed and uncompressed versions of a dataset."""
    
    print(f"\n{'='*80}")
    print(f"Processing: {dataset_name}")
    print(f"{'='*80}")
    
    # Compressed version
    compressed_dir = Path(base_path) / f"{dataset_name}_{compressed_suffix}"
    print(f"\n  Compressed ({compressed_dir.name}):")
    
    if compressed_dir.exists():
        comp_trans, comp_elem, comp_range, comp_files = count_transitions_in_directory(compressed_dir)
        print(f"  ✓ Total: {comp_trans:,} transitions in {comp_files} files")
    else:
        print(f"  ⚠️ Directory not found: {compressed_dir}")
        comp_trans, comp_elem, comp_range, comp_files = 0, 0, 0, 0
    
    # Uncompressed version
    uncompressed_dir = Path(base_path) / f"{dataset_name}_{uncompressed_suffix}"
    print(f"\n  Uncompressed ({uncompressed_dir.name}):")
    
    if uncompressed_dir.exists():
        uncomp_trans, uncomp_elem, uncomp_range, uncomp_files = count_transitions_in_directory(uncompressed_dir)
        print(f"  ✓ Total: {uncomp_trans:,} transitions in {uncomp_files} files")
    else:
        print(f"  ⚠️ Directory not found: {uncompressed_dir}")
        uncomp_trans, uncomp_elem, uncomp_range, uncomp_files = 0, 0, 0, 0
    
    # Calculate reduction
    if uncomp_trans > 0:
        reduction_pct = ((uncomp_trans - comp_trans) / uncomp_trans) * 100
        print(f"\n  📊 Transition Reduction: {reduction_pct:.1f}% ({uncomp_trans - comp_trans:,} transitions saved)")
    else:
        reduction_pct = 0
    
    return {
        'dataset': dataset_name,
        'compressed_transitions': comp_trans,
        'compressed_element': comp_elem,
        'compressed_range': comp_range,
        'compressed_files': comp_files,
        'uncompressed_transitions': uncomp_trans,
        'uncompressed_element': uncomp_elem,
        'uncompressed_range': uncomp_range,
        'uncompressed_files': uncomp_files,
        'reduction_abs': uncomp_trans - comp_trans,
        'reduction_pct': reduction_pct
    }



def main():
    """Main execution function."""
    
    print("\n" + "="*120)
    print("ANML TRANSITION COUNTER - COMPRESSED VS UNCOMPRESSED")
    print("="*120)
    
    # Base path for MFSA files
    base_path = Path('../mfsa')
    
    if not base_path.exists():
        print(f"\n⚠️ ERROR: Base path {base_path} does not exist!")
        print("Please run this script from a directory where '../mfsa' is accessible.")
        return
    
    results = []
    
    # PowerEN datasets (0-6, all use 410 except dataset_6 which uses 398)
    for i in range(7):
        if i == 6:
            dataset_name = f"dataset_6_398"
        else:
            dataset_name = f"dataset_{i}_410"
        
        result = analyze_dataset(base_path, dataset_name, '0', '1')
        results.append(result)
    
    # Synth dataset
    result = analyze_dataset(base_path, 'dataset_regexes_synth', '0', '1')
    results.append(result)
    
    # Dictionary dataset
    result = analyze_dataset(base_path, 'dataset_dictionary', '0', '1')
    results.append(result)
    
    # Generate summary tables
    print("\n" + "="*120)
    print("GENERATING SUMMARY TABLES")
    print("="*120 + "\n")
    
    generate_text_table(results)
    generate_csv_table(results)
    generate_latex_table(results)
    
    print("\n" + "="*120)
    print("✓ Analysis complete!")
    print("="*120 + "\n")

if __name__ == '__main__':
    main()