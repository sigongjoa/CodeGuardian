#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
테스트 에러 발생 모듈
에러 추적 기능 테스트를 위한 모듈
"""

def main():
    """메인 함수"""
    print("테스트 시작")
    try:
        process_data([1, 2, 3, 'four', 5])
    except Exception as e:
        print(f"에러 발생: {str(e)}")
    
    try:
        calculate_average([])
    except Exception as e:
        print(f"에러 발생: {str(e)}")
    
    print("테스트 완료")

def process_data(data_list):
    """데이터 처리"""
    result = []
    for item in data_list:
        # 의도적 에러 발생 (문자열에는 제곱 연산 불가)
        value = item ** 2
        result.append(value)
    
    analyze_results(result)
    return result

def analyze_results(data):
    """결과 분석"""
    if not data:
        raise ValueError("데이터가 비어있습니다")
    
    total = sum(data)
    average = total / len(data)
    return {
        'total': total,
        'average': average,
        'min': min(data),
        'max': max(data)
    }

def calculate_average(numbers):
    """평균 계산"""
    # 의도적 에러 발생 (빈 리스트인 경우 ZeroDivisionError)
    return sum(numbers) / len(numbers)

def generate_report(data, filename):
    """리포트 생성"""
    try:
        with open(filename, 'w') as f:
            f.write(f"Report\n")
            f.write(f"------\n")
            f.write(f"Total: {data['total']}\n")
            f.write(f"Average: {data['average']}\n")
            f.write(f"Minimum: {data['min']}\n")
            f.write(f"Maximum: {data['max']}\n")
        return True
    except Exception as e:
        print(f"리포트 생성 실패: {str(e)}")
        return False

if __name__ == "__main__":
    main()
