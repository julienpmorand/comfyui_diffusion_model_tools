import os

import torch

import folder_paths
import comfy.sd
import comfy.utils


IMAGE_TAES = ["taesd", "taesdxl", "taesd3", "taef1", "taef2"]
VIDEO_TAES = ["taehv", "lighttaew2_2", "lighttaew2_1", "lighttaehy1_5", "taeltx_2"]
CLIP_TYPES = [
    "stable_diffusion",
    "stable_cascade",
    "sd3",
    "stable_audio",
    "mochi",
    "ltxv",
    "pixart",
    "cosmos",
    "lumina2",
    "wan",
    "hidream",
    "chroma",
    "ace",
    "omnigen2",
    "qwen_image",
    "hunyuan_image",
    "flux2",
    "ovis",
    "longcat_image",
    "cogvideox",
    "lens",
    "pixeldit",
    "ideogram4",
]


def _get_filename_list(folder_name):
    try:
        return folder_paths.get_filename_list(folder_name)
    except Exception:
        return []


def _get_full_path(folder_name, filename):
    try:
        return folder_paths.get_full_path(folder_name, filename)
    except Exception:
        return None


def _get_full_path_or_raise(folder_name, filename):
    try:
        return folder_paths.get_full_path_or_raise(folder_name, filename)
    except AttributeError:
        path = _get_full_path(folder_name, filename)
        if path is None:
            raise FileNotFoundError(f"File not found in {folder_name}: {filename}")
        return path


def _get_vae_names():
    vaes = list(_get_filename_list("vae"))
    approx_vaes = _get_filename_list("vae_approx")
    have_img_encoder = set()
    have_img_decoder = set()

    for vae_name in approx_vaes:
        parts = vae_name.split("_", 1)
        if len(parts) != 2 or parts[0] not in IMAGE_TAES:
            for tae_name in VIDEO_TAES:
                if vae_name.startswith(tae_name):
                    vaes.append(vae_name)
                    break
            continue

        if parts[1].startswith("encoder."):
            have_img_encoder.add(parts[0])
        elif parts[1].startswith("decoder."):
            have_img_decoder.add(parts[0])

    vaes.extend(sorted(have_img_encoder.intersection(have_img_decoder)))
    vaes.append("pixel_space")
    return vaes


def _load_taesd(vae_name):
    sd = {}
    approx_vaes = _get_filename_list("vae_approx")

    try:
        encoder = next(v for v in approx_vaes if v.startswith(f"{vae_name}_encoder."))
        decoder = next(v for v in approx_vaes if v.startswith(f"{vae_name}_decoder."))
    except StopIteration as exc:
        raise FileNotFoundError(
            f"Missing encoder/decoder files for approximate VAE: {vae_name}"
        ) from exc

    enc = comfy.utils.load_torch_file(_get_full_path_or_raise("vae_approx", encoder))
    for key in enc:
        sd[f"taesd_encoder.{key}"] = enc[key]

    dec = comfy.utils.load_torch_file(_get_full_path_or_raise("vae_approx", decoder))
    for key in dec:
        sd[f"taesd_decoder.{key}"] = dec[key]

    if vae_name == "taesd":
        sd["vae_scale"] = torch.tensor(0.18215)
        sd["vae_shift"] = torch.tensor(0.0)
    elif vae_name == "taesdxl":
        sd["vae_scale"] = torch.tensor(0.13025)
        sd["vae_shift"] = torch.tensor(0.0)
    elif vae_name == "taesd3":
        sd["vae_scale"] = torch.tensor(1.5305)
        sd["vae_shift"] = torch.tensor(0.0609)
    elif vae_name == "taef1":
        sd["vae_scale"] = torch.tensor(0.3611)
        sd["vae_shift"] = torch.tensor(0.1159)

    return sd


def _get_clip_folder_names():
    # Current ComfyUI uses text_encoders. Older installs/custom forks may still expose clip.
    return ("text_encoders", "clip")


def _get_clip_names():
    names = []
    seen = set()

    for folder_name in _get_clip_folder_names():
        for clip_name in _get_filename_list(folder_name):
            if clip_name not in seen:
                names.append(clip_name)
                seen.add(clip_name)

    return names


def _get_clip_full_path_or_raise(clip_name):
    for folder_name in _get_clip_folder_names():
        path = _get_full_path(folder_name, clip_name)
        if path is not None:
            return path

    raise FileNotFoundError(f"CLIP/text encoder not found: {clip_name}")


