import math
import numpy as np
import scipy.io
import matplotlib.pyplot as plt
from matplotlib import patches

from detect_peaks import detect_peaks
from circle_fit import circle_fit
from Stroke import *
# If matplotlib is not working on OSX follow directions in the link below
# https://stackoverflow.com/questions/21784641/installation-issue-with-matplotlib-python

def circle_error(c_x,c_y,radius,p_x,p_y):
    '''
    Returns circle fit error for one single point only
    '''
    distance = abs(((p_x-c_x)**2 + (p_y-c_y)**2)**0.5 -radius)
    error = distance**2
    return error

def line_error(slope,offset,p_x,p_y):
    line_y = slope*p_x + offset
    difference = abs(p_y-line_y)
    error = difference**2
    return error

def fit_line(X,Y):
    A = np.vstack([X,np.ones(len(X))]).T
    slope,offset = np.linalg.lstsq(A,Y)[0]
    return (slope,offset)

def get_total_line_error(X,Y,slope,offset):
    total_fitted_line_error = 0
    for x,y in zip(X,Y):
        total_fitted_line_error += line_error(slope,offset,x,y)
    return total_fitted_line_error

def get_total_circle_error(X,Y,c_x,c_y,radius):
    total_fitted_circle_error = 0
    for x,y in zip(X,Y):
        total_fitted_circle_error += circle_error(c_x,c_y,radius,x,y)
    return total_fitted_circle_error


def euclidean_distance(x1,y1,x2,y2):
    return ((y2-y1)**2 + (x2-x1)**2)**0.5

def get_cumulative_arc_lengths(X,Y):
    cumulative_arc_lengths = [0]
    assert (len(X)==len(Y))
    for i in range(len(X)-1):
        x1, y1 = X[i], Y[i]
        x2, y2 = X[i+1],Y[i+1]
        distance = euclidean_distance(x1,y1,x2,y2)
        cumulative_distance = distance + cumulative_arc_lengths[-1]
        cumulative_arc_lengths.append(cumulative_distance)
    return cumulative_arc_lengths

def get_subtended_angle(s1_x,s1_y,s2_x,s2_y,c_x,c_y):
    sc1 = [s1_x-c_x,s1_y-c_y]
    sc2 = [s2_x-c_x,s2_y-c_y]
    dot_product = sum([e1*e2 for e1,e2 in zip(sc1,sc2)])
    norm_1 = sum([e**2 for e in sc1])**0.5
    norm_2 = sum([e**2 for e in sc2])**0.5
    
    domain = min(1,dot_product/(norm_1*norm_2))
    angle_in_radians = math.acos(domain)
    return math.degrees(angle_in_radians)

def compute_curvatures(arc_lengths,angles):
    curvatures = [0]
    for i in range(1,len(arc_lengths)):
        try:
            curvature = (angles[i] - angles[i-1])/(arc_lengths[i]-arc_lengths[i-1])
        except ZeroDivisionError:
            curvature = float('inf')
        curvatures.append(curvature)
    return curvatures

def compute_curvatures_alternative(arc_lengths,angles,window):
    alt_curvatures = []
    for i in range(len(arc_lengths)):
        x_points = []
        y_points = []
        for j in range(1,window+1):
            if i-j >= 0:
                x,y = arc_lengths[i-j],angles[i-j]
                x_points.append(x)
                y_points.append(y)
            x_points.append(arc_lengths[i])
            y_points.append(angles[i])
            if i+j < len(arc_lengths):
                x,y = arc_lengths[i+j],angles[i+j]
                x_points.append(x)
                y_points.append(y)
        X=np.array(x_points)
        Y=np.array(y_points)
        A = np.vstack([X,np.ones(len(X))]).T
        curvature,y_intercept = np.linalg.lstsq(A,Y)[0]
        alt_curvatures.append(curvature)
    return alt_curvatures  


def correct_angle_curve(angle):
    return (2*math.pi+angle)%(2*math.pi)


