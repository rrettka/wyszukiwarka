<?php
/*
 * Historia cen – SQLite w jednym pliku, bez użytkownika i hasła.
 *
 * GET api/history.php            → {"src":"db","pl":{"id":[["RRRR-MM-DD",cena],…]},"updated":"…"}
 * GET api/history.php?id=l77c5   → {"src":"db","id":"l77c5","pl":[…],"intl":{"DE":[…],…}}
 *
 * Nikt z zewnątrz nie zapisuje danych. Baza dopisuje się sama: przy zapytaniu sprawdza,
 * czy prices.json / prices_intl.json się zmieniły (data modyfikacji pliku), i wtedy zapisuje
 * najniższą cenę dnia. Przy pierwszym utworzeniu bazy importuje history.json (historia z gita).
 * Plik bazy leży poza katalogiem strony; gdy się nie da – w api/_db z blokadą dostępu.
 */
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-cache');
date_default_timezone_set('Europe/Warsaw');

$ROOT = dirname(__DIR__);

function dbPath(string $root): string {
  foreach ([dirname($root) . '/tvdb_wyszukiwarka', __DIR__ . '/_db'] as $dir) {
    if (!is_dir($dir) && !@mkdir($dir, 0700, true)) continue;
    if (!is_writable($dir)) continue;
    if (strpos($dir, __DIR__) === 0) {
      @file_put_contents($dir . '/.htaccess', "Require all denied\nDeny from all\n");
    }
    return $dir . '/ceny.sqlite';
  }
  throw new RuntimeException('brak katalogu z prawem zapisu');
}

function fail(int $code, string $msg): void {
  http_response_code($code);
  echo json_encode(['error' => $msg], JSON_UNESCAPED_UNICODE);
  exit;
}

function upsert(PDO $db, string $id, string $mkt, string $day, $price): void {
  if (!is_numeric($price) || $price <= 0 || !preg_match('/^[a-z0-9_-]{1,40}$/i', $id)) return;
  static $st = null;
  $st ??= $db->prepare('INSERT INTO price_history(id,mkt,day,price) VALUES(?,?,?,?)
    ON CONFLICT(id,mkt,day) DO UPDATE SET price=MIN(price,excluded.price)');
  $st->execute([$id, $mkt, $day, (float)$price]);
}

function meta(PDO $db, string $k, ?string $v = null): ?string {
  if ($v === null) {
    $s = $db->prepare('SELECT v FROM meta WHERE k=?'); $s->execute([$k]);
    $r = $s->fetchColumn(); return $r === false ? null : (string)$r;
  }
  $db->prepare('INSERT OR REPLACE INTO meta(k,v) VALUES(?,?)')->execute([$k, $v]);
  return $v;
}

function readJson(string $f): ?array {
  if (!is_file($f)) return null;
  $j = json_decode((string)file_get_contents($f), true);
  return is_array($j) ? $j : null;
}

try {
  $db = new PDO('sqlite:' . dbPath($ROOT), null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
  $db->exec('PRAGMA busy_timeout=5000; PRAGMA journal_mode=WAL;');
  $db->exec('CREATE TABLE IF NOT EXISTS price_history(
      id TEXT NOT NULL, mkt TEXT NOT NULL, day TEXT NOT NULL, price REAL NOT NULL,
      PRIMARY KEY(id,mkt,day)) WITHOUT ROWID;
    CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)');

  // Dopisanie nowych cen – tylko gdy któryś plik źródłowy się zmienił.
  $srcP = $ROOT . '/prices.json'; $srcI = $ROOT . '/prices_intl.json'; $srcH = $ROOT . '/history.json';
  $sig = implode(',', array_map(fn($f) => is_file($f) ? (string)filemtime($f) : '-', [$srcP, $srcI, $srcH]));
  if (meta($db, 'sig') !== $sig) {
    $db->exec('BEGIN IMMEDIATE');
    if (meta($db, 'sig') !== $sig) {          // ktoś mógł to zrobić w międzyczasie
      if (($h = readJson($srcH))) {             // historia z gita (bezpieczne do ponawiania)
        foreach ($h['pl'] ?? [] as $id => $pts) foreach ($pts as [$d, $p]) upsert($db, (string)$id, 'PL', (string)$d, $p);
        foreach ($h['intl'] ?? [] as $id => $mk) foreach ($mk as $m => $pts) foreach ($pts as [$d, $p]) upsert($db, (string)$id, (string)$m, (string)$d, $p);
      }
      $today = date('Y-m-d');
      if (($j = readJson($srcP))) {
        foreach ($j['prices'] ?? [] as $id => $v) upsert($db, (string)$id, 'PL', $today, is_array($v) ? ($v[0] ?? null) : $v);
        foreach ($j['add'] ?? [] as $a) if (is_array($a) && isset($a['id'])) upsert($db, (string)$a['id'], 'PL', $today, $a['p'] ?? null);
      }
      if (($j = readJson($srcI))) {
        foreach ($j['offers'] ?? [] as $id => $arr) foreach ((array)$arr as $o) if (isset($o['m'])) upsert($db, (string)$id, (string)$o['m'], $today, $o['price'] ?? null);
      }
      meta($db, 'sig', $sig); meta($db, 'updated', date('c'));
    }
    $db->exec('COMMIT');
  }

  $id = $_GET['id'] ?? null;
  if ($id !== null) {
    if (!preg_match('/^[a-z0-9_-]{1,40}$/i', $id)) fail(400, 'zły identyfikator');
    $s = $db->prepare('SELECT mkt,day,price FROM price_history WHERE id=? ORDER BY day');
    $s->execute([$id]);
    $pl = []; $intl = [];
    foreach ($s as $r) { $pt = [$r['day'], +$r['price']]; if ($r['mkt'] === 'PL') $pl[] = $pt; else $intl[$r['mkt']][] = $pt; }
    echo json_encode(['src' => 'db', 'id' => $id, 'pl' => $pl, 'intl' => (object)$intl, 'updated' => meta($db, 'updated')], JSON_UNESCAPED_UNICODE);
    exit;
  }
  $pl = [];
  foreach ($db->query("SELECT id,day,price FROM price_history WHERE mkt='PL' ORDER BY id,day") as $r) $pl[$r['id']][] = [$r['day'], +$r['price']];
  echo json_encode(['src' => 'db', 'pl' => (object)$pl, 'updated' => meta($db, 'updated')], JSON_UNESCAPED_UNICODE);
} catch (Throwable $e) {
  if (isset($db) && $db->inTransaction()) $db->rollBack();
  fail(500, 'historia cen chwilowo niedostępna');
}