class DiffusionModelNames:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": (folder_paths.get_filename_list("diffusion_models"),),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("model_name",)
    FUNCTION = "get_name"
    CATEGORY = "utils/diffusion"

    def get_name(self, model_name):
        return (model_name,)


class LoadDiffusionModelByName:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": ("STRING",),
                "weight_dtype": (
                    [
                        "default",
                        "fp8_e4m3fn",
                        "fp8_e5m2",
                    ],
                ),
            }
        }

    RETURN_TYPES = ("MODEL",)
    RETURN_NAMES = ("model",)
    FUNCTION = "load_model"
    CATEGORY = "utils/diffusion"

    def load_model(self, model_name, weight_dtype):
        model_path = folder_paths.get_full_path("diffusion_models", model_name)

        if model_path is None:
            raise FileNotFoundError(f"Diffusion model not found: {model_name}")

        model_options = {}
        if weight_dtype != "default":
            model_options["dtype"] = weight_dtype

        model = comfy.sd.load_diffusion_model(
            model_path,
            model_options=model_options,
        )

        return (model,)


class VAENames:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "vae_name": (_get_vae_names(),),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("vae_name",)
    FUNCTION = "get_name"
    CATEGORY = "utils/vae"

    def get_name(self, vae_name):
        return (vae_name,)


class LoadVAEByName:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "vae_name": ("STRING",),
            }
        }

    RETURN_TYPES = ("VAE",)
    RETURN_NAMES = ("vae",)
    FUNCTION = "load_vae"
    CATEGORY = "utils/vae"

    def load_vae(self, vae_name):
        metadata = None
        vae_path = None

        if vae_name == "pixel_space":
            sd = {"pixel_space_vae": torch.tensor(1.0)}
        elif vae_name in IMAGE_TAES:
            sd = _load_taesd(vae_name)
        else:
            if os.path.splitext(vae_name)[0] in VIDEO_TAES:
                vae_path = _get_full_path_or_raise("vae_approx", vae_name)
            else:
                vae_path = _get_full_path_or_raise("vae", vae_name)

            sd, metadata = comfy.utils.load_torch_file(vae_path, return_metadata=True)

        if vae_name == "taef2":
            if metadata is None:
                metadata = {"tae_latent_channels": 128}
            else:
                metadata["tae_latent_channels"] = 128

        vae = comfy.sd.VAE(sd=sd, metadata=metadata)

        if hasattr(vae, "throw_exception_if_invalid"):
            vae.throw_exception_if_invalid()

        if vae_path is not None and hasattr(vae, "patcher") and hasattr(comfy.sd, "load_vae_patcher"):
            vae.patcher.cached_patcher_init = (
                comfy.sd.load_vae_patcher,
                (vae_path, metadata, None),
            )

        return (vae,)


class CLIPNames:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip_name": (_get_clip_names(),),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("clip_name",)
    FUNCTION = "get_name"
    CATEGORY = "utils/clip"

    def get_name(self, clip_name):
        return (clip_name,)


class LoadCLIPByName:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip_name": ("STRING",),
                "type": (CLIP_TYPES,),
            },
            "optional": {
                "device": (["default", "cpu"], {"advanced": True}),
            },
        }

    RETURN_TYPES = ("CLIP",)
    RETURN_NAMES = ("clip",)
    FUNCTION = "load_clip"
    CATEGORY = "utils/clip"

    def load_clip(self, clip_name, type="stable_diffusion", device="default"):
        clip_type = getattr(
            comfy.sd.CLIPType,
            type.upper(),
            comfy.sd.CLIPType.STABLE_DIFFUSION,
        )

        model_options = {}
        if device == "cpu":
            model_options["load_device"] = model_options["offload_device"] = torch.device("cpu")

        clip_path = _get_clip_full_path_or_raise(clip_name)
        clip = comfy.sd.load_clip(
            ckpt_paths=[clip_path],
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
            clip_type=clip_type,
            model_options=model_options,
        )

        return (clip,)


NODE_CLASS_MAPPINGS = {
    "DiffusionModelNames": DiffusionModelNames,
    "LoadDiffusionModelByName": LoadDiffusionModelByName,
    "VAENames": VAENames,
    "LoadVAEByName": LoadVAEByName,
    "CLIPNames": CLIPNames,
    "LoadCLIPByName": LoadCLIPByName,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DiffusionModelNames": "Diffusion Model Names",
    "LoadDiffusionModelByName": "Load Diffusion Model By Name",
    "VAENames": "VAE Names",
    "LoadVAEByName": "Load VAE By Name",
    "CLIPNames": "Clip Names",
    "LoadCLIPByName": "Load Clip By Name",
}
