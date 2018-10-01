<?php
echo file_get_contents('php://input');
$headers = apache_request_headers();
print_r($headers);
?>