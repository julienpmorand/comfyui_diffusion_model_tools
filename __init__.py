import os

import folder_paths
import comfy.sd


class DiffusionModelNames:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": (
                    folder_paths.get_filename_list("diffusion_models"),
                ),
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

        model_path = folder_paths.get_full_path(
            "diffusion_models",
            model_name
        )

        if model_path is None:
            raise Exception(
                f"Diffusion model not found: {model_name}"
            )

        model_options = {}

        if weight_dtype != "default":
            model_options["dtype"] = weight_dtype

        model = comfy.sd.load_diffusion_model(
            model_path,
            model_options=model_options
        )

        return (model,)


NODE_CLASS_MAPPINGS = {
    "DiffusionModelNames": DiffusionModelNames,
    "LoadDiffusionModelByName": LoadDiffusionModelByName,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DiffusionModelNames": "Diffusion Model Names",
    "LoadDiffusionModelByName": "Load Diffusion Model By Name",
}
