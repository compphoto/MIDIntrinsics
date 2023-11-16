# MIDIntrinsics Dataset

Repo for the intrinsic component extension of MIT Multi-Illumination Dataset proposed in the paper "Intrinsic Image Decomposition via Ordinal Shading", [Chris Careaga](https://ccareaga.github.io/) and [Yağız Aksoy](https://yaksoy.github.io) , ACM Transactions on Graphics, 2023 
### [Project Page](https://yaksoy.github.io/intrinsic) | [Paper]() | [Video]() | [Supplementary]() | [Data]()

![examples](https://github.com/compphoto/MIDIntrinsics/assets/3434597/9682d854-2c75-42c8-a970-afaa85ab49a7)

### Downloading the data
In order to compute intrinsic components for each image in MID, you must first download [the original dataset](https://projects.csail.mit.edu/illumination/). We provide the linear albedo images created from the HDR images in the dataset after white-balancing and tonemapping. You can use `wget` to download the zip archives:

```
wget https://data.csail.mit.edu/multilum/multi_illumination_test_mip2_exr.zip
wget https://data.csail.mit.edu/multilum/multi_illumination_train_mip2_exr.zip
```
We provide a single albedo image for each scene, these can be downloaded [here]() or fetched via:

```
wget 
```

The albedo images follow the same directory structure as the original dataset, and can be unzipped into the proper directories. Since the albedo is computed from the tonemapped images, the shading images should be computed using the tonemapped images as well. We use the simple [tonemapping function](https://github.com/CCareaga/chrislib/blob/667ddf1853683cfcfa21c9fcc435b92b2487e9b1/chrislib/general.py#L437-L479) used by rendered datasets. The shading can be computed as:
```
tm_scale = get_tonemap_scale(img)
tm_img = (tm_scale * img).clip(0, 1)
shading = tm_img / albedo
```
This will generate a three-channel shading image. For training intrinsic decomposition methods that use the grayscale shading assumption, the shading images can be desaturated using a function [like this](https://github.com/CCareaga/chrislib/blob/667ddf1853683cfcfa21c9fcc435b92b2487e9b1/chrislib/general.py#L284C1-L306C22). There are then two options for dealing with the desaturation. You can either push the color into the albedo image, ensuring that the input image is maintained and reconstructed, at the cost of each image potentially having slightly different albedo ground-truth:
```
new_albedo = tm_img / grey_shading
```
Or you can re-synthetize the input image from the original albedo and the grayscale shading:
```
new_img = albedo * grey_shading
```
This will essentially white-balance the input image and remove/alter any non-grayscale lighting effects captured by the three-channel shading (e.g. shadows, specularity, etc.). It will however ensure that each image shares a single albedo component.

### Generating the data

Alternatively, you can use our pipeline to re-generate the albedo estimations in case you want more flexibility. To do this you can download the original dataset in the same way. Then you can install our [intrinsic decomposition pipeline](https://github.com/compphoto/Intrinsic):
```
pip install https://github.com/compphoto/Intrinsic/archive/master.zip
```
To generate the albedo estimations, you can run the `generate_albedo` script and point it to the downloaded multi-illumination data:
```
python generate_albedo.py <MULTI_ILLUM_PATH>
```
The images will be white-balanced using the light probe, tonemapped, decomposed using our method and the median albedo will be computed. Each albedo will be stored along side the HDR images. 

### Citation
This implementation is provided for academic use only. Please cite our paper if you use this code or dataset:

```
@ARTICLE{careagaIntrinsic,
  author={Chris Careaga and Ya\u{g}{\i}z Aksoy},
  title={Intrinsic Image Decomposition via Ordinal Shading},
  journal={ACM Trans. Graph.},
  year={2023},
}
```
