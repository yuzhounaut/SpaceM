import spaceM
import pandas as pd
import os, gc
from subprocess import call
import GUI_maldi_helper

def getPath(field):
    return pd.read_json(os.path.dirname(spaceM.__file__) + '\\paths.json')[field].as_matrix()[0]

def curator():
    call(['python', os.path.dirname(GUI_maldi_helper.__file__) + '\\MaldiHelper.py'])

def stitchMicroscopy(MF,
                     merge_colors,
                     merge_filenames,
                     tf,
                     preMALDI=True,
                     postMALDI=True,
                     ):

    """Function to stitch tile microscopy images into a single one. The function first applies a transformation (tf) on
        each tile images prior to stitching. It also merges defined fields of stitched images together into an RGB .png
        file.
    Args:
        MF (str): path to the Main Folder.
        merge_colors (list): list of string of color names: 'red', 'green', 'blue', 'gray', 'cyan', 'magenta', 'yellow'.
        merge_filenames (list): list of string of image files names to merge. Their sequence in the list should match their
            respective color in the 'colors' argument. After stitching they should start with 'img_t1_z1_c ... '.
        tf (fun): image transformation to apply to the tile images prior to stitching.
        preMALDI (bool): whether or not stithcing preMALDI dataset.
        postMALDI (bool): whether or not stithcing postMALDI dataset.

    Data are stored in MF + /Analysis/StitchedMicroscopy/
    """

    if not os.path.exists(MF + 'Analysis/'):
        os.makedirs(MF + 'Analysis/')
        os.mkdir(MF + 'Analysis/StitchedMicroscopy/')

    if preMALDI:

        if not os.path.exists(MF + 'Analysis/StitchedMicroscopy/preMALDI_FLR/'):
            os.makedirs(MF + 'Analysis/StitchedMicroscopy/preMALDI_FLR/')

        tif_files = spaceM.ImageFileManipulation.manipulations.PixFliplr(
            tf,
            MF + 'Input/Microscopy/preMALDI/',
            MF + 'Analysis/StitchedMicroscopy/preMALDI_FLR/')
        spaceM.ImageFileManipulation.FIJIcalls.TileConfFormat(MF + 'Input/Microscopy/preMALDI/',
                                                              MF + 'Analysis/StitchedMicroscopy/preMALDI_FLR/',
                                                              tif_files)
        gc.collect()
        spaceM.ImageFileManipulation.FIJIcalls.callFIJIstitch(MF + 'Analysis/StitchedMicroscopy/preMALDI_FLR/')
        print('Pre-MALDI Stitching finished')

    if postMALDI:

        if not os.path.exists(MF + 'Analysis/StitchedMicroscopy/postMALDI_FLR/'):
            os.makedirs(MF + 'Analysis/StitchedMicroscopy/postMALDI_FLR/')

        tif_files = spaceM.ImageFileManipulation.manipulations.PixFliplr(
            tf,
            MF + 'Input/Microscopy/postMALDI/',
            MF + 'Analysis/StitchedMicroscopy/postMALDI_FLR/')
        spaceM.ImageFileManipulation.FIJIcalls.TileConfFormat(MF + 'Input/Microscopy/postMALDI/',
                                                              MF + 'Analysis/StitchedMicroscopy/postMALDI_FLR/',
                                                              tif_files)
        gc.collect()
        spaceM.ImageFileManipulation.FIJIcalls.callFIJIstitch(MF + 'Analysis/StitchedMicroscopy/postMALDI_FLR/')
        print('Pre-MALDI Stitching finished')


    spaceM.ImageFileManipulation.FIJIcalls.callFIJImergeChannels(
        base_path=MF + 'Analysis/StitchedMicroscopy/preMALDI_FLR/',
        colors=merge_colors,
        filenames=merge_filenames,
        save_filename='Composite.png')

def ablationMarksFinder(MF):
    """Find the ablation marks on the tile images.
    Args:
        MF (str): path to the Main Folder.

    Data are stored in MF + /Analysis/gridFit/
    """

    if not os.path.exists(MF + 'Analysis/gridFit/'):
        os.makedirs(MF + 'Analysis/gridFit/')

    spaceM.Registration.AblationMarkFinder.MarkFinderFT(MF)

