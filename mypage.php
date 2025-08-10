<?php
session_start();
require_once 'db.php';
include 'navbar.php';

if (!isset($_SESSION['uid'])){
    header('Location: login.php');
    exit;
}

$uid = $_SESSION['uid'];
$username = $_SESSION['username'] ?? 'guest';
$token = $_SESSION['token'] ?? 'no-token';

$seat = '';
$background = '';
try {
    $stmt = $db->prepare("
        SELECT seat_code, background
        FROM tickets_test
        WHERE username = :username
        ORDER BY id DESC
        LIMIT 1
    ");
    $stmt->execute([':username' => $username]);
    if ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $seat = $row['seat_code'] ?? '';
        $background = $row['background'] ?? '';
    }
} catch (Exception $e) {
    // 필요시 로그
}
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>My Page</title>

    <style>
      .ticket-box{
        width:200px;height:50px;border:1px solid #aaa;
        padding:10px;margin-top:7px;
        background: <?= $background ?>;
      }
    </style>
</head>
<body>
  <h1>Welcome, <?= htmlspecialchars($username, ENT_QUOTES, 'UTF-8') ?>!</h1>
  <meta name="token" content="<?= htmlspecialchars($token, ENT_QUOTES, 'UTF-8') ?>">

  <div>
    <label>Username</label><br>
    <input type="text" value="<?= htmlspecialchars($username, ENT_QUOTES, 'UTF-8') ?>" readonly>
  </div>
  <br>
  <div><label>auth-code : 847192</label></div>

  <h2>My Tickets</h2>

  <?php if ($seat !== '' || $background !== ''): ?>
    <div class="ticket-box">
      <p><strong>Seat:</strong> <?= htmlspecialchars($seat, ENT_QUOTES, 'UTF-8') ?></p>
    </div>
  <?php else: ?>
    <p>No tickets yet.</p>
  <?php endif; ?>

  <br><br>
</body>
</html>
