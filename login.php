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
            header("Location: index.php");
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
    <title>로그인</title>
</head>
<body>
    <h1>로그인</h1><br/>

    <?php if (!empty($error)): ?>
        <p style="color: red;"><?= htmlspecialchars($error) ?></p>
    <?php endif; ?>

    <form method="POST">
        <div class="form-group">
            <label for="InputId">이름</label>
            <input type="text" class="form-control" id="InputId" name="username" placeholder="사용자 이름 입력" required>
        </div>
        <div class="form-group">
            <label for="InputPassword">비밀번호</label>
            <input type="password" class="form-control" id="InputPassword" name="password" placeholder="비밀번호 입력" required>
        </div>
            <button type="submit" class="btn btn-primary" id="submit">로그인</button>
    </form>
    
    <p class="row">
        계정이 없으신가요? <a href="register.php">회원가입하러 가기</a>
    </p>
</body>
</html>
