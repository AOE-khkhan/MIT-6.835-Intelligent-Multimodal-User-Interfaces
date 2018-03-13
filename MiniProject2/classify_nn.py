import operator
import math
import numpy as np 

def get_L2_distance(sequence1,sequence2):
    """
    Compute the L2 norm between two sequences 
    :param sequence1 the first sequence
    :param sequence2 the second sequence
    :return: the Euclidean distance between the two sequences
    """
    frames1, frames2 = sequence1.frames, sequence2.frames
    total_difference = 0 
    assert(len(frames1)==len(frames2))
    for i in range(len(frames1)):
        f1, f2 = frames1[i], frames2[i]
        nf1 = np.array(f1.frame)
        nf2 = np.array(f2.frame)
        difference = np.sum(np.square(nf1-nf2))
        total_difference += difference
    return np.sqrt(total_difference)

def classify_nn(test_sequence, training_gesture_sets):
    """
    Classify test_sequence using nearest neighbors
    :param test_gesture: Sequence to classify
    :param training_gesture_sets: training set of labeled gestures
    :return: a classification label (an integer between 0 and 8)
    """
    minimum_distance = float('inf')
    guessed_sequence = None #this MUST be updated
    for gesture in training_gesture_sets:
        for sequence in gesture.sequences:
            L2_distance = get_L2_distance(test_sequence,sequence)
            if L2_distance < minimum_distance:
                minimum_distance = L2_distance
                guessed_sequence = sequence.label
    return guessed_sequence