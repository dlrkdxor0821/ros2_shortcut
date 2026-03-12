# Networking (Local / LAN / Remote)

`foxglove_bridge`를 실행한 ROS 2 머신(`robot_pc`)에 Foxglove Studio(`viewer_pc`)가 접속하려면, “ROS 2 네트워크”와는 별개로 **WebSocket 네트워크 경로**가 열려 있어야 합니다.

## 용어
- **robot_pc**: ROS 2 노드와 `foxglove_bridge`가 실행되는 PC
- **viewer_pc**: Foxglove Studio를 실행/접속하는 PC

## 체크리스트: 같은 PC(로컬)
- `viewer_pc == robot_pc`
- Foxglove에서 `ws://localhost:<port>`로 접속
- 방화벽 이슈가 거의 없음

## 체크리스트: 같은 LAN의 다른 PC
- `viewer_pc != robot_pc`
- Foxglove에서 `ws://<robot_pc_ip>:<port>`로 접속
- `robot_pc` 방화벽(UFW 등)에서 `<port>` 인바운드 허용 필요
- 공유기/스위치/서브넷이 달라도 라우팅이 되어야 함

## 체크리스트: 인터넷 넘어 원격(주의)
원격 공개는 “가능”하지만 기본값으로 추천하지 않습니다.

- 포트 포워딩/공인 IP 노출은 **공격 표면**이 됩니다.
- 최소한 아래 중 하나를 고려하세요.
  - VPN(예: WireGuard/Tailscale)
  - SSH 터널
  - 리버스 프록시 + 인증(환경에 따라)

## ROS_DOMAIN_ID와의 관계
- `ROS_DOMAIN_ID`는 **ROS 2 discovery/통신 범위**를 제어합니다.
- Foxglove 접속(WebSocket)은 ROS 2 discovery와 별개로, **브리지 포트에 대한 네트워크 접속**이 핵심입니다.

