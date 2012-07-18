<?php

// This will save a new job ID
$job_id = $_REQUEST['job_id'];
$host = $_SERVER["HTTP_HOST"];

preg_match('/^([-_a-zA-Z0-9]*)\.app/', $host, $matches);
$folder = $matches[1];

$cmd = "python installer.py " . $folder . " " . $job_id;
$pidfile = "test.pid";
$out = "/dev/null";
exec(sprintf("%s > %s 2>&1 & echo $! >> %s", $cmd, $out, $pidfile));

