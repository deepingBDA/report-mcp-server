#!/usr/bin/env python3
"""
GPT-5 계열 모델들을 temperature 없이 테스트
"""

import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# GPT-5 계열 모델들 (temperature 없이)
gpt5_models = [
    "gpt-5",
    "gpt-5-mini", 
    "gpt-5-turbo",
    "gpt-5-preview",
    "o3-mini"  # 최신 모델도 시도
]

def test_model_no_temp(model_name):
    """temperature 없이 모델 테스트"""
    try:
        # temperature 파라미터 제거
        llm = ChatOpenAI(model=model_name, timeout=10)
        
        start_time = time.perf_counter()
        response = llm.invoke("간단히 'OK'라고만 답해주세요.")
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        return True, duration, response.content[:50]
        
    except Exception as e:
        return False, None, str(e)[:150]

def main():
    print("🔍 GPT-5 계열 모델 테스트 (temperature 없이)")
    print("=" * 60)
    
    working_models = []
    
    for model in gpt5_models:
        print(f"\n🧪 {model} 테스트 중...", end="")
        
        available, duration, response = test_model_no_temp(model)
        
        if available:
            print(f" ✅")
            print(f"   응답 시간: {duration:.2f}초")
            print(f"   응답: {response}")
            working_models.append((model, duration))
        else:
            print(f" ❌")
            print(f"   오류: {response}")
    
    # 결과
    if working_models:
        print("\n" + "=" * 60)
        print("📊 사용 가능한 GPT-5 계열 모델들:")
        print("-" * 60)
        
        working_models.sort(key=lambda x: x[1])
        
        for i, (model, duration) in enumerate(working_models, 1):
            print(f"{i}. {model:<15} {duration:6.2f}초")
            
        print(f"\n🚀 추천: {working_models[0][0]} (가장 빠름)")
    else:
        print("\n❌ 사용 가능한 GPT-5 계열 모델이 없습니다.")
        print("💡 대안: gpt-4o-mini (0.46초, 빠르고 안정적)")

if __name__ == "__main__":
    main()