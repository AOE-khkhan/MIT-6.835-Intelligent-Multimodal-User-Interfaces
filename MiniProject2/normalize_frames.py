def handle_indices(cur_frame_number, frame_difference, removing=False):
    """
    Calculate the removal/addition point (indices) to remove/add
    :param cur_frame_numer: length of sequence's frame number 
    :param num_frames_to_remove: how many frames to remove/add in between
    :return a list of indices whose each index shows the removed/added frame id
    """
    steps =  cur_frame_number//frame_difference;
    start = (steps+cur_frame_number%frame_difference)//2 if removing \
    else (cur_frame_number%frame_difference)//2
    indices = [start+i*steps for i in range(frame_difference)]
    return indices

def normalize_each_sequence(sequence,num_frames):
    """
    Wrapper function to decide whether to remove or add indices for each sequence
    **Mutates** the given sequence
    :param sequence: the sequence that contains the frames
    :param num_frames: the target number of frames desired
    :return None 
    """
    cur_frame_number = len(sequence.frames)
    removing_frames = (cur_frame_number>=num_frames)
    frame_difference = abs(cur_frame_number - num_frames)
    if num_frames==cur_frame_number:
        return #don't do anything
    if removing_frames:
        indices_to_remove = handle_indices(cur_frame_number,frame_difference,removing=True) #get indices of frames to remove
        updated_indices = sorted(list(set(range(cur_frame_number)).difference(set(indices_to_remove)))) #add and filter out duplicate index numbers 
    else:
        indices_to_add = handle_indices(cur_frame_number,frame_difference,removing=False) #get indices of frames to duplicate
        updated_indices = sorted(indices_to_add + list(range(cur_frame_number)))
    sequence.frames = [sequence.frames[index] for index in updated_indices] #mutate sequence with computed indices

def normalize_gesture_sets(g_sets,num_frames):
    """
    Wrapper function to normalize each sequence within a gesture set
    **Mutates** the given sequence
    """
    for gesture_set in g_sets:
        for sequence in gesture_set.sequences:
            normalize_each_sequence(sequence,num_frames)

def normalize_frames(gesture_sets, num_frames):
    """
    Normalizes the number of Frames in each Sequence in each GestureSet
    :param gesture_sets: the list of GesturesSets
    :param num_frames: the number of frames to normalize to
    :return: a list of GestureSets where all Sequences have the same number of Frames
    """ 
    gesture_sets_copy = gesture_sets[:]
    normalize_gesture_sets(gesture_sets_copy,num_frames)
    return gesture_sets_copy