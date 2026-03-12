# How to run (Prototype)

이 문서는 **ROS 2 Jazzy** 환경에서 `ros2sc_web`을 실행하고, 브라우저에서 **토픽/서비스/노드/타입/패키지 목록**을 확인하는 “프로토타입 실행 방법”을 정리합니다.

## 구성요소
- **`ros2sc_web`**: ROS 2 그래프를 읽어서 HTTP API + 웹 UI로 제공하는 ROS 패키지

## 0) 사전 준비
- ROS 2 환경이 활성화되어 있어야 합니다.
  - 예: `source /opt/ros/jazzy/setup.bash`
- 기본은 **로컬(127.0.0.1)에서만** 접속하도록 구성합니다.

## 1) 이 저장소 빌드(colcon)
저장소 루트에서 빌드합니다.

```bash
cd /home/rokmc/ros2_shortcut
colcon build --symlink-install
source install/setup.bash
```

## 2) 웹 인스펙터 실행
### 로컬 전용(기본)
```bash
ros2 launch ros2sc_web web_inspector.launch.py
```

### 로컬 + LAN 허용(원할 때만)
```bash
ros2 launch ros2sc_web web_inspector.launch.py address:=0.0.0.0
```

### 포트 변경
```bash
ros2 launch ros2sc_web web_inspector.launch.py port:=8081
```

## 3) 브라우저에서 접속
- 같은 PC에서 접속: `http://127.0.0.1:8081` (기본 포트)
- 같은 LAN의 다른 PC에서 접속(옵션): `http://<robot_pc_ip>:8081`

포트를 바꿨다면 그 포트로 접속하세요(예: `http://127.0.0.1:9090`).

## ROS_DOMAIN_ID 선택
- 페이지 상단의 **`ROS_DOMAIN_ID` 입력칸**에 값을 넣으면, 해당 도메인 기준으로 토픽/서비스/노드를 조회합니다.
- 예: `0`, `7` 등

## 4) 확인 가능한 정보
- Topics: 이름 + 타입 목록
- Services: 이름 + 타입 목록
- Actions: 이름 + 타입 목록
- Nodes: 이름/네임스페이스
- Packages: ament index 기준 설치된 패키지 목록
- Interface: 타입을 클릭해서 `ros2 interface show` 결과 확인

## 5) 자주 막히는 포인트(체크리스트)
- **LAN에서 접속이 안 됨**
  - LAN을 쓰려면 브리지가 `0.0.0.0`에 바인드되어 있는지 확인
  - 방화벽(UFW 등)에서 포트가 열려 있는지 확인
  - `docs/networking.md` 참고
- **ROS_DOMAIN_ID 관련**
  - `ROS_DOMAIN_ID`는 “웹 제공”이 아니라 ROS 2 discovery/분리용입니다.
  - 웹 인스펙터는 HTTP이지만, ROS 그래프를 읽는 쪽은 discovery가 필요합니다.

