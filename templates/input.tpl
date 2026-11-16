<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>T9ADRIVE</title>
<style>
body {
  background-color: #ffcc00;
  text-align: center;
  font-family: sans-serif;
  padding: 10px;
}
input[type=text] {
  background-color: #ffffff;
  border: 2px solid #333333;
  padding: 4px;
  font-size: 16px;
  width: 100%;
  margin-bottom: 8px;
  box-sizing: border-box;
}
</style>
</head>
<body>
<p>ORIGIN / DESTINATION</p>
<form action="/query" method="POST">
  <input type="text" name="origin" placeholder="origin">
  <input type="text" name="dest" placeholder="destination">
  <br>
  <input type="submit" value="Submit">
</form>
<p><a href="/admin">admin</a></p>
</body>
</html>
