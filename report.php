<?php
if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST['url'])) {
    $url = trim($_POST['url']);

    if (filter_var($url, FILTER_VALIDATE_URL)) {
        file_put_contents('report_log.txt', $url . PHP_EOL, FILE_APPEND);
        $msg = "Thank you! Admin will check it soon.";
    } else {
        $msg = "Invalid URL.";
    }
}
?>

<h2>Concert Feedback</h2>
<p>Report any issues you encountered during the ticketing process.</p>

<?php if (!empty($msg)) echo "<p>" . htmlspecialchars($msg) . "</p>"; ?>

<form method="POST">
  <input type="text" name="url" placeholder="Problematic page URL" required><br><br>
  <button type="submit">Submit</button>
</form>

<small>* 운영진이 수시로 확인합니다. 여러분의 의견은 더 나은 서비스를 만드는 데 도움이 됩니다.</small>
