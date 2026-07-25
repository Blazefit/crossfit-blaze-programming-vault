<?php
/**
 * Blaze training-log API
 * -----------------------------------------------------------------------------
 * Tiny JSON store for the Blaze cycle app. Data lives OUTSIDE the web root in
 * ../../../private/blaze-log/ so it can never be fetched directly by URL.
 *
 * Auth model (trust-on-first-use, protected by a one-time setup token):
 *   1. A setup token is placed on the server out-of-band (via SSH).
 *   2. First device calls action=setup with that token + a chosen PIN.
 *      The PIN is stored as a password_hash; the token file is deleted.
 *   3. Every later call sends the PIN. Nothing is readable or writable without it.
 *
 * Actions: ping | setup | get | put
 * All requests are POST with a JSON body, except ping.
 */

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: no-referrer');
header('Cache-Control: no-store');

const MAX_BODY      = 2097152;  // 2 MB
const LOCK_AFTER    = 8;        // failed PIN attempts before lockout
const LOCK_SECONDS  = 900;      // 15 min lockout
const PIN_MIN       = 4;

$DATA = __DIR__ . '/../../../private/blaze-log';
$LOG  = $DATA . '/log.json';
$CFG  = $DATA . '/config.json';
$TOK  = $DATA . '/setup-token.txt';
$RATE = $DATA . '/rate.json';

