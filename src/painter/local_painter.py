import torch
from diffusers import FluxPipeline
import os
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# CUDA 메모리 파편화 방지 설정
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

class LocalPainter:
    def __init__(self, model_id="black-forest-labs/FLUX.1-schnell"):
        self.hf_token = os.getenv("HF_TOKEN")
        print(f"[*] 모델 로드 중 (최강 최적화 모드)...")
        
        try:
            # bfloat16으로 정밀도 유지하며 용량 절반으로 축소
            self.pipe = FluxPipeline.from_pretrained(
                model_id, 
                torch_dtype=torch.bfloat16,
                token=self.hf_token
            )
            
            # 가장 강력한 메모리 절약 기법: 레이어 단위로 GPU/CPU 교체
            # 이 기능을 쓰면 16GB VRAM에서 FLUX를 안전하게 돌릴 수 있습니다.
            self.pipe.enable_sequential_cpu_offload()
            
            print("[+] FLUX 엔진 준비 완료!")
        except Exception as e:
            print(f"[!] 엔진 로드 실패: {str(e)}")
            self.pipe = None

    def generate_image(self, prompt, output_name=None):
        if not self.pipe:
            print("[!] 엔진이 로드되지 않았습니다.")
            return None

        if output_name is None:
            output_name = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        os.makedirs("data/images", exist_ok=True)
        file_path = os.path.join("data/images", output_name)

        print(f"[*] FLUX 이미지 생성 시작 (최적화 모드 구동)...")
        
        try:
            # GPU 캐시 정리
            torch.cuda.empty_cache()
            
            with torch.inference_mode():
                image = self.pipe(
                    prompt,
                    guidance_scale=0.0,
                    num_inference_steps=4,
                    max_sequence_length=256,
                    generator=torch.Generator(device="cuda").manual_seed(42)
                ).images[0]

            image.save(file_path)
            print(f"[+] 이미지 생성 및 저장 완료: {file_path}")
            return file_path
        except Exception as e:
            print(f"[!] 이미지 생성 실패: {str(e)}")
            return None

if __name__ == "__main__":
    painter = LocalPainter()
    # Claude가 추천한 고퀄리티 프롬프트
    test_prompt = "A high-quality 3D medical illustration of vitamin D and K2 capsules. Showing healthy bone structure and clear arterial pathways, cinematic lighting, professional medical blog style, 8k resolution."
    painter.generate_image(test_prompt, "flux_success_thumb.png")