def fiducialsFinder(MF):
    """Find the fiducials coordinates on the stitched images.
    Args:
        MF (str): path to the Main Folder.

    Data are stored in MF + /Analysis/Fiducials/
    """

    if not os.path.exists(MF + 'Analysis/Fiducials/'):
        os.makedirs(MF + 'Analysis/Fiducials/')

    spaceM.Registration.ImageRegistration.penMarksFeatures(MF,  prefix='post')
    spaceM.Registration.ImageRegistration.penMarksFeatures(MF,  prefix='pre')

def ablationMarksFilter(MF, marks_check=True):
    """Filters ablation marks. First by re-running the ablation mark detection on the cropped stitched images where the
    ablation marks are. Then by fitting a theoretical grid on the detections and taking only teh closest detection to
    each grid node. This filters out double detections and re-orders the remaning ones into a uniform index which matches
    later on the index of the ion image. The detections after filtering can be visualized in 'ili (https://ili.embl.de/).

    Args:
        MF (str): path to the Main Folder.
        marks_check (bool): whether or not show the results.

    Data are stored in MF + /Analysis/gridFit/
    Visualization are stored in MF + /Analysis/gridFit/marks_check/
    """

    spaceM.Registration.AblationMarkFinder.GridFit(MF)

    if marks_check:

        if not os.path.exists(MF + 'Analysis/gridFit/marks_check/'):
            os.makedirs(MF + 'Analysis/gridFit/marks_check/')

        spaceM.ImageFileManipulation.manipulations.crop2coords(
            MF + 'Analysis/gridFit/xye_clean2.npy',
            MF + 'Analysis/StitchedMicroscopy/postMALDI_FLR/img_t1_z1_c1',
            MF + 'Analysis/gridFit/marks_check/PHASE_crop_bin1x1_window100.png',
            window=100)
        spaceM.ImageFileManipulation.manipulations.crop2coords(
            MF + 'Analysis/gridFit/xye_clean2.npy',
            MF + 'Analysis/StitchedMicroscopy/postMALDI_FLR/img_t1_z1_c1',
            MF + 'Analysis/gridFit/marks_check/PHASE_crop_bin1x1.png',
            window=0)

        nbin = spaceM.ImageFileManipulation.FIJIcalls.imbin4ili(
            MF + 'Analysis/gridFit/marks_check/PHASE_crop_bin1x1.png',
            maxsize=50e6)
        predata = spaceM.WriteILIinput.preCSVdatagen(
            MF + 'Analysis/gridFit/xye_clean2.npy',
            radius=10,
            nbin=nbin,
            PlainFirst=True)
        spaceM.WriteILIinput.writeCSV(
            path=MF + 'Analysis/gridFit/marks_check/ablation_marks_checkDETECTIONS.csv',
            data=predata)

        predata = spaceM.WriteILIinput.preCSVdatagen(
            MF + 'Analysis/gridFit/xye_grid.npy',
            radius=10,
            nbin=nbin,
            PlainFirst=True)
        spaceM.WriteILIinput.writeCSV(
            path=MF + 'Analysis/gridFit/marks_check/ablation_marks_checkTHEORETICAL.csv',
            data=predata)

