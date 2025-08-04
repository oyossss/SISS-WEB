<?php
session_start();
require_once 'db.php'; 

$error = "";

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    if (isset($_POST['username'], $_POST['password'])) {
        $username = $_POST['username'];
        $password = $_POST['password'];
        $hashed_password = hash('sha256', $password);

        $stmt = $db->prepare("SELECT * FROM users WHERE username = :username AND password = :password");
        $stmt->bindParam(':username', $username, PDO::PARAM_STR);
        $stmt->bindParam(':password', $hashed_password, PDO::PARAM_STR);
        $stmt->execute();
        $user = $stmt->fetch(PDO::FETCH_ASSOC);  

        if ($user) {
            $_SESSION['username'] = $user['username'];
            $_SESSION['uid'] = $user['uid'];
            $_SESSION['token'] = $user['token'];
            header("Location: home.php");
            exit();
        } else {
            $error = "Incorrect username or password.";
        }
    } else {
        $error = "All fields are required.";
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Concert Ticketing - Login</title>
</head>
<body>
    <h1>Login to Concert Ticketing</h1><br/>

    <?php if (!empty($error)): ?>
        <p style="color: red;"><?= htmlspecialchars($error) ?></p>
    <?php endif; ?>

    <form method="POST">
        <div class="form-group">
            <label for="InputId">Username</label>
            <input type="text" class="form-control" id="InputId" name="username" placeholder="Enter your username" required>
        </div>
        <div class="form-group">
            <label for="InputPassword">Password</label>
            <input type="password" class="form-control" id="InputPassword" name="password" placeholder="Enter your password" required>
        </div>
        <button type="submit" class="btn btn-primary" id="submit">Log in and get your ticket</button>
    </form>

    <p class="row">
        Don't have an account? <a href="register.php">Register here</a>
    </p>
</body>
</html>
