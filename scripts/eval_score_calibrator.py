#!/usr/bin/env python3

import argparse
from dca_plda import calibration
from dca_plda import scores as dscores
import numpy as np


    
parser = argparse.ArgumentParser(description="Train a post-hoc score calibrator using linear logistic regression.")
parser.add_argument('--key',      help='Key used for evaluation. If provided when scores are in h5 format, performance metrics before and after calibration will be printed..', default=None)
parser.add_argument('--ptar',     help='Effective prior for positive samples used for computing evaluation metrics.', default=0.01, type=float)
parser.add_argument('--fmt',      help='Format of input scores. If set to "npz", an npz file with two arrays, pos and neg, for the positive and negative samples is expected, or a single array with all scores. In the latter case, performance metrics are not computed', default='npz')
parser.add_argument('scores',     help='Score file in h5 or npz format.')
parser.add_argument('model',      help='File with the calibration parameters, alpha (scale) and beta (shift).')
parser.add_argument('outscores',  help='File name for the output scores, without extension. Will be saved in the same format as the input with the correct extension.')

opt = parser.parse_args()

model = np.load(opt.model)
a, b = model['a'], model['b']

# Read and calibrat scores

has_key = False
if opt.fmt == "h5":
    if opt.key != None:
        key = dscores.Key.load(opt.key)
        has_key = True
        
    raw_scores = dscores.Scores.load(opt.scores)
    if has_key:
        ascores = raw_scores.align(key)
        raw_pos = ascores.score_mat[key.mask==1]
        raw_neg = ascores.score_mat[key.mask==-1]        

    cal_scores = raw_scores
    cal_scores.score_mat = a * raw_scores.score_mat + b
    if has_key:
        ascores = cal_scores.align(key)
        cal_pos = ascores.score_mat[key.mask==1]
        cal_neg = ascores.score_mat[key.mask==-1]        

    cal_scores.save("%s.h5"%opt.outscores)
        
else:
    sc = np.load(opt.scores)
    if 'all' in sc.files:
        raw_all = sc['all']
        cal_all = a * raw_all + b
        np.savez("%s.npz"%opt.outscores, all=cal_all)

    else:
        raw_pos, raw_neg = sc['pos'], sc['neg'] 
        cal_pos = a * raw_pos + b
        cal_neg = a * raw_neg + b
        has_key = True
        np.savez("%s.npz"%opt.outscores, pos=cal_pos, neg=cal_neg)

        
# Compute performance before and after calibration

if has_key:
    print("Results before and after calibration on test %d positive and %d negative samples"%(len(raw_pos), len(raw_neg)))
    ptars = [opt.ptar, 0.5]
    line1, header = dscores.compute_performance_from_arrays(raw_pos, raw_neg, ptars, "before calibration")
    line2, header = dscores.compute_performance_from_arrays(cal_pos, cal_neg, ptars, "after calibration")
    print(header, line1, line2, sep='')
