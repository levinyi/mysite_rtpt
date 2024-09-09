from itertools import combinations

def find_enzyme_sites(dna_sequence, enzymes_info, enzyme_input, circular=True):
    """
    This function finds enzyme cutting sites in a DNA sequence and calculates fragment lengths.
    
    :param dna_sequence: str, DNA sequence to be analyzed
    :param enzymes_info: list of dicts, each containing enzyme information with keys:
                         - 'Enzyme': Name of the enzyme
                         - 'Site_NT': Recognition sequence of the enzyme
                         - 'Cutting_Site_Left(bp)': Cutting position from the left end of the recognition sequence
                         - 'Cutting_Site_Right(bp)': Cutting position from the right end of the recognition sequence
    :param enzyme_input: str or list of str, Names of enzymes to be considered for cutting.
                         If a single enzyme name is provided, use only that enzyme.
                         If a list of enzyme names is provided, use all enzymes in combinations.
    :param circular: bool, True if DNA is circular, False if DNA is linear
    :return: dict, with enzyme combination as keys and a list of fragments as values,
             where each fragment is represented as a tuple: (fragment_sequence, fragment_length)
    """
    
    # Ensure enzyme input is a list
    if isinstance(enzyme_input, str):
        enzyme_input = [enzyme_input]

    # Generate combinations of the selected enzymes (excluding single enzyme combinations if multiple enzymes are provided)
    enzyme_combinations = list(combinations(enzyme_input, len(enzyme_input))) if len(enzyme_input) > 1 else [tuple(enzyme_input)]
    
    result = {}  # Dictionary to store results

    for enzyme_combo in enzyme_combinations:
        cut_positions = set()  # Use a set to collect unique cut positions
        combo_name = " + ".join(enzyme_combo)
        
        # Find cutting sites for each enzyme in the combination
        for enzyme_name in enzyme_combo:
            enzyme = next((enzyme for enzyme in enzymes_info if enzyme['Enzyme'] == enzyme_name), None)
            if not enzyme:
                continue

            recognition_seq = enzyme['Site_NT']
            cut_left = enzyme['Cutting_Site_Left(bp)']
            search_pos = 0

            # Find all occurrences of the recognition sequence
            while (pos := dna_sequence.find(recognition_seq, search_pos)) != -1:
                cut_site = pos + cut_left
                cut_positions.add(cut_site)
                search_pos = pos + 1
        
        cut_positions = sorted(cut_positions)
        fragments = []

        if len(cut_positions) == 0:
            # No cuts, the whole sequence is one fragment
            fragment_seq = dna_sequence
            fragment_length = len(dna_sequence)
            fragments.append((fragment_seq, fragment_length))
        else:
            # Handle the first fragment from start to the first cut position
            if not circular:
                first_fragment_seq = dna_sequence[:cut_positions[0]]
                first_fragment_length = len(first_fragment_seq)
                fragments.append((first_fragment_seq, first_fragment_length))

            # Calculate fragment sequences and lengths between cut positions
            for i in range(len(cut_positions)):
                if i == len(cut_positions) - 1:
                    if circular:
                        # If circular, connect the end of the sequence back to the start
                        fragment_seq = dna_sequence[cut_positions[i]:] + dna_sequence[:cut_positions[0]]
                        fragment_length = len(fragment_seq)
                    else:
                        fragment_seq = dna_sequence[cut_positions[i]:]
                        fragment_length = len(fragment_seq)
                else:
                    fragment_seq = dna_sequence[cut_positions[i]:cut_positions[i + 1]]
                    fragment_length = len(fragment_seq)
                
                fragments.append((fragment_seq, fragment_length))

        # Store fragments info for this combination
        result[combo_name] = fragments

    return result

