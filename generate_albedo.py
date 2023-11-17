# script to generate the albedo components for a set of multi-illumination scenes.

import os
import cv2
import numpy as np
import argparse
import imageio

from chrislib.general import (
    get_tonemap_scale, 
    match_scale, 
    show,
    get_brightness,
    view
)
from chrislib.data_util import np_to_pil

from intrinsic.pipeline import run_pipeline
from intrinsic.model_util import load_models

# this is set so that opencv can load exr files
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

def process_scene(root_dir, scene_name, models, tonemap=True, save_imgs=False, png=False):
    
    images = []
    albedos = []
    
    for img_idx in range(0, 25):
        img = cv2.imread(f'{root_dir}/{scene_name}/dir_{img_idx}_mip2.exr', cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)[:, :, ::-1]
        prb = cv2.imread(f'{root_dir}/{scene_name}/probes/dir_{img_idx}_gray256.exr', cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)[:, :, ::-1]
        
        # create a mask of only valid pixels on the probe, then add a border and erode
        # this is to avoid color spill on the edges of the light probe
        prb_msk = np.any((prb > 0.01), axis=-1)
        prb_msk = np.pad(prb_msk, pad_width=1, mode='constant', constant_values=0)[:, :, None]
        prb_msk = cv2.erode(prb_msk.astype(np.uint8), np.ones((11, 11), np.uint8))
        prb_msk = prb_msk[1:-1, 1:-1].astype(bool)
        
        # now mask the probe to get valid RGB pixel values and take the median
        prb_pix = prb[prb_msk, :]
        prb_med = np.median(prb_pix, axis=0)
        
        # get ration of green-red and green-blue
        r_ratio = prb_med[1] / prb_med[0]
        b_ratio = prb_med[1] / prb_med[2]
        
        # create coeffs to scale the red and blue channels and leave green
        wb_coeffs = np.array([r_ratio, 1.0, b_ratio]).reshape(1, 1, 3)
        
        wb_img = img * wb_coeffs
        
        if tonemap:
            tm_scale = get_tonemap_scale(wb_img)
            tm_img = (tm_scale * wb_img).clip(0, 1)
        else:
            tm_img = wb_img.clip(0)
        
        images.append(tm_img)

        # if the image is in the skip list, we don't use it for the albedo computation
        # but the user may want to save the white-balanced and preprocessed version
        if img_idx in SKIP_LIST:
            continue
        
        # run our pipeline, image already linear, and keep size the same
        result = run_pipeline(
            models,
            tm_img.astype(np.float32),
            resize_conf=0.0,
            linear=True,
            maintain_size=True
        )
        
        alb = result['albedo']
        
        albedos.append(alb)
    
    matched = [albedos[0]]
    for alb in albedos[1:]:
        matched.append(match_scale(alb, albedos[0]))
        
    med_alb = np.median(matched, axis=0)
    
    # if we are saving as png min-max norm to ensure the albedo is between [0-1]
    if png:
        np_to_pil(med_alb / med_alb.max()).save(f'{root_dir}/{scene_name}/albedo.png')
    else:    
        imageio.imwrite(f'{root_dir}/{scene_name}/albedo.exr', med_alb)

    # if the user is saving the images, we write them out as PNGs
    if save_imgs:
        for idx, img in enumerate(images):
            np_to_pil(img).save(f'{root_dir}/{scene_name}/dir_{img_idx}_mip2.png')
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--mid_path", type=str, help="path to the Multi-Illumination Dataset (train or test)")
    parser.add_argument("--weights_path", type=str, default='./weights', help="path to the model weights for the intrinsic pipeline")
    parser.add_argument("--save_imgs", action="store_true", help="whether or not to save preprocessed images as PNG")
    parser.add_argument("--png", action="store_true", help="whether or not to save output as PNGs by default the albedo is saved as EXR")
    args = parser.parse_args()
    
    # this is a list of indices to skip when computing the median albedo
    # this helps avoid any bias from images with a hard flash and saturated pixels
    SKIP_LIST = [2, 3, 20, 21, 24]
    
    # load model weights (only trained on rendered datasets) 
    models = load_models(
        ord_path = f'{args.weights_path}/radiant_pond_314_400.pt',
        iid_path = f'{args.weights_path}/deft_snowflake_134_200.pt'
    )
    
    scenes = os.listdir(args.mid_path)
    num_scenes = len(scenes)
    print(f'found {num_scenes} scenes')
    
    # for each scene run median albedo computation and save outputs
    for i, scene_name in enumerate(scenes):
        process_scene(
            args.mid_path, 
            scene_name, 
            models, 
            save_imgs=args.save_imgs,
            png=args.png
        )
        print(f'({i + 1} / {num_scenes}) - processed {scene_name}')
