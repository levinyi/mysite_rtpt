import re


def calculate_gc_content(sequence):
    '''
    Calculate the GC content of a DNA sequence.
    '''
    sequence = sequence.upper().replace(" ", "")
    gc_count = sequence.count('G') + sequence.count('C')
    gc_content = (gc_count / len(sequence)) * 100
    return round(gc_content, 2)


def reverse_complement(sequence):
    '''
    Get the reverse complement of a DNA sequence.
    '''
    sequence = sequence.upper().replace(" ", "")
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    return ''.join(complement[base] for base in reversed(sequence))


def is_homopolymer(unit):
    '''Check if a given DNA sequence is a homopolymer (consisting of only one type of base).'''
    return len(set(unit)) == 1

def build_suffix_array(s):
    """Build a suffix array for the string `s`."""
    return sorted(range(len(s)), key=lambda k: s[k:])

def find_lcp(s, sa):
    """Find the longest common prefix (LCP) array for `s` using the suffix array `sa`."""
    n = len(s)
    lcp = [0] * n
    rank = [0] * n
    for i in range(n):
        rank[sa[i]] = i
    k = 0
    for i in range(n):
        if rank[i] == n - 1:  # 末尾
            k = 0
            continue
        j = sa[rank[i] + 1]
        while i + k < n and j + k < n and s[i+k] == s[j+k]:
            k += 1
        lcp[rank[i]] = k
        if k:
            k -= 1
    return lcp