if __name__ == "__main__":

    # Example usage
    enzymes_info = [
        {'Enzyme': 'BamHI', 'Site_NT': 'GGATCC', 'Cutting_Site_Left(bp)': 1, 'Cutting_Site_Right(bp)': 5},
        {'Enzyme': 'EcoRV', 'Site_NT': 'GATATC', 'Cutting_Site_Left(bp)': 3, 'Cutting_Site_Right(bp)': 3},
        {'Enzyme': 'PstI', 'Site_NT': 'CTGCAG', 'Cutting_Site_Left(bp)': 5, 'Cutting_Site_Right(bp)': 1},
        {'Enzyme': 'PvuII', 'Site_NT': 'CAGCTG', 'Cutting_Site_Left(bp)': 3, 'Cutting_Site_Right(bp)': 3}
    ]

    dna_sequence = "ATGATGGATTTGTCGCCAAACAATCAGATCGAGGACAGAAAACCCATCCTAACCGCCGACGGCCTGGTTCAGACTTCGAACTCCCCCTTCGAGCCGACCATATCGCAGGAGACGCAAACATCCAACGGAATCGGTGGCCAGTGCCATCTGACGGTTGACCAGTTGGACATTGAGATTCTGCCGATAATCTACGACATTGTGCGCTGCGTGGAAAAGGATCCTCTGGAGAACGCCGTTAAGCTGCGCGAGTCCCAGGATTGCAACCACAAGATCTTTGAACTTCAAAAACGCTTCGAATCGGCACGCGAGCAAATCCGCCAGCTCCCCGGGATCGATTTCAATAAGGAGGAGCAGCAACAGAGACTGGAACTACTGCGAAATCAGCTGAAGCTTAAGCAGCAGCTAATTCGCAAATACAAGGACACAGAGTTCTAGGGTACCGGATCTTTGTGAAGGAACCTTACTTCTGTGGTGTGACATAATTGGACAAACTACCTACAGAGATTTAAAGCTCTAAGGTAAATATAAAATTTTTAAGTGTATAATGTGTTAAACTACTGATTCTAATTGTTTGTGTATTTTAGATTCCAACCTATGGAACTGATGAATGGGAGCAGTGGTGGAATGCCTTTAATGAGGAAAACCTGTTTTGCTCAGAAGAAATGCCATCTAGTGATGATGAGGCTACTGCTGACTCTCAACATTCTACTCCTCCAAAAAAGAAGAGAAAGGTAGAAGACCCCAAGGACTTTCCTTCAGAATTGCTAAGTTTTTTGAGTCATGCTGTGTTTAGTAATAGAACTCTTGCTTGCTTTGCTATTTACACCACAAAGGAAAAAGCTGCACTGCTATACAAGAAAATTATGGAAAAATATTTGATGTATAGTGCCTTGACTAGAGATCATAATCAGCCATACCACATTTGTAGAGGTTTTACTTGCTTTAAAAAACCTCCCACACCTCCCCCTGAACCTGAAACATAAAATGAATGCAATTGTTGTTGTTAACTTGTTTATTGCAGCTTATAATGGTTACAAATAAAGCAATAGCATCACAAATTTCACAAATAAAGCATTTTTTTCACTGCATTCTAGTTGTGGTTTGTCCAAACTCATCAATGTATCTTATCATGTCTGGATCTTGGCCACGTAATAAGTGTGCGTTGAATTTATTCGCAAAAACATTGCATATTTTCGGCAAAGTAAAATTTTGTTGCATACCTTATCAAAAAATAAGTGCTGCATACTTTTTAGAGAAACCAAATAATTTTTTATTGCATACCCGTTTTTAATAAAATACATTGCATACCCTCTTTTAATAAAAAATATTGCATACTTTGACGAAACAAATTTTCGTTGCATACCCAATAAAAGATTATTATATTGCATACCCGTTTTTAATAAAATACATTGCATACCCTCTTTTAATAAAAAATATTGCATACGTTGACGAAACAAATTTTCGTTGCATACCCAATAAAAGATTATTATATTGCATACCTTTTCTTGCCATACCATTTAGCCGATCAATTGTGCTCGGCAACAGTATATTTGTGGTGTGCCAACCAACAACGGATCCACTAGTGTCGACGATGTAGGTCACGGTCTCGAAGCCGCGGTGCGGGTGCCAGGGCGTGCCCTTGGGCTCCCCGGGCGCGTACTCCACCTCACCCATCTGGTCCATCATGATGAACGGGTCGAGGTGGCGGTAGTTGATCCCGGCGAACGCGCGGCGCACCGGGAAGCCCTCGCCCTCGAAACCGCTGGGCGCGGTGGTCACGGTGAGCACGGGACGTGCGACGGCGTCGGCGGGTGCGGATACGCGGGGCAGCGTCAGCGGGTTCTCGACGGTCACGGCGGGCATGTCGACACTAGTTCTAGCCAGCTTTTGTTCCCTTTAGTGAGGGTTAATTTCGAGCTTGGCGTAATCATGGTCATAGCTGTTTCCTGTGTGAAATTGTTATCCGCTCACAATTCCACACAACATACGAGCCGGAAGCATAAAGTGTAAAGCCTGGGGTGCCTAATGAGTGAGCTAACTCACATTAATTGCGTTGCGCTCACTGCCCGCTTTCCAGTCGGGAAACCTGTCGTGCCAGCTGCATTAATGAATCGGCCAACGCGCGGGGAGAGGCGGTTTGCGTATTGGGCGCTCTTCCGCTTCCTCGCTCACTGACTCGCTGCGCTCGGTCGTTCGGCTGCGGCGAGCGGTATCAGCTCACTCAAAGGCGGTAATACGGTTATCCACAGAATCAGGGGATAACGCAGGAAAGAACATGTGAGCAAAAGGCCAGCAAAAGGCCAGGAACCGTAAAAAGGCCGCGTTGCTGGCGTTTTTCCATAGGCTCCGCCCCCCTGACGAGCATCACAAAAATCGACGCTCAAGTCAGAGGTGGCGAAACCCGACAGGACTATAAAGATACCAGGCGTTTCCCCCTGGAAGCTCCCTCGTGCGCTCTCCTGTTCCGACCCTGCCGCTTACCGGATACCTGTCCGCCTTTCTCCCTTCGGGAAGCGTGGCGCTTTCTCATAGCTCACGCTGTAGGTATCTCAGTTCGGTGTAGGTCGTTCGCTCCAAGCTGGGCTGTGTGCACGAACCCCCCGTTCAGCCCGACCGCTGCGCCTTATCCGGTAACTATCGTCTTGAGTCCAACCCGGTAAGACACGACTTATCGCCACTGGCAGCAGCCACTGGTAACAGGATTAGCAGAGCGAGGTATGTAGGCGGTGCTACAGAGTTCTTGAAGTGGTGGCCTAACTACGGCTACACTAGAAGAACAGTATTTGGTATCTGCGCTCTGCTGAAGCCAGTTACCTTCGGAAAAAGAGTTGGTAGCTCTTGATCCGGCAAACAAACCACCGCTGGTAGCGGTGGTTTTTTTGTTTGCAAGCAGCAGATTACGCGCAGAAAAAAAGGATCTCAAGAAGATCCTTTGATCTTTTCTACGGGGTCTGACGCTCAGTGGAACGAAAACTCACGTTAAGGGATTTTGGTCATGAGATTATCAAAAAGGATCTTCACCTAGATCCTTTTAAATTAAAAATGAAGTTTTAAATCAATCTAAAGTATATATGAGTAAACTTGGTCTGACAGTTACCAATGCTTAATCAGTGAGGCACCTATCTCAGCGATCTGTCTATTTCGTTCATCCATAGTTGCCTGACTCCCCGTCGTGTAGATAACTACGATACGGGAGGGCTTACCATCTGGCCCCAGTGCTGCAATGATACCGCGAGACCCACGCTCACCGGCTCCAGATTTATCAGCAATAAACCAGCCAGCCGGAAGGGCCGAGCGCAGAAGTGGTCCTGCAACTTTATCCGCCTCCATCCAGTCTATTAATTGTTGCCGGGAAGCTAGAGTAAGTAGTTCGCCAGTTAATAGTTTGCGCAACGTTGTTGCCATTGCTACAGGCATCGTGGTGTCACGCTCGTCGTTTGGTATGGCTTCATTCAGCTCCGGTTCCCAACGATCAAGGCGAGTTACATGATCCCCCATGTTGTGCAAAAAAGCGGTTAGCTCCTTCGGTCCTCCGATCGTTGTCAGAAGTAAGTTGGCCGCAGTGTTATCACTCATGGTTATGGCAGCACTGCATAATTCTCTTACTGTCATGCCATCCGTAAGATGCTTTTCTGTGACTGGTGAGTACTCAACCAAGTCATTCTGAGAATAGTGTATGCGGCGACCGAGTTGCTCTTGCCCGGCGTCAATACGGGATAATACCGCGCCACATAGCAGAACTTTAAAAGTGCTCATCATTGGAAAACGTTCTTCGGGGCGAAAACTCTCAAGGATCTTACCGCTGTTGAGATCCAGTTCGATGTAACCCACTCGTGCACCCAACTGATCTTCAGCATCTTTTACTTTCACCAGCGTTTCTGGGTGAGCAAAAACAGGAAGGCAAAATGCCGCAAAAAAGGGAATAAGGGCGACACGGAAATGTTGAATACTCATACTCTTCCTTTTTCAATATTATTGAAGCATTTATCAGGGTTATTGTCTCATGAGCGGATACATATTTGAATGTATTTAGAAAAATAAACAAATAGGGGTTCCGCGCACATTTCCCCGAAAAGTGCCACCTAAATTGTAAGCGTTAATATTTTGTTAAAATTCGCGTTAAATTTTTGTTAAATCAGCTCATTTTTTAACCAATAGGCCGAAATCGGCAAAATCCCTTATAAATCAAAAGAATAGACCGAGATAGGGTTGAGTGTTGTTCCAGTTTGGAACAAGAGTCCACTATTAAAGAACGTGGACTCCAACGTCAAAGGGCGAAAAACCGTCTATCAGGGCGATGGCCCACTACGTGAACCATCACCCTAATCAAGTTTTTTGGGGTCGAGGTGCCGTAAAGCACTAAATCGGAACCCTAAAGGGAGCCCCCGATTTAGAGCTTGACGGGGAAAGCCGGCGAACGTGGCGAGAAAGGAAGGGAAGAAAGCGAAAGGAGCGGGCGCTAGGGCGCTGGCAAGTGTAGCGGTCACGCTGCGCGTAACCACCACACCCGCCGCGCTTAATGCGCCGCTACAGGGCGCGTCCCATTCGCCATTCAGGCTGCGCAACTGTTGGGAAGGGCGATCGGTGCGGGCCTCTTCGCTATTACGCCAGCTGGCGAAAGGGGGATGTGCTGCAAGGCGATTAAGTTGGGTAACGCCAGGGTTTTCCCAGTCACGACGTTGTAAAACGACGGCCAGTGAATTGTAATACGACTCACTATAGGGCGAATTGGGTACGTACCGGGCCCCTAGTATGTATGTAAGTTAATAAAACCCATTTTTGCGGAAAGTAGATAAAAAAAACATTTTTTTTTTTTACTGCACTGGATATCATTGAACTTATCTGATCAGTTTTAAATTTACTTCGATCCAAGGGTATTTGATGTACCAGGTTCTTTCGATTACCTCTCACTCAAAATGACATTCCACTCAAAGTCAGCGCTGTTTGCCTCCTTCTCTGTCCACAGAAATATCGCCGTCTCTTTCGCCGCTGCGTCCGCTATCTCTTTCGCCACCGTTTGTAGCGTTACGTAGCGTCAATGTCCGCCTTCAGTTGCATTTTGTCAGCGGTTTCGTGACGAAGCTCCAAGCGGTTTACGCCATCAATTAAACACAAAGTGCTGTGCCAAAACTCCTCTCGCTTCTTATTTTTGTTTGTTTTTTGAGTGATTGGGGTGGTGATTGGTTTTGGGTGGGTAAGCAGGGGAAAGTGTGAAAAATCCCGGCAATGGGCCAAGAGGATCAGGAGCTATTAATTCGCGGAGGCAGCAAACACCCATCTGCCGAGCATCTGAACAATGTGAGTAGTACATGTGCATACATCTTAAGTTCACTTGATCTATAGGAACTGCGATTGCAACATCAAATTGTCTGCGGCGTGAGAACTGCGACCCACAAAAATCCCAAACCGCAATTGCACAAACAAATAGTGACACGAAACAGATTATTCTGGTAGCTGTTCTCGCTATATAAGACAATTTTTGAGATCATATCATGATCAAGACATCTAAAGGCATTCATTTTCGACTATATTCTTTTTTACAAAAAATATAACAACCAGATATTTTAAGCTGATCCTAGATGCACAAAAAATAAATAAAAGTATAAACCTACTTCGTAGGATACTTCGGGGTACTTTTTGTTCGGGGTTAGATGAGCATAACGCTTGTAGTTGATATTTGAGATCCCCTATCATTGCAGGGTGACAGCGGAGCGGCTTCGCAGAGCTGCATTAACCAGGGCTTCGGGCAGGCCAAAAACTACGGCACGCTCCGGCCACCCAGTCCGCCGGAGGACTCCGGTTCAGGGAGCGGCCAACTAGCCGAGAACCTCACCTATGCCTGGCACAATATGGACATCTTTGGGGCGGTCAATCAGCCGGGCTCCGGATGGCGGCAGCTGGTCAACCGGACACGCGGACTATTCTGCAACGAGCGACACATACCGGCGCCCAGGAAACATTTGCTCAAGAACGGTGAGTTTCTATTCGCAGTCGGCTGATCTGTGTGAAATCTTAATAAAGGGTCCAATTACCAATTTGAAACTCAGTTTGCGGCGTGGCCTATCCGGGCGAACTTTTGGCCGTGATGGGCAGTTCCGGTGCCGGAAAGACGACCCTGCTGAATGCCCTTGCCTTTCGATCGCCGCAGGGCATCCAAGTATCGCCATCCGGGATGCGACTGCTCAATGGCCAACCTGTGGACGCCAAGGAGATGCAGGCCAGGTGCGCCTATGTCCAGCAGGATGACCTCTTTATCGGCTCCCTAACGGCCAGGGAACACCTGATTTTCCAGGCCATGGTGCGGATGCCACGACATCTGACCTATCGGCAGCGAGTGGCCCGCGTGGATCAGGTGATCCAGGAGCTTTCGCTCAGCAAATGTCAGCACACGATCATCGGTGTGCCCGGCAGGGTGAAAGGTCTGTCCGGCGGAGAAAGGAAGCGTCTGGCATTCGCCTCCGAGGCACTAACCGATCCGCCGCTTCTGATCTGCGATGAGCCCACCTCCGGACTGGACTCATTTACCGCCCACAGCGTCGTCCAGGTGCTGAAGAAGCTGTCGCAGAAGGGCAAGACCGTCATCCTGACCATTCATCAGCCGTCTTCCGAGCTGTTTGAGCTCTTTGACAAGATCCTTCTGATGGCCGAGGGCAGGGTAGCTTTCTTGGGCACTCCCAGCGAAGCCGTCGACTTCTTTTCCTAGTGAGTTCGATGTGTTTATTAAGGGTATCTAGCATTACATTACATCTCAACTCCTATCCAGCGTGGGTGCCCAGTGTCCTACCAACTACAATCCGGCGGACTTTTACGTACAGGTGTTGGCCGTTGTGCCCGGACGGGAGATCGAGTCCCGTGATCGGATCGCCAAGATATGCGACAATTTTGCTATTAGCAAAGTAGCCCGGGATATGGAGCAGTTGTTGGCCACCAAAAATTTGGAGAAGCCACTGGAGCAGCCGGAGAATGGGTACACCTACAAGGCCACCTGGTTCATGCAGTTCCGGGCGGTCCTGTGGCGATCCTGGCTGTCGGTGCTCAAGGAACCACTCCTCGTAAAAGTGCGACTTATTCAGACAACGGTGAGTGGTTCCAGTGGAAACAAATGATATAACGCTTACAATTCTTGGAAACAAATTCGCTAGATTTTAGTTAGAATTGCCTGATTCCACACCCTTCTTAGTTTTTTTCAATGAGATGTATAGTTTATAGTTTTGCAGAAAATAAATAAATTTCATTTAACTCGCGAACATGTTGAAGATATGAATATTAATGAGATGCGAGTAACATTTTAATTTGCAGATGGTTGCCATCTTGATTGGCCTCATCTTTTTGGGCCAACAACTCACGCAAGTGGGCGTGATGAATATCAACGGAGCCATCTTCCTCTTCCTGACCAACATGACCTTTCAAAACGTCTTTGCCACGATAAATGTAAGTCTTGTTTAGAATACATTTGCATATTAATAATTTACTAACTTTCTAATGAATCGATTCGATTTAGGTGTTCACCTCAGAGCTGCCAGTTTTTATGAGGGAGGCCCGAAGTCGACTTTATCGCTGTGACACATACTTTCTGGGCAAAACGATTGCCGAATTACCGCTTTTTCTCACAGTGCCACTGGTCTTCACGGCGATTGCCTATCCGATGATCGGACTGCGGGCCGGAGTGCTGCACTTCTTCAACTGCCTGGCGCTGGTCACTCTGGTGGCCAATGTGTCAACGTCCTTCGGATATCTAATATCCTGCGCCAGCTCCTCGACCTCGATGGCGCTGTCTGTGGGTCCGCCGGTTATCATACCATTCCTGCTCTTTGGCGGCTTCTTCTTGAACTCGGGCTCGGTGCCAGTATACCTCAAATGGTTGTCGTACCTCTCATGGTTCCGTTACGCCAACGAGGGTCTGCTGATTAACCAATGGGCGGACGTGGAGCCGGGCGAAATTAGCTGCACATCGTCGAACACCACGTGCCCCAGTTCGGGCAAGGTCATCCTGGAGACGCTTAACTTCTCCGCCGCCGATCTGCCGCTGGACTACGTGGGTCTGGCCATTCTCATCGTGAGCTTCCGGGTGCTCGCATATCTGGCTCTAAGACTTCGGGCCCGACGCAAGGAGTAGCCGACATATATCCGAAATAACTGCTTGTTTTTTTTTTTTACCATTATTACCATCGTGTTTACTGTTTATTGCCCCCTCAAAAAGCTAATGTAATTATATTTGTGCCAATAAAAACAAGATATGACCTATAGAATACAAGTATTTCCCCTTCGAACATCCCCACAAGTAGACTTTGGATTTGTCTTCTAACCAAAAGACTTACACACCTGCATACCTTACATCAAAAACTCGTTTATCGCTACATAAAACACCGGGATATATTTTTTATATACATACTTTTCAAATCGCGCGCCCTCTTCATAATTCACCTCCACCACACCACGTTTCGTAGTTGCTCTTTCGCTGTCTCCCACCCGCTCTCCGCAACACATTCACCTTTTGTTCGACGACCTTGGAGCGACTGTCGTTAGTTCCGCGCGATTCGGTTCGCTCAAATGGTTCCGAGTGGTTCATTTCGTCTCAATAGAAATTAGTAATAAATATTTGTATGTACAATTTATTTGCTCCAATATATTTGTATATATTTCCCTCACAGCTATATTTATTCTAATTTAATATTATGACTTTTTAAGGTAATTTTTTGTGACCTGTTCGGAGTGATTAGCGTTACAATTTGAACTGAAAGTGACATCCAGTGTTTGTTCCTTGTGTAGATGCATCTCAAAAAAATGGTGGGCATAATAGTGTTGTTTATATATATCAAAAATAACAACTATAATAATAAGAATACATTTAATTTAGAAAATGCTTGGATTTCACTGGAACTAGGCTAGCATAACTTCGTATAATGTATGCTATACGAAGTTATGCTAGCGGATCCTGGCCACGTAATAAGTGTGCGTTGAATTTATTCGCAAAAACATTGCATATTTTCGGCAAAGTAAAATTTTGTTGCATACCTTATCAAAAAATAAGTGCTGCATACTTTTTAGAGAAACCAAATAATTTTTTATTGCATACCCGTTTTTAATAAAATACATTGCATACCCTCTTTTAATAAAAAATATTGCATACTTTGACGAAACAAATTTTCGTTGCATACCCAATAAAAGATTATTATATTGCATACCCGTTTTTAATAAAATACATTGCATACCCTCTTTTAATAAAAAATATTGCATACGTTGACGAAACAAATTTTCGTTGCATACCCAATAAAAGATTATTATATTGCATACCTTTTCTTGCCATACCATTTAGCCGATCAATTGTGCTCGGCAACAGTATATTTGTGGTGTGCCAACCAACAACAGATCCAAGCTGGCCGCGGCTCGATCCGCTTGCATGCCTGCAGGTCGGAGTACTGTCCTCCGAGCGGAGTACTGTCCTCCGAGCGGAGTACTGTCCTCCGAGCGGAGTACTGTCCTCCGAGCGGAGTACTGTCCTCCGAGCGGAAGCTTGCATGCCTGCAGGTCGGAGTACTGTCCTCCGAGCGGAGTACTGTCCTCCGAGCGGAGTACTGTCCTCCGAGCGGAGTACTGTCCTCCGAGCGGAGTACTGTCCTCCGAGCGGAGACTCTAGCGAGCGCCGGAGTATAAATAGAGGCGCTTCGTCTACGGAGCGACAATTCAATTCAAACAAGCAAAGTGAACACGTCGCTAAGCGAAAGCTAAGCAAATAAACAAGCGCAGCTGAACAAGCTAAACAATCTGCAGTAAAGTGCAAGTTAAAGTGAATCAATTAAAAGTAACCAGCAACCAAGTAAATCAACTGCAACTACTGAAATCTGCCAAGAAGTAATTATTGAATACAAGAAGAGAACTCTGAATAGGGAATTGGGAATTCAAAAATCAAC"

    circular = True
    # Example with a single enzyme
    fragment_lengths_single = find_enzyme_sites(dna_sequence, enzymes_info, enzyme_input='BamHI', circular=circular)
    print("Single enzyme BamHI:")
    for enzyme, fragments in fragment_lengths_single.items():
        for fragment in fragments:
            print(f"Enzyme: {enzyme}, Fragment Length: {fragment[1]}")

    circular = False
    # Example with a single enzyme
    fragment_lengths_single = find_enzyme_sites(dna_sequence, enzymes_info, enzyme_input='BamHI', circular=circular)
    print("Single enzyme BamHI:")
    for enzyme, fragments in fragment_lengths_single.items():
        for fragment in fragments:
            print(f"Enzyme: {enzyme}, Fragment Length: {fragment[1]}")

    # for enzymes, lengths in fragment_lengths_single.items():
    #     print(f"Enzymes: {enzymes}, Fragment Lengths: {lengths}")

    # # Example with multiple enzymes
    # fragment_lengths_multiple = find_enzyme_sites(dna_sequence, enzymes_info, enzyme_input=['BamHI', 'EcoRV'], circular=circular)
    # print("\nMultiple enzymes BamHI and EcoRV:")
    # for enzymes, lengths in fragment_lengths_multiple.items():
    #     print(f"Enzymes: {enzymes}, Fragment Lengths: {lengths}")