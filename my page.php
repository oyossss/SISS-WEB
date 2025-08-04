<?php
session_start();

$color = $_GET['color'] ?? 'white';
$username = $_SESSION['username'] ?? 'guest';
$token = $_SESSION['token'] ?? 'no-token';
$uid = $_SESSION['uid'] ?? 0;
?>

<!DOCTYPE html>
<html>
<head>
    <title>My Page</title>
</head>
<body>
    <h1>Welcome, <?= htmlspecialchars($username) ?>!</h1>

    <div>
        <label>UID</label>
        <input type="text" value="<?= htmlspecialchars($uid) ?>" readonly>
    </div>
    <div>
        <label>Username</label>
        <input type="text" value="<?= htmlspecialchars($username) ?>" readonly>
    </div>
    <div>
        <label>API Token</label>
        <input type="text" value="<?= htmlspecialchars($token) ?>" readonly>
    </div>
    <p><a href= "logout.php">Logout</p>
</body>
</html>
