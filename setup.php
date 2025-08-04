<?php
require_once 'db.php';
$admin_username = 'admin';
$admin_password = hash('sha256', 'admin1234');
$admin_token = bin2hex(random_bytes(16));

$stmt = $db->prepare("SELECT * FROM users WHERE username = ?");
$stmt->execute([$admin_username]);

if (!$stmt->fetch()) {
    $stmt = $db->prepare("INSERT INTO users (username, password, token) VALUES (?, ?, ?)");
    $stmt->execute([$admin_username, $admin_password, $admin_token]);
    echo "✅ admin 계정 생성 완료";
} else {
    echo "⚠️ 이미 admin 계정이 있음";
}
?>
