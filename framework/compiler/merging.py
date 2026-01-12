#!/usr/bin/python3

import sys
import codecs
import subprocess
import threading
import os
import numpy as np
import shutil
import math
import argparse
import time

def main(inputRE, outputLog, batch, reps):
    print("repeating:" + str(reps[0])+" times")
    for i in range(0, 1):
        print("Successful parsing iteration " + str(i))
        avg = []
        fnames = []
        for file in inputRE:
            print(file)
            if os.path.isfile(file):
                currAvg=[]
                for b in batch: 
                    # print("processing "+file+" with batch "+str(b))
                    fname = extract_filename(file)
                    fnames.append(fname+str(b))
                    outputFilename = outputLog+fname+"_"+str(b)+"/"
                    try:
                        os.mkdir(outputFilename)
                    except OSError:
                        print("folder present\n")

                    start = time.time()
                    f = compile_file(file, outputLog, outputFilename+"automaton", b, outputFilename+"compilation_time.txt")
                    end = time.time()

                    duration = end - start
                    print(f"[MERGING] {file} batch={b} took {duration:.3f} seconds")
                lineTW=fname
                for b in currAvg:
                    lineTW=lineTW+", "+str(b)
            else:
                print("not a file "+file)
        
def compile_file(inputFile, outputLog, outputFilename, batch, time_dir):
    if(batch==0):
        batch=-1
    compilerCommand = "./compiler -i "+ inputFile + " -b "+str(batch)+" -o "+ outputFilename + " -t " + "\""+ time_dir +"\""
    print(compilerCommand)
    p = subprocess.Popen(compilerCommand, stdout=subprocess.PIPE, shell=True)
    output, error = p.communicate()

    return outputFilename+".txt"

def extract_filename(dir):
    name=''
    flag = True
    for item in os.path.basename(os.path.basename(dir).split('.')[0]).split('_'):
        if "formatted" not in item and "completeLog" not in item and flag:
            name=name+item
            flag = False
        elif "formatted" not in item and "completeLog" not in item and not flag:
            name = name+'_'+item
    return name 


if __name__ == "__main__":

    s_reps = sys.argv.index('-r')
    s_batch = sys.argv.index('-b')
    reps = [int(i) for i in sys.argv[s_reps+1:s_batch]]
    batch = [int(i) for i in sys.argv[s_batch+1:]]


    inputRE = [
        "../../datasets/custom/current_dataset.txt"
    ]

    simpleOutput="../output/"

    outputLog="../../mfsa/"

    # batch = [1,2,5,10,20,50,100,0]
    
    for files in os.listdir(outputLog):
        path = os.path.join(outputLog, files)
        try:
            shutil.rmtree(path)
        except OSError:
            os.remove(path)


    main(inputRE, outputLog, batch, reps)

