import sys
from sklearn.model_selection import train_test_split

from Gesture import GestureSet, Sequence, Frame
from classify_nn import classify_nn
from normalize_frames import normalize_frames
from load_gestures import load_gestures
import random
def separate_data(gestures,ratio):
    '''
    Sample the entire gesture set data's sequences according to the ratio
    :param gestures: the set of gestures 
    :param ratio: the fraction of dataset to be used as training set
    :return: separated data set as (training,test)
    '''
    N = 30
    number_of_tests = N-int(round(ratio*N))
    copied_gesture_sets = gestures[:] #make sure to not mutate the orig. gesture set
    testing_data = []
    for gesture_set in copied_gesture_sets:
        for i in range(number_of_tests):
            random_index = random.randint(0,len(gesture_set.sequences)-1)
            sequence = gesture_set.sequences.pop(random_index)
            testing_data.append(sequence)
    return (copied_gesture_sets,testing_data)

def test_classify_nn(num_frames, ratio):
    """
    Tests classify_nn function. 
    Splits gesture data into training and testing sets and computes the accuracy of classify_nn()
    :param num_frames: the number of frames to normalize to
    :param ratio: percentage to be used for training
    :return: the accuracy of classify_nn()
    """

    gestures = load_gestures()
    normalized_gestures = normalize_frames(gestures, num_frames)
    training_data,testing_data = separate_data(normalized_gestures,ratio)
    matching_preds = [classify_nn(datum,training_data)==datum.label \
            for datum in testing_data]
    accuracy = sum(matching_preds)/len(matching_preds)
    return accuracy



if len(sys.argv) != 3:
    raise ValueError('Error! Give normalized frame number and test/training ratio after filename in command. \n'
                     'e.g. python test_nn.py 20 0.4')

num_frames = int(sys.argv[1])
ratio = float(sys.argv[2])

accuracy = test_classify_nn(num_frames, ratio)
print("Accuracy: ", accuracy)