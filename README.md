# ComfyUI Diffusion Model Tools

Small ComfyUI custom node pack for selecting model-related files by name and loading them only when they are actually needed by the workflow.

This is useful when you build reusable or conditional workflows where a model, VAE, or CLIP/text encoder should be selectable by name, passed around as a string, and loaded later only if that branch of the graph is used.

## Why this exists

ComfyUI's built-in model loader nodes usually expose file pickers directly on the loader node. That is great for normal workflows, but it can be awkward when you want to separate **selecting a file name** from **loading the actual model object**.

This node pack splits those two steps:

1. A `Names` node returns the selected file name as a `STRING`.
2. A `Load ... By Name` node receives that string and loads the corresponding ComfyUI object.

That makes it easier to build workflows where loading is conditional. For example, if a branch is not executed, the loader node in that branch does not need to run, which can avoid unnecessary model loading, memory usage, and startup overhead.

## Nodes

### Diffusion models

#### Diffusion Model Names

Returns the selected diffusion model file name as a `STRING`.

The list comes from ComfyUI's `diffusion_models` folder.

**Output:**

| Name | Type | Description |
| --- | --- | --- |
| `model_name` | `STRING` | The selected diffusion model file name. |

#### Load Diffusion Model By Name

Loads a diffusion model from a `STRING` model name.

This is similar in spirit to ComfyUI's diffusion model loader, but the model file is selected through a string input instead of directly through the loader widget.

**Inputs:**

| Name | Type | Description |
| --- | --- | --- |
| `model_name` | `STRING` | Diffusion model file name, usually from `Diffusion Model Names`. |
| `weight_dtype` | dropdown | Weight dtype option passed to ComfyUI's diffusion model loader. |

**Output:**

| Name | Type | Description |
| --- | --- | --- |
| `model` | `MODEL` | Loaded diffusion model. |

### VAE

#### VAE Names

Returns the selected VAE name as a `STRING`.

The list follows ComfyUI's VAE loader semantics and can include:

- regular VAE files from the `vae` folder
- approximate VAE files from `vae_approx`
- supported TAESD-style VAE names when matching encoder/decoder files are available
- supported video approximate VAE files
- `pixel_space`

**Output:**

| Name | Type | Description |
| --- | --- | --- |
| `vae_name` | `STRING` | The selected VAE name. |

#### Load VAE By Name

Loads a VAE from a `STRING` VAE name.

This node is useful when a workflow should choose between different VAEs, approximate VAEs, or `pixel_space` without forcing all possible VAEs to load.

**Input:**

| Name | Type | Description |
| --- | --- | --- |
| `vae_name` | `STRING` | VAE name, usually from `VAE Names`. |

**Output:**

| Name | Type | Description |
| --- | --- | --- |
| `vae` | `VAE` | Loaded VAE. |

### CLIP / text encoders

#### Clip Names

Returns the selected CLIP/text encoder file name as a `STRING`.

The node checks ComfyUI's current `text_encoders` folder semantics and also supports older/custom setups that expose files through a `clip` folder.

**Output:**

| Name | Type | Description |
| --- | --- | --- |
| `clip_name` | `STRING` | The selected CLIP/text encoder file name. |

#### Clip Type Names

Returns the selected CLIP type as a `STRING`.

This is useful when the CLIP type needs to be selected in one place and passed into a loader later, the same way model, VAE, and CLIP file names can be passed around as strings.

The available values mirror ComfyUI's built-in `CLIPLoader` type list, such as:

- `stable_diffusion`
- `stable_cascade`
- `sd3`
- `lumina2`
- `wan`
- `qwen_image`
- `flux2`

**Output:**

| Name | Type | Description |
| --- | --- | --- |
| `clip_type` | `STRING` | The selected CLIP type name. |

#### Load Clip By Name

Loads a CLIP/text encoder from a `STRING` file name.

This follows ComfyUI's CLIP loader style by using a CLIP type and the configured embeddings directory. The node still has a normal `type` dropdown for simple workflows, but it also accepts an optional `clip_type` string input. When `clip_type` is connected, it overrides the dropdown value.

**Inputs:**

| Name | Type | Description |
| --- | --- | --- |
| `clip_name` | `STRING` | CLIP/text encoder file name, usually from `Clip Names`. |
| `type` | dropdown | Fallback CLIP type, such as `stable_diffusion`, `sd3`, `flux2`, and other ComfyUI-supported types. Used when `clip_type` is not connected. |
| `clip_type` | `STRING`, optional | CLIP type string, usually from `Clip Type Names`. If connected, this overrides the `type` dropdown. |
| `device` | dropdown, advanced | `default` or `cpu`. Use `cpu` if you specifically want to force CLIP loading on CPU. |

**Output:**

| Name | Type | Description |
| --- | --- | --- |
| `clip` | `CLIP` | Loaded CLIP/text encoder. |

## Typical use cases

### Optional model loading

Use a `Names` node to select a file, then connect its string output into a loader only inside the branch that needs that model.

This is helpful when building workflows with optional branches, switches, bypasses, or reusable groups where not every selected model should be loaded every time.

### Reusable workflow templates

Instead of hard-wiring a loader widget everywhere, you can pass model names through your workflow as strings. This can make complex templates easier to maintain.

For example:

```text
Diffusion Model Names -> Load Diffusion Model By Name -> sampler branch
VAE Names             -> Load VAE By Name             -> decode branch
Clip Names            -> Load Clip By Name            -> conditioning branch
Clip Type Names       -> Load Clip By Name            -> conditioning branch type
```

### Avoiding unnecessary memory pressure

Large models, VAEs, and text encoders can consume significant memory. Splitting selection from loading can help avoid loading assets in workflow paths that are not used.

This does not replace ComfyUI's own model management, and it does not guarantee that memory will be freed immediately. It simply gives the workflow graph more control over when a loader node needs to execute.

## Installation

Clone or copy this repository into your ComfyUI `custom_nodes` directory:

```bash
git clone https://github.com/julienpmorand/comfyui_diffusion_model_tools.git ComfyUI/custom_nodes/comfyui_diffusion_model_tools
```

Then restart ComfyUI.

## Model folders

These nodes use the same model folders ComfyUI normally uses:

| Asset type | Folder |
| --- | --- |
| Diffusion models | `models/diffusion_models` |
| VAE files | `models/vae` |
| Approximate VAE files | `models/vae_approx` |
| CLIP/text encoders | `models/text_encoders` |
| Older/custom CLIP setups | `models/clip` |
| Embeddings | `models/embeddings` |

Your exact paths may vary depending on your ComfyUI installation and `extra_model_paths.yaml` configuration.

## Node category

The nodes appear under:

```text
utils/diffusion
utils/vae
utils/clip
```

## Notes and limitations

- The `Names` nodes only output strings. They do not load the actual model asset.
- The `Load ... By Name` nodes perform the actual loading.
- If a name does not exist in the expected ComfyUI folder, the loader raises a file-not-found error.
- The CLIP loader requires the correct CLIP type for the selected text encoder. Use `Clip Type Names` when you want that type to be selected/passed through the graph as a string.
- The benefit is mostly seen in conditional, modular, or reusable workflows. In a simple linear workflow, the built-in ComfyUI loader nodes may be enough.

## Included nodes

- `Diffusion Model Names`
- `Load Diffusion Model By Name`
- `VAE Names`
- `Load VAE By Name`
- `Clip Names`
- `Clip Type Names`
- `Load Clip By Name`
