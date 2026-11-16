<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>T9ADRIVE — result</title>
</head>
<body>
<p>{{origin}} &gt; {{dest}}</p>
%for step in steps:
<p>{{step['instruction']}} ({{step['distance']}})</p>
%end
<p>Duration: {{duration}} ({{distance}})</p>
<p><a href="/">[new query]</a></p>
</body>
</html>
