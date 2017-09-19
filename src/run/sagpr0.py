#!/usr/bin/python

import sys
import numpy as np
import math
import scipy.linalg
import argparse 
import os
sys.path.insert(1,os.path.join(sys.path[0], '..'))
import utils.kern_utils

###############################################################################################################################

def do_sagpr0(lm0,fractrain,tens,kernel0_flatten,sel,rdm):

    # Initialize regression
    mean0 = 0.0 
    intrins_dev0 = 0.0
    abs_error0 = 0.0
    ncycles = 5

    lvals = [0]
    degen = [(2*l+1) for l in lvals]
    intrins_dev   = np.zeros(len(lvals),dtype=float)
    intrins_error = np.zeros(len(lvals),dtype=float)
    abs_error     = np.zeros(len(lvals),dtype=float)

    print "Results averaged over "+str(ncycles)+" cycles"

    for ic in range(ncycles):

        ndata = len(tens)
        [ns,nt,ntmax,trrange,terange] = utils.kern_utils.shuffle_data(ndata,sel,rdm,fractrain)

        # Build kernel matrix
        kernel0 = utils.kern_utils.unflatten_kernel0(ndata,kernel0_flatten)

        # Partition properties and kernel for training and testing
        [vtrain,vtest,[k0tr],[k0te]] = utils.kern_utils.partition_kernels_properties(tens,[kernel0],trrange,terange)

###        # Extract the non-equivalent component, including degeneracy.

###        # Unitary transormation matrix from Cartesian to spherical (l=0,m=0), Condon-Shortley convention.

###        # Transformation matrix from complex to real spherical harmonics (l=1,m=-1,0,+1).

###        # Extract the real spherical components (l=1) of the dipoles.

        # Build regression vectors
        vtrain0 = np.real(vtrain).astype(float) - np.real(np.mean(vtrain))
        vtest0 = np.real(vtest).astype(float)
 
        # Build and invert training kernel
        ktrain0 = np.real(k0tr) + lm0*np.identity(nt)

        # Invert training kernel
        invktrvec0 = scipy.linalg.solve(ktrain0,vtrain0)

        # Predict on train data set.
        outvec0 = np.dot(np.real(k0tr),invktrvec0)

        # Predict on test data set.
        outvec0 = np.dot(np.real(k0te),invktrvec0) + np.real(np.mean(vtrain))
        # Print out errors and diagnostics.
        mean0 += np.mean(vtest0)-np.min(vtest0)
        intrins_dev0 += np.std(vtest0)**2
        abs_error0 += np.sum((outvec0-vtest0)**2)/float(ns)

    mean0 /= float(ncycles)
    intrins_dev0 = np.sqrt(intrins_dev0/float(ncycles))
    abs_error0 = np.sqrt(abs_error0/float(ncycles))
    intrins_error0 = 100*np.sqrt(abs_error0**2/intrins_dev0**2)
    print ""
    print "testing data points: ", ns    
    print "training data points: ", nt   
    print "Results for lambda_0 = ", lm0
    print "--------------------------------"
    print " TEST AVE  (l=0) = %.6f"%mean0
    print " TEST STD  (l=0) = %.6f"%intrins_dev0
    print " ABS  RMSE (l=0) = %.6f"%abs_error0
    print " TEST RMSE (l=0) = %.6f %%"%intrins_error0

###############################################################################################################################

def add_command_line_arguments_learn(parsetext):
    parser = argparse.ArgumentParser(description=parsetext)
    parser.add_argument("-lm", "--lmda", nargs='+', help="Lambda values list for KRR calculation")
    parser.add_argument("-ftr", "--ftrain",type=float, help="Fraction of data points used for testing")
    parser.add_argument("-t", "--tensors", help="File containing tensors")
    parser.add_argument("-k0", "--kernel0", help="File containing L=0 kernel")
    parser.add_argument("-sel", "--select",nargs='+', help="Select maximum training partition")
    parser.add_argument("-rdm", "--random",type=int, help="Number of random training points")
    args = parser.parse_args()
    return args

###############################################################################################################################

def set_variable_values_learn(args):

    # default values
    lm0 = 0.001
    ftr = 1  
 
    lm = [lm0]
    if args.lmda:
        lmlist = args.lmda
        if sum([lmlist[i].count(',') for i in xrange(len(lmlist))]) > 0:
            for i in xrange(len(lmlist)):
                lmlist[i] = lmlist[i].split(',')
            lmlist = np.concatenate(lmlist)
        if (len(lmlist)%2 != 0):
            print "Error: list of lambdas must have the format n,lambda[n],m,lambda[m],..."
            sys.exit(0)
        for i in xrange(len(lmlist)/2):
            nval = int(lmlist[2*i])
            lmval = float(lmlist[2*i+1])
            lm[nval] = lmval

    if args.ftrain:
        ftr = args.ftrain 
    if args.tensors:
        tfile = args.tensors
    else:
        print "Features file must be specified!"
        sys.exit(0)
    # Read in features
    tens=[line.rstrip('\n') for line in open(tfile)]

    print "Loading kernel matrices..."
    if args.kernel0:
        kfile0 = args.kernel0
    else:
        print "Kernel file must be specified!"
        sys.exit(0)
    kernel0 = np.loadtxt(kfile0,dtype=float)

    beg = 0
    end = int(len(tens)/2)
    sel = [beg,end]
    if args.select:
        sellist = args.select
        for i in xrange(len(sellist)):
            sel[0] = int(sellist[0])
            sel[1] = int(sellist[1])

    rdm = 0
    if args.random:
        rdm = args.random 

    return [lm[0],ftr,tens,kernel0,sel,rdm]

###############################################################################################################################

if __name__ == '__main__':
    # Read in all arguments and call the main function.
    args = add_command_line_arguments_learn("SA-GPR for scalars")
    [lm0,fractrain,ener,kernel0_flatten,sel,rdm] = set_variable_values_learn(args)
    do_sagpr0(lm0,fractrain,ener,kernel0_flatten,sel,rdm)
