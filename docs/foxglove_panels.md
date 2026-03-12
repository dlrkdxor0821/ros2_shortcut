# Foxglove Panels (Image / 3D / Plot)

이 문서는 `foxglove_bridge`로 연결한 뒤 Foxglove Studio에서 자주 쓰는 패널을 빠르게 고르는 기준을 정리합니다.

## Raw Messages
- 토픽의 메시지 구조를 그대로 확인할 때 유용합니다.
- “토픽이 보이는데 패널이 안 뜬다” 같은 상황에서 디버깅 1순위입니다.

## Image
- 카메라 이미지 토픽을 볼 때 사용합니다.
- 흔한 토픽 예시
  - `/camera/image`
  - `/camera/color/image_raw`
  - `/image_raw`

## 3D
TF를 바탕으로 프레임/센서/포인트클라우드를 한 화면에서 볼 때 사용합니다.

- TF 토픽
  - `/tf`
  - `/tf_static`
- PointCloud2 토픽 예시
  - `/points`
  - `/velodyne_points`
- LaserScan 토픽 예시
  - `/scan`

### RobotModel(선택)
- URDF가 제공되면 로봇 모델을 3D 뷰에 올릴 수 있습니다.
- 흔한 URDF 소스 예시
  - `/robot_description`

## Plot
- 수치 데이터를 시간에 따라 그래프로 보고 싶을 때 사용합니다.
- 예: 제어 입력, 센서 스칼라 값, 상태 값 등

