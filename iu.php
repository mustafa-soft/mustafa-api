<?php
/*
 * Mustafa Soft: imei-unlock relay (runs on the hosting that has the fixed IP).
 * Vercel -> https://api.mustafa-soft.com/iu.php -> imei-unlock.net
 * Read-only actions only. Edit PROXY_KEY below, nothing else.
 */
const PROXY_KEY = 'PUT_A_LONG_RANDOM_KEY_HERE';   // letters+digits, 24+ chars (same value goes in Vercel)
const IU_API    = 'https://imei-unlock.net/api/index.php'; // fixed on purpose
const ALLOWED   = ['imeiservicelist', 'accountinfo'];

header('Content-Type: application/json');

function out($code, $arr) { http_response_code($code); echo json_encode($arr); exit; }

if (PROXY_KEY === 'Kdcu1982@0900287738
    out(500, ['error' => 'proxy key not configured']);
}
$key = $_SERVER['HTTP_X_PROXY_KEY'] ?? '';
if (!hash_equals(PROXY_KEY, $key)) {
    out(401, ['error' => 'unauthorized']);
}
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    out(405, ['error' => 'method not allowed']);
}

$action   = $_POST['action'] ?? '';
$username = $_POST['username'] ?? '';
$apikey   = $_POST['apiaccesskey'] ?? '';
if (!in_array($action, ALLOWED, true)) {
    out(400, ['error' => 'action not allowed']);
}
if ($username === '' || $apikey === '') {
    out(400, ['error' => 'missing credentials']);
}

$ch = curl_init(IU_API);
curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => http_build_query([
        'username'      => $username,
        'apiaccesskey'  => $apikey,
        'action'        => $action,
        'requestformat' => 'JSON',
    ]),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_TIMEOUT        => 30,
]);
$body = curl_exec($ch);
$code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($body === false) {
    out(502, ['error' => 'upstream unreachable']);
}
http_response_code($code > 0 ? $code : 200);
echo $body;
