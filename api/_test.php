<?php
// Jednorazowy test środowiska OVH (do usunięcia). Nie zapisuje żadnych danych poza plikiem testowym.
header('Content-Type: text/plain; charset=utf-8');
$doc = rtrim($_SERVER['DOCUMENT_ROOT'] ?? '', '/');
echo "php ", PHP_VERSION, "\n";
echo "pdo_sqlite ", extension_loaded('pdo_sqlite') ? 'tak' : 'NIE', " | sqlite3 ", extension_loaded('sqlite3') ? 'tak' : 'nie', "\n";
echo "dir ", __DIR__, "\ndocroot ", $doc, "\n";
foreach ([dirname(__DIR__, 2), dirname(__DIR__)] as $i => $base) {
  $d = $base . '/' . ($i ? '_priv_test' : 'tvdb_test');
  $ok = @is_dir($d) || @mkdir($d, 0700, true);
  echo "\n[$d] mkdir ", $ok ? 'ok' : 'NIE';
  if ($ok) {
    try {
      $db = new PDO('sqlite:' . $d . '/t.sqlite'); $db->exec('CREATE TABLE IF NOT EXISTS t(x)'); $db->exec('INSERT INTO t VALUES (1)');
      echo " | sqlite zapis ok, wierszy: ", $db->query('SELECT COUNT(*) FROM t')->fetchColumn(), " | sqlite ", $db->query('select sqlite_version()')->fetchColumn();
    } catch (Throwable $e) { echo " | BŁĄD ", $e->getMessage(); }
  }
}
echo "\n";
