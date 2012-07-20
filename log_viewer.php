<?php

$job_id = $_REQUEST['job_id'];
$host = $_SERVER["HTTP_HOST"];

preg_match('/^([-_a-zA-Z0-9]*)\.app/', $host, $matches);
$folder = $matches[1];

$filename = "logs/" . $folder . "/" . $job_id . "_log.json";
$handle = fopen($filename, "r");
$contents = fread($handle, filesize($filename));
fclose($handle);

if($contents) {
    print $_REQUEST['callback'] . "(" . $contents . ")";
} else {
    print $_REQUEST['callback'] . "(" . json_encode(array('status'=>false)) . ")";
}

