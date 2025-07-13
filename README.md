
# FROG-System: Among Aircraft AI System

> **FROG-System**은 드론 및 항공기 경로 탐색을 위한 인공지능 기반 시스템입니다. 사용자는 출발지와 목적지를 입력하면, 비행 가능한 구역을 기반으로 최적의 경로를 시각화해줍니다.

---

## 📌 주요 기능

- ✅ **비행 가능/불가 지역 시각화**  
  - Folium 기반 지도 시각화
  - 금지구역, 비행제한구역 등 실제 공역 정보 반영
- 🧭 **1x1m 단위 그리드 생성**
  - 드론 수준의 정밀도 확보
- ✈️ **A\* 알고리즘 기반 경로 탐색**
  - 비행 가능 구역 내 최적 경로 계산
- 📍 **출발지/도착지 주소 입력 기능**
  - 지명 또는 건물명을 주소로 입력하면 자동 좌표 변환 (Geocoding)
- 💻 **웹 인터페이스**
  - 사용자 친화적인 HTML 인터페이스 제공

---

## 🗂️ 프로젝트 구조

```bash
FROG-System-Among-Aircraft-AI-System/
├── content/
│   └── data/             # 공역 데이터 csv (직접 크롤링)
├── web/
│   ├── main.html          
│   └── map.html           # 지도
├── mapping.py             # 메인 지도 시각화 스크립트
└── README.md
```

---

## 📬 문의

프로젝트 관련 문의는 [Issues](https://github.com/ksh6940/FROG-System-Among-Aircraft-AI-System-/issues)를 통해 남겨주세요.
```
