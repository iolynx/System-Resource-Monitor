import pickle
import os
import time


cwd = os.path.abspath(__file__)[:-21]
FilesToTrack = cwd + "\\ProcessHistory.txt"

track = {}

while True:
    with open(FilesToTrack, 'r') as f:
        track = eval(f.readline())
    for file_path in track.keys():
        current_access_time = os.path.getatime(file_path)
        if current_access_time > track[file_path][-1]:
            track[file_path].append(current_access_time)
    with open(FilesToTrack, 'w') as f:
        f.write(str(track))
    time.sleep(10)
