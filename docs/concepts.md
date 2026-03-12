# Concepts

이 문서는 “ROS 2 토픽/서비스를 웹에서 볼 수 있나?”라는 질문을 기준으로, 필요한 개념을 짧게 정리합니다.

## ROS graph
- ROS 2의 **노드/토픽/서비스/액션/파라미터**의 관계를 통칭합니다.
- 같은 네트워크(DDS discovery가 가능한 범위)에서 노드들이 서로를 발견하면 `ros2 topic list`, `ros2 service list` 같은 CLI로 탐색할 수 있습니다.

## ROS_DOMAIN_ID
- DDS 도메인을 분리하는 값으로, 같은 도메인끼리만 discovery/통신이 되도록 합니다.
- **웹 UI를 제공하는 기능은 아닙니다.**
- 다른 PC에서 ROS graph가 보이게 하려면 일반적으로 아래가 필요합니다.
  - 같은 `ROS_DOMAIN_ID`
  - 네트워크 경로가 열려 있음(같은 LAN, 라우팅/방화벽 등)

## “웹에서 보기”가 의미하는 것
보통 2가지가 있습니다.

1) **목록만 보기(텍스트 수준)**
- 다른 PC에서도 `ros2 topic list` 등으로 확인하는 형태
- 이 경우 브리지가 필요 없을 수 있습니다(네트워크/도메인 설정이 핵심)

2) **시각화(이미지/3D/플롯)**
- 브라우저/앱에서 이미지, 3D, 그래프 등으로 보는 형태
- 이 경우 대개 **브리지(예: `foxglove_bridge`)**가 필요합니다.

## Bridge와 WebSocket
- 브리지는 ROS 2 메시지를 외부 클라이언트가 읽을 수 있게 변환/중계합니다.
- Foxglove Studio는 보통 **WebSocket**으로 브리지에 연결합니다.

## 추천 스택
- **Foxglove Studio + `foxglove_bridge`**
  - 이미지/TF/PointCloud2 등 시각화 UX가 좋고, 대시보드 구성도 쉬운 편입니다.