def segment_stroke(stroke):

    segpoints, segtypes = [], []

    # YOUR CODE HERE

    x_s, y_s, times = stroke.x, stroke.y, stroke.time

    # 1. CUMULATIVE ARC LENGTHS
    cumulative_arc_lengths = get_cumulative_arc_lengths(x_s,y_s)

    # 2. SMOOTHED PEN SPEEDS
    window = 2

    speeds = [0] #Assign first point's speed to be 0 
    for i in range(1,len(cumulative_arc_lengths)-1):
        s_i = (cumulative_arc_lengths[i+1] - cumulative_arc_lengths[i-1])/(times[i+1]-times[i-1])
        speeds.append(s_i)
    speeds.append(speeds[-1]) #Assign last point's speed to that of penultimate point (given in paper!)


    smoothed_speeds = [0] #Assign first point's speed to be 0

    for i in range(1,len(speeds)):
        speed = speeds[i]
        array = [speed]
        for j in range(1,window+1):
            if i+j < len(speeds):
                array.append(speeds[i+j])
            if i-j >= 0: 
                array.append(speeds[i-j])
        smoothed_speed = sum(array)/float(len(array))
        smoothed_speeds.append(smoothed_speed)

    # 3. TANGENTS
    tangents = []
    window = 11
    computed_lines = []
    for i in range(len(x_s)):
        x_points = []
        y_points = []
        for j in range(1,window+1):
            if i-j >= 0:
                x,y = x_s[i-j],y_s[i-j]
                x_points.append(x)
                y_points.append(y)
            x_points.append(x_s[i])
            y_points.append(y_s[i])
            if i+j < len(x_s):
                x,y = x_s[i+j],y_s[i+j]
                x_points.append(x)
                y_points.append(y)
        X=np.array(x_points)
        Y=np.array(y_points)
        A = np.vstack([X,np.ones(len(X))]).T
        slope,y_intercept = np.linalg.lstsq(A,Y)[0]
        computed_lines.append(slope)
    
    # 4. CURVATURE

    angles = [math.atan(slope) for slope in computed_lines]

    corrected_angles = [correct_angle_curve(angle) for angle in angles] #project angles 0 to 2pi range

    curvatures = compute_curvatures(cumulative_arc_lengths,corrected_angles)

    
    # 5. IDENTIFY CORNERS
    average_smoothed_speed = sum(smoothed_speeds)/len(smoothed_speeds)
    speed_threshold = 0.50 * average_smoothed_speed

    speed_minima = []
    assert (len(x_s) == len(curvatures) == len(smoothed_speeds))

    for i in range(len(x_s)):
        speed = smoothed_speeds[i]
        if speed<=speed_threshold:
            speed_minima.append(speed)
        else:
            speed_minima.append(None)
    assert (len(speed_minima) == len(speeds))

    speed_threshold2 = 0.80 * average_smoothed_speed
    curvature_maxima = []
    curvature_threshold = 0.75
    for i in range(len(x_s)):
        curvature = curvatures[i]
        if smoothed_speeds[i] <= speed_threshold2 and abs(curvature) >= curvature_threshold:
            curvature_maxima.append(curvature)
        else:
            curvature_maxima.append(None)

    #peaks
    peaks = []
    peak_indices1 = list(detect_peaks(x_s,mpd=40))
    peak_coordinates = [x_s[i] for i in peak_indices1]

    peak_indices2 = list(detect_peaks(y_s))
    peak_coordinates2 = [y_s[i] for i in peak_indices2]

    peaks = peak_indices1 + peak_indices2
    # 6. COMBINE AND FILTER POINTS

    segment_indices = []
    for i in range(len(x_s)):
        if speed_minima[i] is not None and curvature_maxima[i] is not None:
            segment_indices.append(i)
        elif i==0 or i==len(x_s)-1:
            segment_indices.append(i)
    segment_indices += peaks
    segment_indices = sorted(segment_indices)  

    prev = segment_indices[0]
    filtered_indices = [prev]
    threshold = 12
    for i in range(1,len(segment_indices)):
        index = segment_indices[i]
        if (index - prev)>= 5:
            filtered_indices.append(index)
        prev = index

    # 7. CLASSIFY SEGMENTS
    candidate_types = []
    for i in range(len(filtered_indices)-1):
        start_index, end_index = filtered_indices[i], filtered_indices[i+1]
        X = x_s[start_index:end_index+1]
        Y = y_s[start_index:end_index+1]

        #Try Fitting A Line
        A = np.vstack([X,np.ones(len(X))]).T
        slope,offset = np.linalg.lstsq(A,Y)[0]

        #Try Fitting A Circle
        c_x,c_y,radius = circle_fit(X,Y)

        total_fitted_line_error = get_total_line_error(X,Y,slope,offset)
        total_fitted_circle_error = get_total_circle_error(X,Y,c_x,c_y,radius)

        if total_fitted_line_error <= total_fitted_circle_error:
            candidate_types.append(0) #0 for line
        else:
            begin, end = cumulative_arc_lengths[start_index], cumulative_arc_lengths[end_index]
            subtended_angle = math.degrees((begin-end)/radius)
            if abs(subtended_angle) >= 36: candidate_types.append(1)
            else: candidate_types.append(0)

    # 8. MERGE SEGMENTS
    segpoints = filtered_indices
    segtypes = candidate_types
    merge_size_threshold = 5 #0.2
    i = 0
    N = len(filtered_indices)

    # while i < N-2:
    #     this_type = candidate_types[i]
    #     this_index = filtered_indices[i]
    #     line = this_type  == 0 
    #     circle = not line 
    #     start_x, start_y  = x_s[filtered_indices[i]], y_s[filtered_indices[i]]
    #     end_x, end_y = x_s[filtered_indices[i+1]], y_s[filtered_indices[i+1]]
    #     start_x2, start_y2  = x_s[filtered_indices[i+1]], y_s[filtered_indices[i+1]]
    #     end_x2, end_y2 = x_s[filtered_indices[i+2]], y_s[filtered_indices[i+2]]
    #     print ("Now analysing points:")
    #     print ("point1_coords:",start_x,start_y)
    #     print ("point2_coords:",end_x,end_y)
    #     print ("point3_coords:",end_x2,end_y2)

    #     if line:
    #         length_of_segment = euclidean_distance(start_x,start_y,end_x,end_y)
    #     if circle: 
    #         length_of_segment = cumulative_arc_lengths[filtered_indices[i+1]] - cumulative_arc_lengths[filtered_indices[i]]
        
    #     adjacent_segment_type = candidate_types[i+1]
    #     adj_line = (adjacent_segment_type == 0)
    #     adj_circle = not adj_line
    #     if adj_line:
    #         length_of_segment2 = euclidean_distance(start_x2,start_y2,end_x2,end_y2)
    #     if adj_circle:
    #         length_of_segment2 = cumulative_arc_lengths[filtered_indices[i+2]] - cumulative_arc_lengths[filtered_indices[i+1]]
        
    #     if adjacent_segment_type == candidate_types[i]:
            
    #         X1, Y1 = x_s[this_index:filtered_indices[i+1]], y_s[this_index:filtered_indices[i+1]] 
    #         slope1,offset1 = fit_line(X1,Y1)
    #         line1_error = get_total_line_error(X1,Y1,slope1,offset1)

    #         X2, Y2 = x_s[filtered_indices[i+1]:filtered_indices[i+2]], y_s[filtered_indices[i+1]:filtered_indices[i+2]] 
    #         slope2,offset2 = fit_line(X2,Y2)
    #         line2_error = get_total_line_error(X2,Y2,slope2,offset2)

    #         X3, Y3 = x_s[this_index:filtered_indices[i+2]], y_s[this_index:filtered_indices[i+2]] 
    #         slope3,offset3 = fit_line(X3,Y3)

    #         lines_merged_error = get_total_line_error(X3,Y3,slope2,offset2)
    #         lines_separate_error = line1_error + line2_error

    #         if lines_merged_error <= (lines_separate_error):
    #             print ("yeah, merging", x_s[filtered_indices[i]],x_s[filtered_indices[i+1]],x_s[filtered_indices[i+2]])
    #             segpoints.append(filtered_indices[i])
    #             segpoints.append(filtered_indices[i+2])
    #             segtypes.append(this_type)
    #             i+=2
    #         else:
    #             print ("Not merging", x_s[filtered_indices[i]],x_s[filtered_indices[i+1]],x_s[filtered_indices[i+2]])
    #             print ("point1_coords:",start_x,start_y)
    #             print ("point2_coords:",end_x,end_y)
    #             print ("point3_coords:",end_x2,end_y2)
    #             segpoints.append(filtered_indices[i])
    #             segpoints.append(filtered_indices[i+1])
    #             segtypes.append(this_type)
    #             i+=1 

        
    #     if adjacent_segment_type != this_type:
    #         print ("different segments")
    #         if length_of_segment2 == 0 or length_of_segment/length_of_segment2 >= merge_size_threshold:
    #             segpoints.append(filtered_indices[i])
    #             segpoints.append(filtered_indices[i+2])
    #             segtypes.append(this_type)
    #             i+=2 
                
    #         elif length_of_segment == 0 or length_of_segment2/length_of_segment >= merge_size_threshold:
    #             segpoints.append(filtered_indices[i])
    #             segpoints.append(filtered_indices[i+2])
    #             segtypes.append(adjacent_segment_type) #since adjacent segment is larger
    #             i+=2 
    #         else:
    #             segpoints.append(filtered_indices[i])
    #             segpoints.append(filtered_indices[i+1])
    #             segtypes.append(this_type)
    #             i+=1 
    
    print ("BEFORE:" ,filtered_indices) 
    # print ("X COORDS", [x_s[i] for i in filtered_indices])
    # print ("Y COORDS", [y_s[i] for i in filtered_indices])
    # print ("TYPES", candidate_types)
    print ("OUTPUT:", segpoints)
    sorted_list = sorted(list(set(segpoints)))
    segpoints = sorted_list
    print ("SORTED",sorted_list)
    print ("TYPES", segtypes)
    print ("X COORDS", [x_s[i] for i in sorted_list])
    print ("Y COORDS", [y_s[i] for i in sorted_list])
















    




    # print "SEGPOINTS",segpoints
    # print "SEGTYPES",segtypes

    return segpoints, segtypes

#For Debugging
from stroke_data import strokes

# X = [0, 1, 2]
# Y = [0, 1, 2]
# t = [0, 1, 2]
# m_stroke = Stroke(X,Y,t)
# print segment_stroke(m_stroke)
# print (segment_stroke(my_stroke))

# xs = my_strokes[1]['x']
# ys = my_strokes[1]['y']
# # cx,cy,r = circle_fit(xs,ys)
# # print circle_error(cx,cy,r,-0.5,0)

# X=np.array(xs)
# Y=np.array(ys)
# A = np.vstack([X,np.ones(len(X))]).T
# slope,offset = np.linalg.lstsq(A,Y)[0]
# print line_error(slope,offset,1,1)



