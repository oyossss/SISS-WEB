<?php
session_start();
session_unset();     // 세션 변수 초기화
session_destroy();   // 세션 자체 삭제

header("Location: login.php"); // 로그인 페이지로 리다이렉트
exit();
?>
