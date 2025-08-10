<?php session_start(); ?>
<!-- navbar.php -->
<nav class="navbar navbar-dark bg-dark">
  <div class="container">
    <a class="navbar-brand" href="index.php">Concert Ticket</a>
    <ul class="navbar-nav flex-row">
      <li class="nav-item me-3">
        <a class="nav-link" href="index.php">홈</a>
      </li>
      <li class="nav-item me-3">
        <a class="nav-link" href="report.php">부정티켓신고</a>
      </li>
      <?php if (isset($_SESSION['username'])): ?>
        <li class="nav-item me-3">
          <a class="nav-link" href="mypage.php"><?= htmlspecialchars($_SESSION['username']) ?>님</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="logout.php">로그아웃</a>
        </li>
      <?php else: ?>
        <li class="nav-item me-3">
          <a class="nav-link" href="login.php">로그인</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="register.php">회원가입</a>
        </li>
      <?php endif; ?>
    </ul>
  </div>
</nav>
