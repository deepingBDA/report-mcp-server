#!/usr/bin/env python3
"""
LangChain ChatOpenAI에서 사용 가능한 모델들 테스트
"""

import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# 테스트할 모델들 (GPT-5 계열 포함)
test_models = [
    "gpt-5",
    "gpt-5-turbo", 
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo"
]

def test_model_availability(model_name):
    """모델 사용 가능 여부와 응답 시간 테스트"""
    try:
        llm = ChatOpenAI(model=model_name, temperature=0.1, timeout=10)
        
        start_time = time.perf_counter()
        response = llm.invoke("간단히 'OK'라고만 답해주세요.")
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        return True, duration, response.content[:50]
        
    except Exception as e:
        return False, None, str(e)[:100]

def main():
    print("🔍 LangChain ChatOpenAI 모델 가용성 테스트")
    print("=" * 70)
    
    available_models = []
    
    for model in test_models:
        print(f"\n🧪 {model} 테스트 중...", end="")
        
        available, duration, response = test_model_availability(model)
        
        if available:
            print(f" ✅")
            print(f"   응답 시간: {duration:.2f}초")
            print(f"   응답: {response}")
            available_models.append((model, duration))
        else:
            print(f" ❌")
            print(f"   오류: {response}")
    
    # 결과 요약
    if available_models:
        print("\n" + "=" * 70)
        print("📊 사용 가능한 모델들 (빠른 순):")
        print("-" * 70)
        
        available_models.sort(key=lambda x: x[1])  # 응답 시간순 정렬
        
        for i, (model, duration) in enumerate(available_models, 1):
            print(f"{i:2d}. {model:<20} {duration:6.2f}초")
            
        print(f"\n💡 가장 빠른 모델: {available_models[0][0]} ({available_models[0][1]:.2f}초)")
        
        # GPT-5 계열 모델 필터링
        gpt5_models = [(m, d) for m, d in available_models if m.startswith('gpt-5')]
        if gpt5_models:
            print(f"🚀 GPT-5 계열에서 가장 빠른 모델: {gpt5_models[0][0]} ({gpt5_models[0][1]:.2f}초)")
        else:
            print("❌ GPT-5 계열 모델은 사용 불가능하거나 모두 실패")

if __name__ == "__main__":
    main()