def check_tandem_repeats(sequence, min_unit=3, min_copies=3):
    '''
    Identify and return non-overlapping tandem repeats in a DNA sequence with at least the specified minimum unit length and copies.
    Each tandem repeat's details including penalty score, sequence, start and end index, length, and GC content are returned.

    Args:
        sequence (str): The DNA sequence to be checked.
        min_unit (int): The minimum length of the repeat unit (default 3).
        min_copies (int): The minimum number of copies in the repeat (default 3).

    Returns:
        list: A list of dictionaries containing details about each tandem repeat found.
    '''
    temp_results = []
    n = len(sequence)

    # Loop through each possible unit length from min_unit to n // min_copies
    for unit in range(min_unit, n // min_copies + 1):
        checked_indices = set()
        for i in range(n - unit * min_copies + 1):
            if i in checked_indices:
                continue
            repeat_unit = sequence[i:i + unit]
            if is_homopolymer(repeat_unit):  # Skip homopolymer units
                continue
            count = 1
            while sequence[i + unit * count:i + unit * (count + 1)] == repeat_unit:
                count += 1
            
            if count >= min_copies:
                actual_repeat = repeat_unit * count
                penalty_score = (len(actual_repeat) - 15) / 2 if len(actual_repeat) > 15 else 0

                result = {
                    'seqType': 'tandem_repeats',
                    'sequence': actual_repeat,
                    'penalty_score': penalty_score,
                    'length': len(actual_repeat),
                    'gc_content': calculate_gc_content(actual_repeat),
                    'positions': [(i, i + len(actual_repeat) - 1)]
                }

                # Update checked indices
                checked_indices.update(range(i, i + len(actual_repeat)))

                # Add to temp results
                temp_results.append(result)

    # Merge positions of identical sequences
    final_results = {}
    for res in temp_results:
        seq = res['sequence']
        if seq in final_results:
            final_results[seq]['positions'].extend(res['positions'])
        else:
            final_results[seq] = res

    # Convert the results to list and merge positions for each sequence
    merged_results = list(final_results.values())
    for result in merged_results:
        sorted_positions = sorted(result['positions'])
        merged_positions = [sorted_positions[0]]

        for current in sorted_positions[1:]:
            last = merged_positions[-1]
            if current[0] <= last[1] + 1:
                merged_positions[-1] = (last[0], max(last[1], current[1]))
            else:
                merged_positions.append(current)
        
        result['positions'] = merged_positions

    return merged_results

# checked
def check_long_repeats(sequence, min_length=16):
    '''
    Check for all long repeats in a DNA sequence that are at least `min_length` characters long.
    Ensure that only the longest repeats that contain shorter repeats are retained,
    and their positions are consolidated into one record without duplicates.
    
    Args:
        sequence (str): The DNA sequence to check.
        min_length (int): The minimum length of the long repeat (default 16).
    
    Returns:
        list: A list of dictionaries with the detected long repeats, their consolidated positions, length, GC content, and penalty.
    '''
    results = []
    n = len(sequence)
    
    # Identify all potential repeats of length >= min_length
    for i in range(n - min_length + 1):
        for length in range(min_length, n - i + 1):
            repeat = sequence[i:i+length]
            start_search = i + length
            occurrences = []
            while start_search <= n - length:
                if sequence[start_search:start_search + length] == repeat:
                    occurrences.append(start_search)
                    start_search += length
                else:
                    start_search += 1
            
            if len(occurrences) > 0:
                occurrences.insert(0, i)  # Include the original occurrence
                results.append({
                    'seqType': 'long_repeats',
                    'sequence': repeat,
                    'length': length,
                    'gc_content': calculate_gc_content(repeat),
                    'occurrences': occurrences,
                    'penalty_score': (length - (min_length-1)) / 2
                })
                
    # Filter results to keep only the longest non-contained sequences
    final_results = {}
    for result in results:
        is_contained = any(
            other['sequence'].find(result['sequence']) != -1 and other['length'] > result['length']
            for other in results if other['sequence'] != result['sequence'])
        if not is_contained:
            sequence_key = result['sequence']
            if sequence_key not in final_results:
                final_results[sequence_key] = {
                    'seqType': 'long_repeats',
                    'sequence': sequence_key,
                    'length': result['length'],
                    'gc_content': result['gc_content'],
                    'penalty_score': result['penalty_score'],
                    'positions': [(start, start + result['length'] - 1) for start in set(result['occurrences'])]
                }
            else:
                # Ensure no duplicate positions are added
                current_positions = {pos for pos in final_results[sequence_key]['positions']}
                new_positions = {(start, start + result['length'] - 1) for start in result['occurrences']}
                final_results[sequence_key]['positions'] = list(current_positions.union(new_positions))

    return list(final_results.values())


# checked
def check_homopolymers(sequence, min_length=7):
    '''
    Identify and list all homopolymers in a DNA sequence that are at least `min_length` characters long.
    A homopolymer is a sequence of identical bases in a row, e.g., AAAAAAA, TTTTTTT, CCCCCCC, GGGGGGG.
    The function also calculates a penalty score for each homopolymer based on its length and consolidates all positions.

    Args:
        sequence (str): The DNA sequence to check.
        min_length (int): The minimum length of the homopolymer (default 7).

    Returns:
        list: A list of dictionaries with each homopolymer, its penalty score, length, and consolidated positions.
    '''
    results = {}
    n = len(sequence)
    i = 0
    while i < n:
        j = i + 1
        while j < n and sequence[j] == sequence[i]:
            j += 1
        length = j - i
        if length >= min_length:
            penalty_score = length if length < 11 else length * 10
            homopolymer = sequence[i:j]
            if homopolymer not in results:
                results[homopolymer] = {
                    'seqType': 'homopolymers',
                    'sequence': homopolymer,
                    'penalty_score': penalty_score,
                    'length': length,
                    'positions': [(i, j - 1)]
                }
            else:
                # Only update positions to avoid overwriting with different penalty scores or lengths
                results[homopolymer]['positions'].append((i, j - 1))
        i = j

    # Convert dictionary to list
    return list(results.values())


# checked
def analyze_local_gc_content(sequence, window_size=30, min_GC_threshold=20, max_GC_threshold=80):
    """
    Analyze and merge local GC content regions in a sequence that are below the minimum GC threshold 
    or above the maximum GC threshold. Calculate a penalty score for these regions and merge overlapping and consecutive regions.

    Returns a list of dictionaries, each containing the sequence segment, a list of (start, end) index pairs,
    average GC content, and cumulative penalty score.

    :param sequence: The DNA sequence to analyze.
    :param window_size: The size of the window to use for GC content calculation.
    :param min_GC_threshold: The minimum GC content threshold.
    :param max_GC_threshold: The maximum GC content threshold.
    :return: A list of dictionaries with the merged results.
    """
    n = len(sequence)
    merged_results = {}
    start = 0
    end = -1
    cumulative_penalty_score = 0
    cumulative_gc_content = 0
    count_windows = 0

    for i in range(n - window_size + 1):
        window = sequence[i:i + window_size]
        gc_content = calculate_gc_content(window)

        if gc_content < min_GC_threshold or gc_content > max_GC_threshold:
            penalty_score = window_size * abs(min_GC_threshold - gc_content if gc_content < min_GC_threshold else gc_content - max_GC_threshold) / 100
            if i > end + 1:
                # Close the previous segment and start a new one
                if count_windows > 0:
                    key = sequence[start:end + 1]
                    if key not in merged_results:
                        merged_results[key] = {
                            'seqType': 'local_gc_content',
                            'sequence': key,
                            'penalty_score': cumulative_penalty_score,
                            'gc_content': cumulative_gc_content / count_windows,
                            'positions': [(start, end)]
                        }
                    else:
                        # Merge the positions
                        merged_results[key]['seqType'] = 'local_gc_content'
                        merged_results[key]['penalty_score'] += cumulative_penalty_score
                        merged_results[key]['gc_content'] = (
                            merged_results[key]['gc_content'] * len(merged_results[key]['positions']) + cumulative_gc_content
                        ) / (len(merged_results[key]['positions']) + count_windows)
                        merged_results[key]['positions'].append((start, end))

                # Reset counters for the new segment
                start = i
                cumulative_penalty_score = 0
                cumulative_gc_content = 0
                count_windows = 0

            end = i + window_size - 1
            cumulative_penalty_score += penalty_score
            cumulative_gc_content += gc_content
            count_windows += 1

    # Add the last segment
    if count_windows > 0:
        key = sequence[start:end + 1]
        if key not in merged_results:
            merged_results[key] = {
                'seqType': 'local_gc_content',  # 'local_gc_content
                'sequence': key,
                'penalty_score': cumulative_penalty_score,
                'gc_content': cumulative_gc_content / count_windows,
                'positions': [(start, end)]
            }
        else:
            merged_results[key]['seqType'] = 'local_gc_content'
            merged_results[key]['penalty_score'] += cumulative_penalty_score
            merged_results[key]['gc_content'] = (
                merged_results[key]['gc_content'] * len(merged_results[key]['positions']) + cumulative_gc_content
            ) / (len(merged_results[key]['positions']) + count_windows)
            merged_results[key]['positions'].append((start, end))

    return list(merged_results.values())

# checked
def check_motifs(sequence, min_W_length=8, min_S_length=8):
    '''
    Check for the presence of W and S motifs in a DNA sequence where the motifs have lengths
    greater than or equal to specified minimum lengths. Skips any detected homopolymers.
    W motif: a sequence of nucleotides containing at least 'min_W_length' consecutive A and T bases.
    S motif: a sequence of nucleotides containing at least 'min_S_length' consecutive G and C bases.
    
    Parameters:
    - sequence: the DNA sequence to check
    - min_W_length: the minimum length of the W motif (default 8)
    - min_S_length: the minimum length of the S motif (default 8)
    
    Returns:
    A list of dictionaries with the detected motifs and their consolidated start and end indices.
    '''
    results = {}

    # Prepare patterns for longer motifs
    W_pattern = r'[AT]{' + str(min_W_length) + ',}'
    S_pattern = r'[GC]{' + str(min_S_length) + ',}'

    # Helper function to find all matches using a pattern and check for homopolymers
    def find_motifs(pattern, motif_type):
        for match in re.finditer(pattern, sequence):
            matched_sequence = match.group(0)
            if not is_homopolymer(matched_sequence):
                if matched_sequence not in results:
                    results[matched_sequence] = {
                        'seqType': 'W8S8_motifs',  # 'W8' or 'S8
                        'motif_type': motif_type,
                        'sequence': matched_sequence,
                        'length': len(matched_sequence),
                        'penalty_score': (len(matched_sequence) - (min_W_length -1) if motif_type.startswith('W') else (min_S_length-1)) / 2,
                        'positions': [(match.start(), match.end() - 1)]
                    }
                else:
                    # should add penalty score
                    results[matched_sequence]['penalty_score'] += (len(matched_sequence) - (min_W_length -1) if motif_type.startswith('W') else (min_S_length-1)) / 2
                    results[matched_sequence]['positions'].append((match.start(), match.end() - 1))

    # Check if a given DNA sequence is a homopolymer
    def is_homopolymer(unit):
        return len(set(unit)) == 1

    # Find W and S motifs
    find_motifs(W_pattern, 'W' + str(min_W_length))
    find_motifs(S_pattern, 'S' + str(min_S_length))

    # Convert dictionary to list
    return list(results.values())


def merge_positions(positions):
    # Sort and merge overlapping or consecutive positions
    if not positions:
        return []
    sorted_positions = sorted(positions)
    merged = [sorted_positions[0]]

    for current in sorted_positions[1:]:
        last = merged[-1]
        if current[0] <= last[1] + 1:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def check_inverted_repeats(sequence, min_length=6):
    results = {}
    n = len(sequence)
    
    for i in range(n):
        for length in range(min_length, (n - i) // 2 + 1): # Check for inverted repeats of length >= min_length
            repeat = sequence[i:i + length]
            rev_comp = reverse_complement(repeat)
            
            for j in range(i + length, n - length + 1):  # Search for the reverse complement in the rest of the sequence
                if sequence[j:j + length] == rev_comp:
                    key = (repeat, rev_comp)
                    position_original = (i, i + length - 1)
                    position_inverted = (j, j + length - 1)
                    
                    if key not in results:
                        results[key] = {
                            'seqType': 'inverted_repeats',
                            'sequence': repeat,
                            'inverted_sequence': rev_comp,
                            'penalty_score': (length - 9)/2 if length >= 5 else 0,
                            'original_positions': [position_original],
                            'inverted_positions': [position_inverted]
                        }
                    else:
                        if position_original not in results[key]['original_positions']:
                            results[key]['original_positions'].append(position_original)
                        if position_inverted not in results[key]['inverted_positions']:
                            results[key]['inverted_positions'].append(position_inverted)

                    break  # Stop once a matching inverted repeat is found

    # Merge positions for each entry and filter subsets
    final_results = []
    for entry in results.values():
        entry['original_positions'] = merge_positions(entry['original_positions'])
        entry['inverted_positions'] = merge_positions(entry['inverted_positions'])
        if not any((entry['sequence'] in res['sequence'] or res['sequence'] in entry['sequence']) and res != entry for res in final_results):
            final_results.append(entry)

    return final_results


# # Example usage:
# sequence = 'TTCAGTGCTATCGTCGGAtgaccgatccagccaccATGGAAACTGATACTCTCCTGCTCTGGGTCCTCCTGCTCTGGGTCCCCGGCTCCACAGGACACCATCATCATCACCACCACCATACAACTGCTGCTCCTCCTACCCCTTCCGCCACAACACCTGCTCCTCCATCCTCCTCCGCACCTCCAGAGACAACTGCCGCACCTCCTACTCCTTCCGCTACAACTCCAGCCCCTCCATCCTCCAGCGCACCTCCTGAAACAACCGCCGCTCCTCCTACTCCTAGCGCCACAACTCCAGCCCCTCCATCCTCCTCCGCTCCTCCAGAGACAACCGCAGCCCCACCAACACCATCCGCTACCACCCCAGCTCCTCCCTCCTCCTCCGCTCCTCCTGAGACAACAGCCGCACCTCCTACCCCCTCCGCTACCACACCAGCTCCCCCATCCTCCTCCGCACCACCAGAAACTACAGCCGCTCCTCCCaaGTCTTCgaaacacatatccctatc'
# print("tandem repeats", check_tandem_repeats(sequence),"\n")
# sequence = "banana"
# print("tandem repeats optimized", find_repeated_sequences(sequence))
# print("long repeats", check_long_repeats(sequence))
# print("homopolymers", check_homopolymers(sequence))
# print("local GC", analyze_local_gc_content(sequence, window_size=20))
# print("motifs", check_motifs(sequence, min_W_length=12, min_S_length=12))
# print("inverted repeats", check_inverted_repeats(sequence))

class DNARepeatsFinder:
    def __init__(self, s):
        self.s = s
        self.sa = self.build_suffix_array(s)
        self.lcp = self.find_lcp(s)

    def build_suffix_array(self, s):
        return sorted(range(len(s)), key=lambda k: s[k:])

    def find_lcp(self):
        n = len(self.s)
        lcp = [0] * n
        rank = [0] * n
        for i, suffix in enumerate(self.sa):
            rank[suffix] = i
        h = 0
        for i in range(n):
            if rank[i] > 0:
                j = self.sa[rank[i] - 1]
                while i + h < n and j + h < n and self.s[i + h] == self.s[j + h]:
                    h += 1
                lcp[rank[i]] = h
                if h > 0:
                    h -= 1
        return lcp

    def calculate_gc_content(sequence):
        '''
        Calculate the GC content of a DNA sequence.
        '''
        sequence = sequence.upper().replace(" ", "")
        gc_count = sequence.count('G') + sequence.count('C')
        gc_content = (gc_count / len(sequence)) * 100
        return round(gc_content, 2)

    def calculate_penalty_score(self, length):
        return (length - 15) / 2 if length > 15 else 0

    # Method placeholders
    def find_tandem_repeats(self, min_unit=3, min_copies=3):
        repeats = []
        n = len(self.s)
        for i in range(1, n):
            length = self.lcp[i]
            if length >= min_unit * min_copies:
                start = self.sa[i]
                while length >= min_unit:
                    count = 0
                    while (start + (count + 1) * length <= n and
                           self.s[start:start + length] == self.s[start + count * length:start + (count + 1) * length]):
                        count += 1
                    if count >= min_copies:
                        seq = self.s[start:start + length]
                        actual_length = count * length
                        repeats.append({
                            'sequence': seq,
                            'start': start,
                            'end': start + actual_length - 1,
                            'length': actual_length,
                            'gc_content': self.calculate_gc_content(seq),
                            'penalty_score': self.calculate_penalty_score(actual_length)
                        })
                        break  # Avoid detecting sub-parts of this repeat
                    length -= 1
        return repeats


    def find_dispersed_repeats(self, min_len=10):
        pass

    def find_palindromes(self, min_len=3):
        pass

    def find_homopolymers(self, min_len=3):
        pass

# Example usage
dna_sequence = "ATCGATCGATCGATCGTTTTGCACACACACACGTGTGTGTGTGAGAGAGAGACCCCCC"
repeats_finder = DNARepeatsFinder(dna_sequence)
tandem_repeats, homopolymer_repeats = repeats_finder.find_tandem_repeats(min_unit=3, min_copies=3)
print("Tandem repeats:", tandem_repeats)


