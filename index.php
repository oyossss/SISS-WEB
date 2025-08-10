<?php
session_start();
$conn = new mysqli('127.0.0.1', 'root', '', 'summer_resort');
if ($conn->connect_error) {
    die("DB 연결 실패: " . $conn->connect_error);
}

$rows = 5;
$cols = 8;

// 예약 좌석 로드
$reservedSeats = [];
$res = $conn->query("SELECT seat_code FROM tickets_test");
while ($row = $res->fetch_assoc()) {
    $reservedSeats[] = $row['seat_code'];
}
$res->free();

// Reserve 처리
$msg = '';
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    if (empty($_SESSION['username'])) {
        header("Location: login.php");
        exit;
    }

    $selectedSeat = $_POST['seat_code'] ?? null;
    $username     = $_SESSION['username'];                 
    $bg           = $_POST['ticketColor'] ?? 'pink';      
    if (!$selectedSeat) {
        $msg = "<p style='color:red;'>좌석을 선택하세요.</p>";
    } elseif (in_array($selectedSeat, $reservedSeats, true)) {
        $msg = "<p style='color:red;'>이미 예약된 좌석입니다.</p>";
    } else {
        $stmt = $conn->prepare("INSERT INTO tickets_test (seat_code, username, background) VALUES (?, ?, ?)");
        $stmt->bind_param("sss", $selectedSeat, $username, $bg);
        if ($stmt->execute()) {
            $msg = "<p style='color:green;'>예약이 완료되었습니다!</p>";
            // 방금 좌석을 예약 목록에 반영
            $reservedSeats[] = $selectedSeat;
        } else {
            $msg = "<p style='color:red;'>예약 실패: " . htmlspecialchars($stmt->error) . "</p>";
        }
        $stmt->close();
    }
}
?>
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>좌석 예매</title>
  <link rel="stylesheet" href="index_style.css">
  <style>


  </style>

</head>
<body>

<?php include 'navbar.php'; ?>

<form method="POST">
  <h3>Select your Seat and Buy tickets!!!</h3>

  <?= $msg ?>

  <h4>Choose Ticket Color</h4>
  <select name="ticketColor" id="ticketColor" class="form-select">
    <option value="pink">Pink</option>
    <option value = "black">Black</option>
    <option value="blue">Blue</option>
    <option value="green">Green</option>
    <option value="yellow">Yellow</option>
    <option value = "red">Red</option>
    <option value = "orange">Orange</option>
  </select>

  <br/>
  <div class="grid">
    <?php for ($i = 0; $i < $rows * $cols; $i++): ?>
      <?php
        $seatCode   = "A" . ($i + 1);
        $isReserved = in_array($seatCode, $reservedSeats, true);
        $seatClass  = $isReserved ? 'reserved' : '';
      ?>
      <label class="seat <?= $seatClass ?>">
        <input type="radio" name="seat_code" value="<?= $seatCode ?>" <?= $isReserved ? 'disabled' : '' ?>>
        <?= $i + 1 ?>
      </label>
    <?php endfor; ?>
  </div>

  <br><button type="submit">Reserve</button>
</form>

</body>
</html>

