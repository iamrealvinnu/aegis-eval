import logging
import re

# Initialize load and generate as None
# I'm doing this so I don't get NameErrors if the MLX imports fail on a non-Mac machine.
load = None
generate = None
make_sampler = None

try:
    import mlx.core as mx
    import mlx.nn as nn
    from mlx_lm import load, generate
    try:
        from mlx_lm.sample_utils import make_sampler
    except ImportError:
        # Fallback for older versions where sampling was internal to generate
        make_sampler = None
except ImportError:
    logging.warning("MLX not found. Inference will fail unless running on Apple Silicon with MLX installed.")
except Exception as e:
    logging.warning(f"Error importing MLX libraries: {e}")

logger = logging.getLogger("Aegis-Model-Interface")

class MLXEngine:
    def __init__(self, model_path: str, max_tokens: int = 512, system_prompt: str = ""):
        """
        Initializes the MLX engine for local inference.
        """
        self.model_path = model_path
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.model = None
        self.tokenizer = None
        
        if load is None:
            # If we're here, it means MLX didn't load properly. I'll switch to MOCK MODE
            # so the rest of the pipeline can still be tested without weights.
            logger.warning("MLX 'load' function not available. Engine will run in MOCK MODE.")
            return

        logger.info(f"Loading local weights from {model_path} into unified memory...")
        try:
            # This is the actual weight loading part. Can take a few seconds depending on the model size.
            self.model, self.tokenizer = load(model_path)
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load MLX model: {e}")

    def _extract_code(self, text: str) -> str:
        """
        This part is crucial. Models love to wrap their code in markdown blocks or
        add conversational fluff. I'm using regex and some basic string parsing
        to strip all that away so only valid Python reaches the sandbox.
        """
        # First, try to grab anything inside triple backticks
        pattern = r"```(?:python)?\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            # If there are multiple blocks, I'll take the longest one. Usually the main script.
            return max(matches, key=len).strip()
        
        # If no markdown blocks, I'll try to find where the code actually starts
        lines = text.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if line.strip().startswith(('def ', 'import ', 'from ', 'class ', '#')):
                in_code = True
            if in_code:
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines).strip()
            
        return text.strip()

    def generate_code(self, prompt: str, temperature: float = 0.2) -> str:
        """
        Generates code modifications based on the prompt.
        """
        logger.debug("Generating code iteration...")
        
        # I'm using the Llama 3 format here. If I change models, I might need to tweak these tags.
        if self.system_prompt:
            full_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{self.system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        else:
            full_prompt = f"<s>[INST] {prompt} [/INST]"
        
        if not self.model or generate is None:
            # Fallback for testing: return a timestamped string to avoid triggering the loop detector
            import time
            return f"print('Mocked code generation for testing at {time.time()}')"

        # Setting up the arguments for the mlx_lm.generate call
        gen_kwargs = {
            "model": self.model,
            "tokenizer": self.tokenizer,
            "prompt": full_prompt,
            "max_tokens": self.max_tokens,
            "verbose": False,
        }

        # Dealing with the API changes in mlx-lm versions
        if make_sampler is not None:
            gen_kwargs["sampler"] = make_sampler(temp=temperature)
        else:
            # Fallback for older versions that used 'temp' or 'temperature' directly
            gen_kwargs["temp"] = temperature

        try:
            # Fire off the inference
            response = generate(**gen_kwargs)
            # Clean it up before sending to the orchestrator
            extracted = self._extract_code(response)
            return extracted
        except TypeError as te:
            # I added this fallback because the mlx-lm internal API can be a bit inconsistent
            error_msg = str(te)
            if "unexpected keyword argument" in error_msg:
                logger.warning(f"Detected API mismatch: {error_msg}. Attempting final fallback...")
                # Strip all sampling args and just go for greedy decoding
                gen_kwargs.pop("sampler", None)
                gen_kwargs.pop("temp", None)
                gen_kwargs.pop("temperature", None)
                try:
                    response = generate(**gen_kwargs)
                    return self._extract_code(response.strip())
                except Exception as e:
                    logger.error(f"Inference failure after all fallbacks: {e}")
            else:
                logger.error(f"Type error during inference: {te}")
            return ""
        except Exception as e:
            logger.error(f"Inference failure: {e}")
            return ""