def registration(MF, tf_obj, ili_only=False, ili_fdr=0.2):

    if not os.path.exists(MF + 'Analysis/Fiducials/optimized_params.npy'):
        spaceM.Registration.ImageRegistration.fiducialsAlignment(MF + 'Analysis/')

    if ili_only==False:
        if not os.path.exists(MF + 'Analysis/Fiducials/transformedMarksMask.npy'):
            spaceM.Registration.AblationMarkFinder.regionGrowingAblationMarks(MF + 'Analysis/')

    if not os.path.exists(MF + 'Analysis/Fiducials/transformedMarksMask.npy'):
        spaceM.Registration.ImageRegistration.TransformMarks(MF + 'Analysis/')

    if not os.path.exists(MF + 'Analysis/ili/'):
        os.makedirs(MF + 'Analysis/ili/')

    if not os.path.exists(MF + 'Analysis/ili/FLUO_crop_bin1x1.png'):
        spaceM.ImageFileManipulation.manipulations.crop2coords(
            MF + 'Analysis/Fiducials/transformedMarks.npy',
            MF + 'Analysis/StitchedMicroscopy/preMALDI_FLR/Composite.png',
            MF + 'Analysis/ili/FLUO_crop_bin1x1.png',
                          window=0)
        spaceM.ImageFileManipulation.manipulations.crop2coords(
            MF + 'Analysis/Fiducials/transformedMarks.npy',
            MF + 'Analysis/StitchedMicroscopy/preMALDI_FLR/Composite.png',
            MF + 'Analysis/ili/FLUO_crop_bin1x1_window100.png',
                          window=100)
        gc.collect()

    nbin = spaceM.ImageFileManipulation.FIJIcalls.imbin4ili(MF + 'Analysis/ili/FLUO_crop_bin1x1.png', maxsize=50e6)
    spaceM.WriteILIinput.annotationSM2CSV(
        MF + 'Analysis/',
        MF + 'Input/',
        fdr=ili_fdr,
        nbin=nbin,
        radius=20,
        tf_obj=tf_obj)

def cellSegmentation(MF,
                     merge_colors,
                     merge_filenames
                     ):

    if not os.path.exists(MF + 'Analysis/CellProfilerAnalysis/'):
        os.makedirs(MF + 'Analysis/CellProfilerAnalysis/')

    CP_window = 100
    spaceM.ImageFileManipulation.manipulations.crop2coords4CP(
        MF + 'Analysis/Fiducials/transformedMarks.npy',
        MF + 'Analysis/StitchedMicroscopy/preMALDI_FLR/',
        MF + 'Analysis/CellProfilerAnalysis/',
        window=CP_window)
    spaceM.ImageFileManipulation.FIJIcalls.callFIJImergeChannels(
        base_path=MF + 'Analysis/CellProfilerAnalysis/',
        colors=merge_colors,
        filenames=merge_filenames,
        save_filename='Composite_window100_adjusted.png')
    gc.collect()

    spaceM.ImageFileManipulation.manipulations.imAdjQuantiles(pc=0.01,
                                                              im_p=MF + 'Analysis/CellProfilerAnalysis/img_t1_z1_c2.tif',
                                                              adj_p=MF + 'Analysis/CellProfilerAnalysis/img_t1_z1_c2_adjusted.tif')
    print('Start CellProfiler Anlalysis')
    cp_p = getPath('CellProfiler path')
    cppipe_p = getPath('CellProfiler pipeline path')
    spaceM.scAnalysis.Segmentation.callCP(MF + 'Analysis/', cp_p, cppipe_p)
    print('Finished CellProfiler Anlalysis')

    spaceM.scAnalysis.Segmentation.cellOutlines(MF + 'Analysis/CellProfilerAnalysis/Composite_window100_adjusted.png',
                             CP_window,
                             MF + 'Analysis/CellProfilerAnalysis/Labelled_cells.tif',
                             MF + 'Analysis/CellProfilerAnalysis/Contour_cells_adjusted.png')

def spatioMolecularMatrix(MF, tf_obj, CDs=[0.75]):

    if not os.path.exists(MF + 'Analysis/scAnalysis/'):
        os.makedirs(MF + 'Analysis/scAnalysis/')

    spaceM.scAnalysis.scAnalysis.defMORPHfeatures(MF)
    fetch_ann = 'online' # either 'online' or 'offline'
    filter = 'mean'  # either 'mean' or 'correlation'
    tol_fact = -0.2

    spaceM.scAnalysis.scAnalysis.defMOLfeatures(
        MF,
        tf_obj=tf_obj,
        CDs=CDs,
        norm_method='weighted_mean_sampling_area_MarkCell_overlap_ratio_sampling_area',
        fetch_ann=fetch_ann, tol_fact=tol_fact, filter=filter)

    spaceM.scAnalysis.scAnalysis.mergeMORPHnMOL4cyt(
        MF,
        CDs=CDs,
        fetch_ann=fetch_ann,
        tol_fact=tol_fact,
        filter=filter)