function out(array $o, int $code = 200): void {
    http_response_code($code);
    echo json_encode($o, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}
function fail(string $msg, int $code = 400): void { out(['ok' => false, 'error' => $msg], $code); }

/** Read a JSON file, returning $default when missing or corrupt. */
function readJson(string $path, $default) {
    if (!is_file($path)) return $default;
    $raw = @file_get_contents($path);
    if ($raw === false || $raw === '') return $default;
    $val = json_decode($raw, true);
    return is_array($val) ? $val : $default;
}

/** Write JSON atomically so a crash mid-write can't corrupt the log. */
function writeJson(string $path, array $val): bool {
    $tmp = $path . '.tmp' . getmypid();
    $enc = json_encode($val, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    if ($enc === false) return false;
    if (@file_put_contents($tmp, $enc, LOCK_EX) === false) return false;
    if (!@rename($tmp, $path)) { @unlink($tmp); return false; }
    @chmod($path, 0600);
    return true;
}

// ---------------------------------------------------------------- rate limit
function rateState(string $f): array {
    $r = readJson($f, ['fails' => 0, 'until' => 0]);
    return ['fails' => (int)($r['fails'] ?? 0), 'until' => (int)($r['until'] ?? 0)];
}
function rateFail(string $f): void {
    $r = rateState($f);
    $r['fails']++;
    if ($r['fails'] >= LOCK_AFTER) { $r['until'] = time() + LOCK_SECONDS; $r['fails'] = 0; }
    writeJson($f, $r);
}
function rateClear(string $f): void { writeJson($f, ['fails' => 0, 'until' => 0]); }

// ------------------------------------------------------------------- request
if (!is_dir($DATA)) { @mkdir($DATA, 0700, true); }
if (!is_dir($DATA)) fail('storage unavailable', 500);

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

// ping: liveness + whether a PIN has been configured. Reveals nothing else.
if ($method === 'GET') {
    out(['ok' => true, 'action' => 'ping', 'configured' => is_file($CFG), 'v' => 1]);
}
if ($method !== 'POST') fail('method not allowed', 405);

$raw = file_get_contents('php://input', false, null, 0, MAX_BODY + 1);
if ($raw === false) fail('no body');
if (strlen($raw) > MAX_BODY) fail('body too large', 413);

$req = json_decode($raw, true);
if (!is_array($req)) fail('bad json');

$action = (string)($req['action'] ?? '');
$pin    = (string)($req['pin'] ?? '');

$rs = rateState($RATE);
if ($rs['until'] > time()) {
    fail('locked, retry in ' . ($rs['until'] - time()) . 's', 429);
}

// ------------------------------------------------------------------- setup
if ($action === 'setup') {
    if (is_file($CFG)) fail('already configured', 409);
    if (!is_file($TOK)) fail('no setup token on server', 403);

    $token    = trim((string)@file_get_contents($TOK));
    $supplied = trim((string)($req['token'] ?? ''));
    if ($token === '' || !hash_equals($token, $supplied)) { rateFail($RATE); fail('bad setup token', 403); }
    if (strlen($pin) < PIN_MIN) fail('pin too short (min ' . PIN_MIN . ')');

    if (!writeJson($CFG, ['pin' => password_hash($pin, PASSWORD_DEFAULT), 'created' => time()])) {
        fail('could not save config', 500);
    }
    @chmod($CFG, 0600);
    @unlink($TOK);                       // one-time use
    if (!is_file($LOG)) writeJson($LOG, ['v' => 1, 'updated' => time(), 'cycles' => (object)[], 'tm' => (object)[], 'sessions' => (object)[]]);
    rateClear($RATE);
    out(['ok' => true, 'action' => 'setup']);
}

// --------------------------------------------------------------- authenticate
$cfg = readJson($CFG, []);
if (!isset($cfg['pin'])) fail('not configured', 409);
if ($pin === '' || !password_verify($pin, (string)$cfg['pin'])) { rateFail($RATE); fail('bad pin', 401); }
rateClear($RATE);

$log = readJson($LOG, ['v' => 1, 'updated' => 0, 'cycles' => [], 'tm' => [], 'sessions' => []]);
foreach (['cycles', 'tm', 'sessions'] as $k) { if (!isset($log[$k]) || !is_array($log[$k])) $log[$k] = []; }

// -------------------------------------------------------------------- get
if ($action === 'get') {
    out(['ok' => true, 'action' => 'get', 'log' => $log]);
}

// -------------------------------------------------------------------- put
// Merge a patch. Per-key last-write-wins using client timestamps, so two
// devices editing different days/lifts never clobber each other.
if ($action === 'put') {
    $patch = $req['patch'] ?? null;
    if (!is_array($patch)) fail('bad patch');

    // sessions: keyed "YYYY-MM-DD|cycle|day"
    if (isset($patch['sessions']) && is_array($patch['sessions'])) {
        foreach ($patch['sessions'] as $key => $sess) {
            if (!is_string($key) || !is_array($sess)) continue;
            if (!preg_match('/^[0-9]{4}-[0-9]{2}-[0-9]{2}\|[a-z0-9\-]{1,40}\|[a-zA-Z0-9\-]{1,40}$/', $key)) continue;
            $incoming = (int)($sess['ts'] ?? 0);
            $existing = (int)($log['sessions'][$key]['ts'] ?? 0);
            if ($incoming >= $existing) $log['sessions'][$key] = $sess;
        }
    }
    // cycles: { cycleId: {week, ts} }
    if (isset($patch['cycles']) && is_array($patch['cycles'])) {
        foreach ($patch['cycles'] as $cid => $c) {
            if (!is_string($cid) || !preg_match('/^[a-z0-9\-]{1,40}$/', $cid) || !is_array($c)) continue;
            $incoming = (int)($c['ts'] ?? 0);
            $existing = (int)($log['cycles'][$cid]['ts'] ?? 0);
            if ($incoming >= $existing) $log['cycles'][$cid] = $c;
        }
    }
    // tm: { liftId: {v, ts} }
    if (isset($patch['tm']) && is_array($patch['tm'])) {
        foreach ($patch['tm'] as $lift => $t) {
            if (!is_string($lift) || !preg_match('/^[a-z0-9\-]{1,40}$/', $lift) || !is_array($t)) continue;
            $incoming = (int)($t['ts'] ?? 0);
            $existing = (int)($log['tm'][$lift]['ts'] ?? 0);
            if ($incoming >= $existing) $log['tm'][$lift] = $t;
        }
    }

    $log['v'] = 1;
    $log['updated'] = time();
    if (!writeJson($LOG, $log)) fail('could not save', 500);
    out(['ok' => true, 'action' => 'put', 'log' => $log]);
}

fail('unknown action');
