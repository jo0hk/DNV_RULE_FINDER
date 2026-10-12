/*
 * config.js — 화면이 요청을 보낼 서버 주소
 *
 *   서버(server.py)가 화면까지 함께 띄우는 경우(로컬 실행, Cloud Run 주소로 직접 접속)에는
 *   화면과 같은 주소로 요청을 보내므로 아무것도 적지 않아도 된다.
 *   GitHub Pages처럼 화면만 따로 올린 경우에는 아래 CLOUD_RUN_URL의 서버로 요청을 보낸다.
 */
const CLOUD_RUN_URL = "";   // 배포 후 Cloud Run 주소를 적는다. 예: "https://dnv-rule-finder-xxxxxxxx.a.run.app"

window.API_BASE = location.hostname.endsWith("github.io") ? CLOUD_RUN_URL : "";
