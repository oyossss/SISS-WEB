<?php
session_start();
$username = $_SESSION['username'] ?? null;
?>

<!DOCTYPE html>
<html>
<head>
    <title>Concert Ticketing</title>
</head>
<body>
    <h1>Welcome to Concert Ticketing Portal</h1>

    <?php if ($username): ?>
        <p>Welcome back, <?= htmlspecialchars($username) ?>!</p>
        <ul>
            <li><a href="mypage.php">My Tickets</a></li>
            <li><a href="logout.php">Logout</a></li>
            <li><a href ="report.php">Report a Problem</li>
        
        </ul>
    <?php else: ?>
        <p>You are not logged in.</p>
        <ul>
            <li><a href="login.php">Login</a></li>
            <li><a href="register.php">Register</a></li>
            
        </ul>
    <?php endif; ?>

</body>
</html>
