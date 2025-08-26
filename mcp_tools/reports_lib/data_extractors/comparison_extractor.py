"""
비교 분석을 위한 데이터 추출기

실제 ClickHouse 테이블 구조:
- line_in_out_individual: 방문자 상세 정보
- line: 라인 정보 (entrance=1이 입구)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

try:
    from mcp_tools.utils.database_manager import get_site_client
except ImportError:
    # 데이터베이스 연결이 불가능한 경우를 위한 fallback
    get_site_client = None

class ComparisonDataExtractor:
    """비교 분석에 필요한 데이터를 추출하는 클래스"""
    
    def __init__(self):
        self.database = "plusinsight"
        
    def extract_comparison_data(self, sites: List[str], end_date: str, days: int) -> Dict[str, Any]:
        """
        비교 분석에 필요한 모든 데이터를 추출하고 변환
        
        Args:
            sites: 매장 리스트
            end_date: 종료 날짜
            days: 분석 기간 (일)
            
        Returns:
            변환된 데이터 딕셔너리
        """
        result = {}
        
        for site in sites:
            try:
                # 원본 데이터 추출
                raw_data = self._extract_raw_comparison_data(site, end_date, days)
                
                if raw_data:
                    # 데이터 변환
                    daily_trends = self._transform_daily_trends_data(raw_data, end_date, days)
                    customer_composition = self._transform_customer_composition_data(raw_data, end_date, days)
                    time_age_heatmap = self._transform_time_age_heatmap_data(raw_data)
                    
                    result[site] = {
                        'daily_trends': daily_trends,
                        'customer_composition': customer_composition,
                        'time_age_heatmap': time_age_heatmap
                    }
                else:
                    # 데이터가 없는 경우 빈 데이터로 채움
                    result[site] = {
                        'daily_trends': self._create_empty_daily_trends(days),
                        'customer_composition': self._create_empty_customer_composition(),
                        'time_age_heatmap': self._create_empty_time_age_heatmap()
                    }
                    
            except Exception as e:
                logging.error(f"Failed to extract comparison data for {site}: {e}")
                # 에러 발생 시에도 빈 데이터로 채움
                result[site] = {
                    'daily_trends': self._create_empty_daily_trends(days),
                    'customer_composition': self._create_empty_customer_composition(),
                    'time_age_heatmap': self._create_empty_time_age_heatmap()
                }
        
        return result

    def _extract_raw_comparison_data(self, site: str, end_date: str, days: int) -> List[Tuple]:
        """원본 비교 데이터 추출"""
        if not get_site_client:
            logging.warning("Database connection not available, returning empty data")
            return []
            
        try:
            client = get_site_client(site)
            if not client:
                logging.warning(f"No database client available for site: {site}")
                return []
            
            # SQL 쿼리 구성
            sql = self._build_raw_comparison_sql(site, end_date, days)
            
            # 쿼리 실행 (clickhouse_connect 클라이언트는 query() 메서드 사용)
            result = client.query(sql)
            
            # 결과를 튜플 리스트로 변환
            raw_data = []
            for row in result.result_rows:
                raw_data.append(tuple(row))
            
            return raw_data
            
        except Exception as e:
            logging.error(f"Error extracting raw data for {site}: {e}")
            return []

    def _build_raw_comparison_sql(self, site: str, end_date: str, days: int) -> str:
        """원본 비교 데이터를 위한 SQL 쿼리 구성"""
        return f"""
        WITH
          toDate('{end_date}') AS req_end,
          if(req_end >= today(), addDays(today(), -1), req_end) AS target_end,
          {days} AS win,
          addDays(target_end, -(win-1)) AS curr_start,
          addDays(target_end, -(2*win-1)) AS prev_start,
          addDays(target_end, -win) AS prev_end,

          base AS (
            SELECT 
              lioi.date, 
              lioi.timestamp,
              lioi.person_seq,
              lioi.age,
              lioi.gender
            FROM line_in_out_individual AS lioi
            INNER JOIN line AS l ON l.id = lioi.triggered_line_id AND l.entrance = 1
            WHERE lioi.date BETWEEN prev_start AND target_end
              AND lioi.is_staff = 0
              AND upper(lioi.in_out) = 'IN'
          )
        SELECT 
          date,
          toHour(timestamp) as hour,
          age,
          gender,
          person_seq
        FROM base
        ORDER BY date, hour, age, gender
        """

    def _transform_daily_trends_data(self, raw_data: List[Tuple], end_date: str, days: int) -> Dict[str, Any]:
        """1번 카드용: 일별 방문 추이 데이터 변환"""
        # 날짜 범위 생성
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        dates = []
        weekdays = []
        
        for i in range(days):
            date_dt = end_dt - timedelta(days=days-1-i)
            dates.append(date_dt.strftime('%Y-%m-%d'))
            weekdays.append(date_dt.strftime('%a'))
        
        # 이전 주 데이터 (7일 전부터)
        prev_dates = []
        for i in range(days):
            date_dt = end_dt - timedelta(days=days-1-i+7)
            prev_dates.append(date_dt.strftime('%Y-%m-%d'))
        
        # 일별 집계
        daily_totals = {}
        for date in dates + prev_dates:
            daily_totals[date] = {'current': 0, 'previous': 0}
        
        # raw_data에서 일별 방문자 수 집계
        for row in raw_data:
            date, hour, age, gender, person_seq = row
            date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
            
            if date_str in daily_totals:
                if date_str in dates:
                    daily_totals[date_str]['current'] += 1
                elif date_str in prev_dates:
                    daily_totals[date_str]['previous'] += 1
        
        # 데이터 배열 생성
        curr_visitors = [daily_totals.get(date, {}).get('current', 0) for date in dates]
        prev_visitors = [daily_totals.get(date, {}).get('previous', 0) for date in prev_dates]
        
        # 성장률 계산
        growth_rates = []
        for curr, prev in zip(curr_visitors, prev_visitors):
            if prev > 0:
                growth = ((curr - prev) / prev) * 100
                growth_rates.append(round(growth, 1))
            else:
                growth_rates.append(0.0)
        
        return {
            'dates': dates,
            'weekdays': weekdays,
            'current': curr_visitors,
            'previous': prev_visitors,
            'growth': growth_rates
        }

    def _transform_customer_composition_data(self, raw_data: List[Tuple], end_date: str, days: int) -> Dict[str, Any]:
        """2번 카드용: 연령대별 성별 데이터 변환 (전주/금주 분리, 실제 방문객 수)"""
        # 날짜 범위 생성
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        curr_start = end_dt - timedelta(days=days-1)
        prev_start = curr_start - timedelta(days=days)
        prev_end = curr_start - timedelta(days=1)
        
        # 전주/금주 데이터 분리
        current_data = []
        previous_data = []
        
        for row in raw_data:
            date, hour, age, gender, person_seq = row
            date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
            date_dt = datetime.strptime(date_str, '%Y-%m-%d')
            
            if curr_start <= date_dt <= end_dt:
                current_data.append((date, hour, age, gender, person_seq))
            elif prev_start <= date_dt <= prev_end:
                previous_data.append((date, hour, age, gender, person_seq))
        
        # 전주 데이터 집계
        prev_age_gender_stats = self._aggregate_age_gender(previous_data)
        
        # 금주 데이터 집계
        curr_age_gender_stats = self._aggregate_age_gender(current_data)
        
        # 연령대 순서 정의 (60대+부터 10대까지)
        age_order = ['60대+', '50대', '40대', '30대', '20대', '10대']
        
        # 결과 배열 생성 (전주/금주 분리, 실제 방문객 수)
        prev_male_counts = []
        prev_female_counts = []
        curr_male_counts = []
        curr_female_counts = []
        
        for age_group in age_order:
            # 전주 데이터 - 실제 방문객 수
            if age_group in prev_age_gender_stats:
                male = prev_age_gender_stats[age_group]['male']
                female = prev_age_gender_stats[age_group]['female']
                prev_male_counts.append(male)
                prev_female_counts.append(female)
            else:
                prev_male_counts.append(0)
                prev_female_counts.append(0)
            
            # 금주 데이터 - 실제 방문객 수
            if age_group in curr_age_gender_stats:
                male = curr_age_gender_stats[age_group]['male']
                female = curr_age_gender_stats[age_group]['female']
                curr_male_counts.append(male)
                curr_female_counts.append(female)
            else:
                curr_male_counts.append(0)
                curr_female_counts.append(0)
        
        return {
            'age_groups': age_order,
            'prev_male_counts': prev_male_counts,
            'prev_female_counts': prev_female_counts,
            'curr_male_counts': curr_male_counts,
            'curr_female_counts': curr_female_counts
        }
    
    def _aggregate_age_gender(self, data: List[Tuple]) -> Dict[str, Dict[str, int]]:
        """연령대별 성별 집계 헬퍼 함수"""
        age_gender_stats = {}
        
        for row in data:
            date, hour, age, gender, person_seq = row
            
            # 연령대 그룹화
            if age < 20:
                age_group = '10대'
            elif age < 30:
                age_group = '20대'
            elif age < 40:
                age_group = '30대'
            elif age < 50:
                age_group = '40대'
            elif age < 60:
                age_group = '50대'
            else:
                age_group = '60대+'
            
            # 성별 라벨
            gender_label = 'female' if gender == 1 else 'male'
            
            if age_group not in age_gender_stats:
                age_gender_stats[age_group] = {'male': 0, 'female': 0}
            
            if gender_label == 'male':
                age_gender_stats[age_group]['male'] += 1
            else:
                age_gender_stats[age_group]['female'] += 1
        
        return age_gender_stats

    def _transform_time_age_heatmap_data(self, raw_data: List[Tuple]) -> Dict[str, Any]:
        """3번 카드용: 시간대별 연령대별 히트맵 데이터 변환"""
        # 시간대별 연령대별 집계
        heatmap_stats = {}
        
        for row in raw_data:
            date, hour, age, gender, person_seq = row
            
            # 연령대 그룹화
            if age < 20:
                age_group = '10대'
            elif age < 30:
                age_group = '20대'
            elif age < 40:
                age_group = '30대'
            elif age < 50:
                age_group = '40대'
            elif age < 60:
                age_group = '50대'
            else:
                age_group = '60대+'
            
            if hour not in heatmap_stats:
                heatmap_stats[hour] = {}
            
            if age_group not in heatmap_stats[hour]:
                heatmap_stats[hour][age_group] = 0
            
            heatmap_stats[hour][age_group] += 1
        
        # 연령대 순서 정의 (60대+부터 10대까지)
        age_order = ['60대+', '50대', '40대', '30대', '20대', '10대']
        
        # 히트맵 매트릭스 생성 (24시간 × 6연령대)
        heatmap_matrix = []
        for age_group in age_order:
            row = []
            for hour in range(24):
                if hour in heatmap_stats and age_group in heatmap_stats[hour]:
                    row.append(heatmap_stats[hour][age_group])
                else:
                    row.append(0)
            heatmap_matrix.append(row)
        
        return {
            'age_groups': age_order,
            'hours': list(range(24)),
            'data': heatmap_matrix
        }

    def _create_empty_daily_trends(self, days: int) -> Dict[str, List]:
        """빈 일별 추이 데이터 생성"""
        empty_list = [0] * days
        return {
            'dates': [None] * days,
            'weekdays': [None] * days,
            'current': empty_list,
            'previous': empty_list,
            'growth': empty_list
        }

    def _create_empty_customer_composition(self) -> Dict[str, Any]:
        """빈 고객 구성 데이터 생성"""
        return {
            'age_groups': ['10대', '20대', '30대', '40대', '50대', '60대+'],
            'male_shares': [0.0] * 6,
            'female_shares': [0.0] * 6
        }

    def _create_empty_time_age_heatmap(self) -> Dict[str, Any]:
        """빈 시간대별 연령대별 히트맵 데이터 생성"""
        return {
            'age_groups': ['60대+', '50대', '40대', '30대', '20대', '10대'],
            'hours': list(range(24)),
            'data': [[0 for _ in range(24)] for _ in range(6)]
        } 