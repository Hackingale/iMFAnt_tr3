import numpy as np

import subprocess
import os

num_threads = [1]

merging_factors = [0]

output_folder = "../output_matches/"

input = [
    "../mfsa/current_dataset_"
]

streams = [
    "../input_streams/custom/input_current.input"
]


for i in input: 
    for m in merging_factors:
        for n in num_threads:
            mfsa_dir = i + str(m) + "/"
            print("MFSA DIR: "+mfsa_dir)
            output_file = output_folder + i.split("/")[2] + "_multi_"+str(m)+"m_"+str(n)+"t.output.txt"
            num = len(os.listdir(mfsa_dir)) - 1
            p = subprocess.Popen("export OMP_NUM_THREADS="+str(n)+"; make && ./multithreaded_imfant " + streams[input.index(i)] + " " + mfsa_dir + " " + str(num) + " " + output_file, shell=True)
            output, error = p.communicate()

