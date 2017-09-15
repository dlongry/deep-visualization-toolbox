#! /usr/bin/env python

import argparse
import ipdb as pdb
import cPickle as pickle

import settings
from caffevis.caffevis_helper import load_mean

from loaders import load_imagenet_mean, load_labels, caffe
from jby_misc import WithTimer
from max_tracker import output_max_patches



def main():
    parser = argparse.ArgumentParser(description='Loads a pickled NetMaxTracker and outputs one or more of {the patches of the image, a deconv patch, a backprop patch} associated with the maxes.')
    parser.add_argument('--N',           type = int, default = 9, help = 'Note and save top N activations.')
    parser.add_argument('--gpu',         action = 'store_true', default=settings.caffevis_mode_gpu, help = 'Use gpu.')
    parser.add_argument('--do-maxes',    action = 'store_true', help = 'Output max patches.')
    parser.add_argument('--do-deconv',   action = 'store_true', help = 'Output deconv patches.')
    parser.add_argument('--do-deconv-norm', action = 'store_true', help = 'Output deconv-norm patches.')
    parser.add_argument('--do-backprop', action = 'store_true', help = 'Output backprop patches.')
    parser.add_argument('--do-backprop-norm', action = 'store_true', help = 'Output backprop-norm patches.')
    parser.add_argument('--do-info',     action = 'store_true', help = 'Output info file containing max filenames and labels.')
    parser.add_argument('--idx-begin',   type = int, default = None, help = 'Start at this unit (default: all units).')
    parser.add_argument('--idx-end',     type = int, default = None, help = 'End at this unit (default: all units).')
    
    parser.add_argument('--nmt_pkl',       type = str, help = 'Which pickled NetMaxTracker to load.')
    parser.add_argument('--net_prototxt', type = str, default = settings.caffevis_deploy_prototxt, help = 'network prototxt to load')
    parser.add_argument('--net_weights', type = str, default = settings.caffevis_network_weights, help = 'network weights to load')
    parser.add_argument('--datadir', type = str, default = settings.static_files_dir, help = 'directory to look for files in')
    parser.add_argument('--filelist',      type = str, help = 'List of image files to consider, one per line. Must be the same filelist used to produce the NetMaxTracker!')
    parser.add_argument('--outdir',        type = str, help = r'Which output directory to use. Files are output into outdir/layer/unit_%%04d/{maxes,deconv,backprop}_%%03d.png')
    parser.add_argument('--layer',         type = str, help = 'Which layer to output')
    parser.add_argument('--mean', type = str, default = settings.caffevis_data_mean, help = 'data mean to load')
    args = parser.parse_args()

    if args.gpu:
        caffe.set_mode_gpu()
    else:
        caffe.set_mode_cpu()

    if args.mean == "":
        data_mean = load_imagenet_mean()
    else:
        data_mean = load_mean(args.mean)

    net = caffe.Classifier(args.net_prototxt,
                           args.net_weights,
                           mean=None,
                           channel_swap=settings.caffe_net_channel_swap,
                           raw_scale=settings.caffe_net_raw_scale,
                           image_dims=settings.caffe_net_image_dims)

    if data_mean is not None:
        net.transformer.set_mean(net.inputs[0], data_mean)

    assert args.do_maxes or args.do_deconv or args.do_deconv_norm or args.do_backprop or args.do_backprop_norm or args.do_info, 'Specify at least one do_* option to output.'

    with open(args.nmt_pkl, 'rb') as ff:
        nmt = pickle.load(ff)

    normalized_layer_name = settings.normalize_layer_name_for_max_tracker_fn(args.layer)

    # TODO: use settings.normalize_layer_name_for_max_tracker_fn to normalize layer name
    mt = nmt.max_trackers[normalized_layer_name]

    if args.idx_begin is None:
        args.idx_begin = 0
    if args.idx_end is None:
        args.idx_end = mt.max_vals.shape[0]

    with WithTimer('Saved %d images per unit for %s units %d:%d.' % (args.N, normalized_layer_name, args.idx_begin, args.idx_end)):
        output_max_patches(mt, net, normalized_layer_name, args.idx_begin, args.idx_end,
                           args.N, args.datadir, args.filelist, args.outdir,
                           (args.do_maxes, args.do_deconv, args.do_deconv_norm, args.do_backprop, args.do_backprop_norm, args.do_info))



if __name__ == '__main__':
    main()
